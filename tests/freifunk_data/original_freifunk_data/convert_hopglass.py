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

links = {}

# map to give each node a short number
nodes = {}

with open(args.input, "r") as file:
	obj = json.load(file)

	# record all nodes
	for node in obj['JSON']['rows']:
		if node['id'] not in nodes:
			nodes[node['id']] = {'id': len(nodes), 'label': node['id']}

		if 'links' not in node['value']:
			continue

		for lnode in node['value']['links']:
			if lnode['id'] not in nodes:
				nodes[lnode['id']] = {'id': str(len(nodes)), 'name': lnode['id']}

	for node in obj['JSON']['rows']:
		source = node['id']

		if 'links' not in node['value']:
			continue

		for lnode in node['value']['links']:
			target = lnode['id']
			if source > target:
				link_id = "{}->{}".format(source, target)
			else:
				link_id = "{}->{}".format(target, source)

			if link_id not in links:
				links[link_id] = {'source': nodes[source]['id'], 'target': nodes[target]['id']}

if args.formatted:
	json.dump({'nodes': list(nodes.values()), 'links': list(links.values())}, sys.stdout, indent="  ", sort_keys = True)
else:
	json.dump({'nodes': list(nodes.values()), 'links': list(links.values())}, sys.stdout, sort_keys = True)
