#!/usr/bin/env python3

import os
import sys
import glob

sys.path.append('../../')
import software
import network
from shared import Remote
import tools

# increase limit for all the parallel pings
os.system('ulimit -Sn 4096')

remotes= [Remote()]

tools.check_access(remotes)
software.copy(remotes, '../../protocols', '/var/')

software.clear(remotes)
network.clear(remotes)

prefix = os.environ.get('PREFIX', '')

# 100MBit LAN cable
def get_tc_command(link, ifname):
	return f'tc qdisc replace dev "{ifname}" root tbf rate 100mbit burst 8192 latency 1ms'

def run(protocol, files, csvfile):
	for path in sorted(glob.glob(files)):
		state = tools.load_json(path)
		(node_count, link_count) = tools.json_count(state)

		# Limit node count to 300
		if node_count > 300:
			continue

		print(f'run {protocol} on {path}')

		network.apply(state=state, link_command=get_tc_command, remotes=remotes)

		tools.sleep(10)

		software_start_ms = tools.millis()
		software.start(protocol, remotes)
		software_startup_ms = tools.millis() - software_start_ms

		tools.sleep(300)

		start_ms = tools.millis()
		traffic_beg = tools.traffic(remotes)

		paths = tools.get_random_paths(state, 2 * 200)
		paths = tools.filter_paths(state, paths, min_hops=2, path_count=200)
		ping_result = tools.ping_paths(remotes=remotes, paths=paths, duration_ms=300000, verbosity='verbose')

		traffic_ms = tools.millis() - start_ms
		traffic_end = tools.traffic(remotes)

		sysload_result = tools.sysload(remotes)

		software.clear(remotes)
		network.clear(remotes)

		# add data to csv file
		extra = (['node_count', 'traffic_ms', 'software_startup_ms'], [node_count, traffic_ms, software_startup_ms])
		tools.csv_update(csvfile, '\t', extra, (traffic_end - traffic_beg).getData(), ping_result.getData(), sysload_result)

for name in ['line', 'grid4', 'rtree']:
	for protocol in ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'ospf', 'yggdrasil']:
		with open(f"{prefix}scalability1-{protocol}-{name}.csv", 'w+') as csvfile:
			run(protocol, f"../../data/{name}/*.json", csvfile)

tools.stop_all_terminals()
