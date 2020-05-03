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

def run(protocol, files, csvfile):
	for path in sorted(glob.glob(files)):
		(node_count, link_count) = tools.json_count(path)

		print(f'run {protocol} on {path}')

		network.change(from_state='none', to_state=path)

		tools.sleep(10)

		for offset in range(0, 60, 2):
			tmp_ms = tools.millis()
			traffic_beg = tools.traffic()
			traffic_ms = tools.millis() - tmp_ms

			tmp_ms = tools.millis()
			software.start(protocol)
			software_ms = tools.millis() - tmp_ms

			# Wait until wait seconds are over, else error
			tools.sleep(offset)

			ping_result = tools.ping(protocol=protocol, count=200, duration_ms=2000, verbosity='verbose', seed=1234)

			traffic_end = tools.traffic()

			sysload_result = tools.sysload()

			software.stop(protocol)

			# add data to csv file
			extra = (['node_count', 'traffic_ms', 'software_ms', 'offset_ms'], [node_count, traffic_ms, software_ms, offset * 1000])
			tools.csv_update(csvfile, '\t', extra, (traffic_end - traffic_beg).getData(), ping_result, sysload_result)

		network.clear()

for file in ['../../data/line/line-0050.json', '../../data/grid4/grid4-0049.json', '../../data/rtree/rtree-0050.json']:
	for protocol in ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'none', 'olsr1', 'olsr2', 'yggdrasil']:
		name = file.split('/')[-2]
		with open(f"{prefix}convergence1-{protocol}-{name}.csv", 'w+') as csvfile:
			run(protocol, file, csvfile)
