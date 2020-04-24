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
tc = os.environ.get('TC', '')
wait = os.environ.get('WAIT', 60)

print(f'prefix: "{prefix}", wait: "{wait}", tc: "{tc}"')

protocol = 'batman-adv'
name = 'grid4'

with open(f"{prefix}traffic2-{protocol}-{name}.csv", 'w+') as csvfile:
	for path in sorted(glob.glob(f'../../data/{name}/*.json')):
		(node_count, link_count) = tools.json_count(path)

		# Limit node count to 300
		if node_count > 300:
			continue

		print(f'run {protocol} on {path}')

		network.change(from_state='none', to_state=path, force_tc=tc)
		tools.sleep(10)

		for i in range(0, 10):
			wait_beg_ms = tools.millis()

			software.start(protocol)

			# Wait until 60s are over, else error
			tools.wait(wait_beg_ms, wait)

			ping_result = tools.ping(protocol=protocol, count=link_count, duration_ms=60000, verbosity='verbose')

			sysload_result = tools.sysload()

			software.stop(protocol)

			# add data to csv file
			extra = tools.Wrapper(['node_count'], [node_count])
			tools.csv_update(csvfile, '\t', extra, ping_result, sysload_result)

		network.clear()
