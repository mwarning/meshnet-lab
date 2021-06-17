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
import ping
from shared import Remote
import shared


remotes= [Remote()]

shared.check_access(remotes)
software.clear(remotes)
network.clear(remotes)

prefix = os.environ.get('PREFIX', '')

# 100MBit LAN cable
def get_tc_command(link, ifname):
	return f'tc qdisc replace dev "{ifname}" root tbf rate 100mbit burst 8192 latency 1ms'

def run(protocol, csvfile, step_duration, step_distance):
	shared.seed_random(42)

	node_count = 50
	state = topology.create_nodes(node_count)
	mobility.randomize_positions(state, xy_range=1000)
	mobility.connect_range(state, max_links=150)

	# create network and start routing software
	network.apply(state, link_command=get_tc_command, remotes=remotes)
	software.start(protocol)

	test_beg_ms = shared.millis()
	for n in range(0, 30):
		print(f'{protocol}: iteration {n}')

		#with open(f'graph-{step_duration}-{step_distance}-{n:03d}.json', 'w+') as file:
		#	json.dump(state, file, indent='  ')

		# connect nodes range
		wait_beg_ms = shared.millis()

		# update network representation
		mobility.move_random(state, distance=step_distance)
		mobility.connect_range(state, max_links=150)

		# update network
		tmp_ms = shared.millis()
		network.apply(state=state, link_command=get_tc_command, remotes=remotes)
		#software.apply(protocol=protocol, state=state) # we do not change the node count
		network_ms = shared.millis() - tmp_ms

		# Wait until wait seconds are over, else error
		shared.wait(wait_beg_ms, step_duration)

		paths = ping.get_random_paths(state, 2 * 400)
		paths = ping.filter_paths(state, paths, min_hops=2, path_count=200)
		ping_result = ping.ping(paths=paths, duration_ms=2000, verbosity='verbose', remotes=remotes)

		# add data to csv file
		extra = (['node_count', 'time_ms'], [node_count, shared.millis() - test_beg_ms])
		shared.csv_update(csvfile, '\t', extra, ping_result.getData())

	software.clear(remotes)
	network.clear(remotes)

for step_duration in [10, 30]:
	for step_distance in [10, 30, 60]:
		for protocol in ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'ospf', 'yggdrasil']:
			with open(f"{prefix}mobility1-{step_duration}-{step_distance}-{protocol}.csv", 'w+') as csvfile:
				run(protocol, csvfile, step_duration, step_distance)

shared.stop_all_terminals()
