#!/usr/bin/env python3

import os
import sys
import glob
import copy
import math
import json

sys.path.append('../../')
import topology
import mobility
import shared
import ping


prefix = os.environ.get('PREFIX', '')

def get_all_paths(node_count):
	paths = []
	for i in range(0, node_count):
		for j in range(0, i):
			if i != j:
				paths.append((i, j))
	return paths

def float_range(start, stop, step):
	while start < stop:
		yield float(start)
		start += step

def get_mean_geo_distance(state, paths):
	nodes = {}
	for node in state['nodes']:
		nodes[node['id']] = node

	distance = 0
	for path in paths:
		distance += mobility.get_distance(nodes[path[0]], nodes[path[1]])

	return distance / len(paths)

def get_connectivity(state, paths):
	dijkstra = ping.Dijkstra(state)
	path_count = 0
	hop_count = 0
	max_hop_count = 0

	for path in paths:
		d = dijkstra.find_shortest_distance(path[0], path[1])
		if d is not math.inf:
			path_count += 1
			hop_count += d
			if d > max_hop_count:
				max_hop_count = d

	median_hop_count = 0 if path_count == 0 else (hop_count / path_count)
	return (path_count, median_hop_count, max_hop_count)


def run(node_count, csvfile):
	print(f'run for node_count: {node_count}')

	state = topology.create_nodes(node_count)
	for max_range in float_range(0.0, 0.8, 0.01):
		# calculate every value 100 times
		for _ in range(0, 100):
			mobility.randomize_positions(state, xy_range=1.0)
			mobility.connect_range(state, max_distance=max_range)

			paths = get_all_paths(node_count)

			(connected_path_count, connected_median_hop_count, connected_max_hop_count) = get_connectivity(state, paths)
			mean_geo_distance = get_mean_geo_distance(state, paths)

			# add data to csv file
			connectivity_per = 100 * connected_path_count / len(paths)
			extra = (
				['node_count', 'max_range', 'mean_geo_distance', 'connectivity_per', 'connected_median_hop_count', 'connected_max_hop_count'],
				[node_count, max_range, mean_geo_distance, connectivity_per, connected_median_hop_count, connected_max_hop_count]
			)
			shared.csv_update(csvfile, '\t', extra)

for node_count in [10, 20, 30, 40, 50]:
	with open(f'{prefix}connectivity1-{node_count}.csv', 'w+') as csvfile:
		run(node_count, csvfile)

shared.stop_all_terminals()
