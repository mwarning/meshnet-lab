#!/usr/bin/env python3

import os
import sys
import glob

sys.path.append('../../')
import software
import network
import tools


tools.root()
software.clear()
network.clear()

# need to open more files (especially for traffic measurement processes)
os.system('ulimit -Sn 4096')

prefix = os.environ.get('PREFIX', '')

# 100MBit LAN cable
def get_tc_command(link, ifname):
	return f'tc qdisc replace dev "{ifname}" root tbf rate 100mbit burst 8192 latency 1ms'

def run(protocol, files, csvfile):
	for path in sorted(glob.glob(files)):
		(node_count, link_count) = tools.json_count(path)

		# Limit node count to 300
		if node_count > 300:
			continue

		print(f'run {protocol} on {path}')

		network.change(from_state='none', to_state=path, link_command=get_tc_command)

		tools.sleep(10)

		wait_beg_ms = tools.millis()

		tmp_ms = tools.millis()
		traffic_beg = tools.traffic()
		traffic_ms = tools.millis() - tmp_ms

		tmp_ms = tools.millis()
		software.start(protocol)
		software_ms = tools.millis() - tmp_ms

		# Wait until wai seconds are over, else error
		tools.wait(wait_beg_ms, 300)

		ping_result = tools.ping(protocol=protocol, count=node_count, duration_ms=60000, verbosity='verbose')

		traffic_end = tools.traffic()

		sysload_result = tools.sysload()

		software.stop(protocol)
		network.clear()

		# add data to csv file
		extra = (['node_count', 'traffic_ms', 'software_ms'], [node_count, traffic_ms, software_ms])
		tools.csv_update(csvfile, '\t', extra, (traffic_end - traffic_beg).getData(), ping_result, sysload_result)

for name in ['line', 'grid4', 'rtree']:
	for protocol in ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'yggdrasil']:
		with open(f"{prefix}scalability1-{protocol}-{name}.csv", 'w+') as csvfile:
			run(protocol, f"../../data/{name}/*.json", csvfile)
