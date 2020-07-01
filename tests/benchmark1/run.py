#!/usr/bin/env python3

import os
import sys
import glob

sys.path.append('../../')
import software
import network
import tools


software.clear()
network.clear()

prefix = os.environ.get('PREFIX', '')

# 100MBit LAN cable
def get_tc_command(link, ifname):
	return f'tc qdisc replace dev "{ifname}" root tbf rate 100mbit burst 8192 latency 1ms'

def run(protocol, csvfile):
	for path in sorted(glob.glob(f'../../data/grid4/*.json')):
		state = tools.load_json(path)
		(node_count, link_count) = tools.json_count(state)

		print(f'run {protocol} on {path}')

		network.change(from_state='none', to_state=state, link_command=get_tc_command)
		tools.sleep(10)

		software_start_ms = tools.millis()
		software.start(protocol)
		software_startup_ms = tools.millis() - software_start_ms

		tools.sleep(30)

		paths = tools.get_random_paths(state, 2 * link_count)
		paths = tools.filter_paths(state, paths, min_hops=2, path_count=link_count)
		ping_result = tools.ping_paths(paths=paths, duration_ms=30000, verbosity='verbose')

		sysload_result = tools.sysload()

		software.clear()

		# add data to csv file
		extra = (['node_count', 'software_startup_ms'], [node_count, software_startup_ms])
		tools.csv_update(csvfile, '\t', extra, ping_result.getData(), sysload_result)

		network.clear()

		# abort benchmark when less then 40% of the pings arrive
		if (ping_result.received / ping_result.transmitted) < 0.4:
			break

for protocol in ['babel', 'batman-adv', 'yggdrasil']:
	with open(f"{prefix}benchmark1-{protocol}.csv", 'w+') as csvfile:
		run(protocol, csvfile)

tools.stop_all_terminals()
