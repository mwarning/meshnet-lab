#!/usr/bin/env python3

import os
import sys
import glob
import copy

import json

sys.path.append('../../')
import software
import network
import topology
import mobility
import tools


prefix = os.environ.get('PREFIX', '')

tools.root()
software.clear()
network.clear()

os.system('ulimit -Sn 4096')

def run(protocol, csvfile, tc = ''):
	state = topology.create_nodes(20)
	mobility.randomize_positions(state, xy_range=1)
	mobility.connect_range(state, max_distance=0.5, max_links=50)

	# create network and start routing software
	network.change(from_state={}, to_state=state, force_tc=tc)
	software.start(protocol)

	test_beg_ms = tools.millis()
	for n in range(0, 20):
		print(f'{protocol}: iteration {n}')

		with open('graph.json', 'w+') as file:
			json.dump(state, file, indent='  ')

		# connect nodes range
		wait_beg_ms = tools.millis()

		# update network representation
		old_state = copy.copy(state)
		mobility.move_random(state, distance=0.03)
		mobility.connect_range(state, max_distance=0.5, max_links=50)

		# update network
		tmp_ms = tools.millis()
		network.change(from_state=old_state, to_state=state, force_tc=tc)
		#software.change(protocol=protocol, from_state=old_state, to_state=state) # we do not change the node count
		network_ms = tools.millis() - tmp_ms

		# Wait until wait seconds are over, else error
		tools.wait(wait_beg_ms, 10)

		paths = tools.get_random_paths(state, 100, seed=n)
		valid_path_count = tools.get_valid_path_count(state, paths)
		ping_result = tools.ping_paths(protocol=protocol, paths=paths, duration_ms=1000, verbosity='verbose')

		# add data to csv file
		extra = (['time_ms', 'node_count', 'valid_path_count'], [tools.millis() - test_beg_ms, len(state['nodes']), valid_path_count])
		tools.csv_update(csvfile, '\t', extra, ping_result)

	software.stop(protocol)
	network.clear()


for protocol in ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'yggdrasil']:
	with open(f"{prefix}mobility1-{protocol}.csv", 'w+') as csvfile:
		run(protocol, csvfile)
