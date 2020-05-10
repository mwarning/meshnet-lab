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

def run(protocol, csvfile):
	tools.seed_random(23)

	node_count = 50
	state = topology.create_nodes(node_count)
	mobility.randomize_positions(state, xy_range=1000)
	mobility.connect_range(state, max_links=150)

	# create network and start routing software
	network.change(from_state={}, to_state=state, link_command=get_tc_command)
	software.start(protocol)
	tools.sleep(30)

	for step_distance in [50, 100, 150, 200, 250, 300, 350, 400]:
		print(f'{protocol}: step_distance {step_distance}')

		traffic_beg = tools.traffic()
		for n in range(0, 6):
			#with open(f'graph-{step_distance}-{n}.json', 'w+') as file:
			#	json.dump(state, file, indent='  ')

			# connect nodes range
			wait_beg_ms = tools.millis()

			# update network representation
			old_state = copy.copy(state)
			mobility.move_random(state, distance=step_distance)
			mobility.connect_range(state, max_links=150)

			# update network
			network.change(from_state=old_state, to_state=state, link_command=get_tc_command)

			# Wait until wait seconds are over, else error
			tools.wait(wait_beg_ms, 10)

			paths = tools.get_random_paths(state, 200)
			paths = tools.filter_paths(state, paths, min_hops=2, max_hops=node_count)
			ping_result = tools.ping_paths(paths=paths, duration_ms=2000, verbosity='verbose')

			packets_arrived_pc = 100 * (ping_result.received / ping_result.send)
			traffic_end = tools.traffic()

			# add data to csv file
			extra = (['node_count', 'time_ms', 'step_distance_m', 'n', 'packets_arrived_pc'], [node_count, tools.millis() - wait_beg_ms, step_distance, n, packets_arrived_pc])
			tools.csv_update(csvfile, '\t', extra, (traffic_end - traffic_beg).getData())

			traffic_beg = traffic_end

	software.stop(protocol)
	network.clear()

# remove none, after it has been verified to be 0% (also for mobility1)
for protocol in ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'yggdrasil']:
	with open(f"{prefix}mobility2-{protocol}.csv", 'w+') as csvfile:
		run(protocol, csvfile)
