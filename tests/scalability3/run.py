#!/usr/bin/env python3

import os
import sys
import glob
import random

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

def get_paths(network, towards_sink=True):
	def get_nodes(network):
		nodes = set()

		for node in network.get('nodes', []):
			nodes.add(str(node['id']))

		for link in network.get('links', []):
			nodes.add(str(link['source']))
			nodes.add(str(link['target']))

		return list(nodes)

	nodes = get_nodes(network)

	# random order
	random.shuffle(nodes)

	# node with lowest id as sink
	sink_id = None
	for node_id in nodes:
		if sink_id is None:
			sink_id = node_id
		elif node_id < sink_id:
			sink_id = node_id

	paths = []
	for node_id in nodes:
		if node_id != sink_id:
			if towards_sink:
				paths.append((node_id, sink_id))
			else:
				paths.append((sink_id, node_id))

	return paths

def run(topology, path, state, towards_sink):
	(node_count, link_count) = shared.json_count(state)

	with open(f'{prefix}scalability3-{protocol}-{topology}.csv', 'a') as csvfile:
		print(f'run {protocol} on {path}')

		# Start routing software
		software_start_ms = shared.millis()
		software.start(protocol, remotes)
		software_stop_ms = shared.millis()

		# Let the nodes start up and discover themselves.
		shared.sleep(60)

		traffic_start_ms = shared.millis()
		traffic_begin = traffic.traffic(remotes)

		# Send "<node_count> - 1" pings
		paths = get_paths(state, False)
		ping_result = ping.ping(remotes=remotes, paths=paths, duration_ms=(1000*len(paths)), verbosity='verbose')

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

# Keep track of tests that exceed the machines resources and drop bigger networks
drop_test = set()
protocols = ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'yggdrasil']

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
