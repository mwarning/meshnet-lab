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

prefix = '' if len(sys.argv) <= 1 else sys.argv[1]

def run(protocol, files, csvfile):
	for path in sorted(glob.glob(files)):
		(node_count, link_count) = tools.json_count(path)

		# Limit node count to 300
		if node_count > 300:
			continue

		print(f'run {protocol} on {path}')

		network.change(from_state='none', to_state=path, force_tc='')

		tools.sleep(10)

		for offset in range(0, 60, 2):
			beg_ts = tools.traffic()
			beg_ms = tools.millis()

			software.start(protocol)

			tools.sleep(offset)

			ping_result = tools.ping(protocol=protocol, path_count=link_count, duration_ms=60000)

			end_ts = tools.traffic()
			end_ms = tools.millis()

			sysload_result = tools.sysload()

			# add data to csv file
			tools.csv_update(csvfile, '\t',
				tools.Wrapper(['startup_ms', 'wait_ms'], [end_ms - beg_ms, offset * 1000]), (end_ts - beg_ts), ping_result, sysload_result)

			exit(1)
			software.stop(protocol)

		network.clear()

for name in ['line', 'grid4', 'rtree']:
	for protocol in ['olsr2', 'batman-adv', 'yggdrasil', 'babel', 'bmx6', 'bmx7', 'cjdns']:
		with open(f"{prefix}convergence1-{protocol}-{name}.csv", 'w+') as csvfile:
			run(protocol, f"../../data/{name}/*.json", csvfile)
