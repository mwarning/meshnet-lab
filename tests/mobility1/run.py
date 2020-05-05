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

# 100MBit LAN cable
def get_tc_command(link, ifname):
	return f'tc qdisc replace dev "{ifname}" root tbf rate 100mbit burst 8192 latency 1ms'

def run(protocol, csvfile, step_duration, step_distance):
	tools.seed_random(42)

	state = topology.create_nodes(50)
	mobility.randomize_positions(state, xy_range=1.0)
	mobility.connect_range(state, max_links=150)

	# create network and start routing software
	network.change(from_state={}, to_state=state, link_command=get_tc_command)
	software.start(protocol)

	test_beg_ms = tools.millis()
	for n in range(0, 30):
		print(f'{protocol}: iteration {n}')

		#with open(f'graph-{step_duration}-{step_distance}-{n:03d}.json', 'w+') as file:
		#	json.dump(state, file, indent='  ')

		# connect nodes range
		wait_beg_ms = tools.millis()

		# update network representation
		old_state = copy.copy(state)
		mobility.move_random(state, distance=step_distance)
		mobility.connect_range(state, max_links=150)

		# update network
		tmp_ms = tools.millis()
		network.change(from_state=old_state, to_state=state, link_command=get_tc_command)
		#software.change(protocol=protocol, from_state=old_state, to_state=state) # we do not change the node count
		network_ms = tools.millis() - tmp_ms

		# Wait until wait seconds are over, else error
		tools.wait(wait_beg_ms, step_duration)

		paths = tools.get_random_paths(state, 200)
		valid_path_count = tools.get_valid_path_count(state, paths)
		ping_result = tools.ping_paths(protocol=protocol, paths=paths, duration_ms=2000, verbosity='verbose')

		# add data to csv file
		extra = (['time_ms', 'node_count', 'valid_path_count'], [tools.millis() - test_beg_ms, len(state['nodes']), valid_path_count])
		tools.csv_update(csvfile, '\t', extra, ping_result)

	software.stop(protocol)
	network.clear()

for step_duration in [10, 30]:
	for step_distance in [0.01, 0.03, 0.06]:
		for protocol in ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'none', 'olsr1', 'olsr2', 'yggdrasil']:
			with open(f"{prefix}mobility1-{step_duration}-{step_distance}-{protocol}.csv", 'w+') as csvfile:
				run(protocol, csvfile, step_duration, step_distance)
