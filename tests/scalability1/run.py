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

def run(protocol, files, csvfile, tc = ''):
	for path in sorted(glob.glob(files)):
		(node_count, link_count) = tools.json_count(path)

		# Limit node count to 300
		if node_count > 300:
			continue

		print(f'run {protocol} on {path}')

		network.change(from_state='none', to_state=path, force_tc=tc)

		tools.sleep(10)

		wait_beg_ms = tools.millis()

		tmp_ms = tools.millis()
		traffic_beg = tools.traffic()
		traffic_ms = tools.millis() - tmp_ms

		tmp_ms = tools.millis()
		software.start(protocol)
		software_ms = tools.millis() - tmp_ms

		# Wait until wai seconds are over, else error
		tools.wait(wait_beg_ms, wait)

		ping_result = tools.ping(protocol=protocol, count=link_count, duration_ms=60000, verbosity='verbose')

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
