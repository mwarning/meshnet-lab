#!/usr/bin/env python3

from pathlib import Path
import argparse
import json
import sys
import os


parser = argparse.ArgumentParser()
parser.add_argument("input", help="Input meshviewer file.")
parser.add_argument('--formatted', action="store_true", help="Formatted JSON output data.")
args = parser.parse_args()

links = []

# map to give each node a short number
nodes = {}

with open(args.input, "r") as file:
	obj = json.load(file)

	for node in obj['nodes']:
		nodes[node['node_id']] = {'id': str(len(nodes)), 'name': node['hostname']}

	for link in obj['links']:
		source = link['source']
		target = link['target']
		source_tq = link['source_tq']
		target_tq = link['target_tq']

		# TODO: set source_tc and target_tc
		links.append({'source': nodes[source], 'target': nodes[target]})

if args.formatted:
	json.dump({'nodes': list(nodes.values()), 'links': links}, sys.stdout, indent="  ", sort_keys = True)
else:
	json.dump({'nodes': list(nodes.values()), 'links': links}, sys.stdout, sort_keys = True)

print(len(nodes))