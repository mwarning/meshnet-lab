#!/usr/bin/env python3

import os
import sys
import glob

sys.path.append('../../')
from shared import Remote
import shared
import ping
import software
import network


remotes= [Remote()] #[Remote('192.168.44.133'), Remote('192.168.44.137')]

shared.check_access(remotes)
software.clear(remotes)
network.clear(remotes)

prefix = os.environ.get('PREFIX', '')

# 100MBit LAN cable
def get_tc_command(link, ifname):
	return f'tc qdisc replace dev "{ifname}" root tbf rate 100mbit burst 8192 latency 1ms'

def run(protocol, topology, csvfile):
	for path in sorted(glob.glob(f'../../data/{topology}/{topology}-*.json')):
		state = shared.load_json(path)
		(node_count, link_count) = shared.json_count(state)

		print(f'run {protocol} on {path}')

		network.apply(state=state, link_command=get_tc_command, remotes=remotes)
		shared.sleep(10)

		software_start_ms = shared.millis()
		software.start(protocol, remotes)
		software_startup_ms = shared.millis() - software_start_ms

		print(f'Wait 60s for the nodes start up and discover each other (needed for proactive protocols) and let the system load settle.')
		shared.sleep(60)

		paths = ping.get_random_paths_filtered(state, min_hops=2, path_count=link_count)
		ping_result = ping.ping(remotes=remotes, paths=paths, duration_ms=30000, verbosity='verbose')

		sysload_result = shared.sysload(remotes)

		software.clear(remotes)

		# add data to csv file
		extra = (['node_count', 'link_count', 'software_startup_ms'], [node_count, link_count, software_startup_ms])
		shared.csv_update(csvfile, '\t', extra, ping_result.getData(), sysload_result)

		network.clear(remotes)

		# system load too high (/2 because of hyperthreading)
		if sysload_result[1][0] > os.cpu_count() * 0.75:
			break

		# abort benchmark when less than 40% of the pings arrive
		if ping_result.send == 0 or (ping_result.received / ping_result.send) < 0.4:
			break

for protocol in ['babel', 'batman-adv', 'yggdrasil']:
	for topology in ['rtree', 'grid4', 'grid8']:
		with open(f"{prefix}benchmark2-{protocol}-{topology}.csv", 'w+') as csvfile:
			run(protocol, topology, csvfile)

shared.stop_all_terminals()