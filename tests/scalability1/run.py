#!/usr/bin/env python3

import os
import sys
import glob

sys.path.append('../../')
import software
import network
from shared import Remote
import shared
import traffic
import ping


# Increase limit for all the parallel pings
os.system('ulimit -Sn 4096')

remotes= [Remote()]

shared.check_access(remotes)
software.copy(remotes, '../../protocols', '/var/')

# Cleanup environment
software.clear(remotes)
network.clear(remotes)

prefix = os.environ.get('PREFIX', '')

def run(topology, path, state):
	(node_count, link_count) = shared.json_count(state)

	with open(f'{prefix}scalability1-{protocol}-{topology}.csv', 'a') as csvfile:
		print(f'run {protocol} on {path}')

		# Start routing software
		software_start_ms = shared.millis()
		software.start(protocol, remotes)
		software_stop_ms = shared.millis()

		# Let the nodes start up and discover themselves.
		shared.sleep(60)

		traffic_start_ms = shared.millis()
		traffic_begin = traffic.traffic(remotes)

		# Send <node_count> pings.
		# For a good routing algorithm, the traffic per node should be constant.
		paths = ping.get_random_paths(state, 2 * node_count)
		paths = ping.filter_paths(state, paths, min_hops=2, path_count=node_count)
		ping_result = ping.ping(remotes=remotes, paths=paths, duration_ms=300000, verbosity='verbose')

		traffic_stop_ms = shared.millis()
		traffic_end = traffic.traffic(remotes)

		sysload_result = shared.sysload(remotes)

		# Stop routing software
		software.clear(remotes)

		# Add data to csv file
		extra = (['node_count', 'software_startup_ms', 'traffic_measurement_ms'],
			[node_count, (software_stop_ms - software_start_ms), (traffic_stop_ms - traffic_start_ms)])
		shared.csv_update(csvfile, '\t', extra,
			(traffic_end - traffic_begin).getData(), ping_result.getData(), sysload_result)

		return (100.0 * ping_result.received / ping_result.send)

# Keep track of tests that exceed the machines resources and skip bigger networks
drop_test = set()
protocols = ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'ospf', 'yggdrasil']

for topology in ['line', 'grid4', 'grid8', 'rtree']:
	for path in sorted(glob.glob(f'../../data/{topology}/*.json')):
		state = shared.load_json(path)
		(node_count, link_count) = shared.json_count(state)

		# No test to be done for this topology
		if all((f'{p}_{topology}' in drop_test) for p in protocols):
			continue

		# Create network
		network.apply(state=state, remotes=remotes)

		for protocol in protocols:
			if f'{protocol}_{topology}' in drop_test:
				continue

			pc = run(topology, path, state)

			# Skip test if the successful pings drop below 60%
			if pc < 60:
				print(f'Less than 60% successful pings for {protocol} on {topology} with {node_count} nodes => skip other')
				drop_test.add(f'{protocol}_{topology}')

		# Remove network
		network.clear(remotes)

shared.stop_all_terminals()
print("finished")
