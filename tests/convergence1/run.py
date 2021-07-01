#!/usr/bin/env python3

import os
import sys
import glob

sys.path.append('../../')
import software
import network
from shared import Remote
import shared
import ping
import traffic

remotes= [Remote()]

software.clear(remotes)
network.clear(remotes)

prefix = os.environ.get('PREFIX', '')

# 100MBit LAN cable
def get_tc_command(link, ifname):
	return f'tc qdisc replace dev "{ifname}" root tbf rate 100mbit burst 8192 latency 1ms'

def run(protocol, files, csvfile):
	shared.seed_random(1234)

	for path in sorted(glob.glob(files)):
		state = shared.load_json(path)
		(node_count, link_count) = shared.json_count(state)

		print(f'run {protocol} on {path}')

		network.apply(state=state, link_command=get_tc_command, remotes=remotes)

		shared.sleep(10)

		for offset in range(0, 60, 2):
			tmp_ms = shared.millis()
			traffic_beg = traffic.traffic(remotes)
			traffic_ms = shared.millis() - tmp_ms

			tmp_ms = shared.millis()
			software.start(protocol)
			software_ms = shared.millis() - tmp_ms

			# Wait until wait seconds are over, else error
			shared.sleep(offset)

			paths = ping.get_random_paths(state, 2 * 200)
			paths = ping.filter_paths(state, paths, min_hops=2, path_count=200)
			ping_result = ping.ping(paths=paths, duration_ms=2000, verbosity='verbose', remotes=remotes)

			traffic_end = traffic.traffic(remotes)

			sysload_result = shared.sysload(remotes)

			software.clear(remotes)

			# add data to csv file
			extra = (['node_count', 'traffic_ms', 'software_ms', 'offset_ms'], [node_count, traffic_ms, software_ms, offset * 1000])
			shared.csv_update(csvfile, '\t', extra, (traffic_end - traffic_beg).getData(), ping_result.getData(), sysload_result)

		network.clear(remotes)

for file in ['../../data/line/line-0050.json', '../../data/grid4/grid4-0049.json', '../../data/rtree/rtree-0050.json']:
	for protocol in ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'ospf', 'yggdrasil']:
		name = file.split('/')[-2]
		with open(f"{prefix}convergence1-{protocol}-{name}.csv", 'w+') as csvfile:
			run(protocol, file, csvfile)

shared.stop_all_terminals()
