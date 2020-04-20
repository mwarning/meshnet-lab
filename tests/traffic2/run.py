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
protocol = 'batman-adv'
name = 'grid4'

with open(f"{prefix}traffic2-{protocol}-{name}.csv", 'w+') as csvfile:
	for path in sorted(glob.glob(f'../../data/{name}/*.json')):
		(node_count, link_count) = tools.json_count(path)

		# Limit node count to 300
		if node_count > 300:
			continue

		print(f'run {protocol} on {path}')

		network.change(from_state='none', to_state=path, force_tc='')
		tools.sleep(10)

		for i in range(0, 10):
			beg_ms = tools.millis()
			beg_ts = tools.traffic()

			software.start(protocol)

			# Wait until 60s are over, else error
			tools.wait(beg_ms, 60)

			ping_result = tools.ping(protocol=protocol, path_count=link_count, duration_ms=60000)

			end_ts = tools.traffic()
			end_ms = tools.millis()

			sysload_result = tools.sysload()

			software.stop(protocol)

			# add data to csv file
			tools.csv_update(csvfile, '\t', tools.Wrapper('startup_ms', end_ms - beg_ms), (end_ts - beg_ts), ping_result, sysload_result)

		network.clear()
