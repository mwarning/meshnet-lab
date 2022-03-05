#!/usr/bin/env python3

from pathlib import Path
import argparse
import json
import sys
import os

sys.path.append('../../../')
import shared


parser = argparse.ArgumentParser()
parser.add_argument("input", help="Input meshviewer file.")
parser.add_argument('--formatted', action="store_true", help="Formatted JSON output data.")
parser.add_argument('--connected', action="store_true", help="Create a connected network.")
args = parser.parse_args()

# map to give each node a short number
nodes = {}
links = {}

def link_id(link):
	source = link['source']
	target = link['target']
	if source > target:
		return f"{source}->{target}"
	else:
		return f"{target}->{source}"

with open(args.input, "r") as file:
	obj = json.load(file)

	# record all nodes
	for node in obj['JSON']['rows']:
		e = {'id': len(nodes)}

		if 'hostname' in node['value']:
			e['name'] = node['value']['hostname']

		if 'latlng' in node['value']:
			e['x'] = float(node['value']['latlng'][0])
			e['y'] = float(node['value']['latlng'][1])

		nodes[node['id']] = e

		if 'links' in node['value']:
			for lnode in node['value']['links']:
				if lnode['id'] not in nodes:
					e = {'id': len(nodes)}

					if lnode['id'].endswith('.olsr'):
						e['name'] = lnode['id'][:-5]

					nodes[lnode['id']] = e

	for node in obj['JSON']['rows']:
		if 'links' not in node['value']:
			continue

		for lnode in node['value']['links']:
			target = lnode['id']

			link = {
				'source': nodes[node['id']]['id'],
				'target': nodes[lnode['id']]['id']
			}

			if link['source'] == link['target']:
				continue

			if 'wifi' in lnode:
				link['type'] = 'wifi'
			else:
				link['type'] = 'vpn'

			if 'olsr_ipv4' in lnode:
				link_quality = lnode['olsr_ipv4']['linkQuality']
				link['source_tq'] = link_quality
				link['target_tq'] = link_quality

			lid = link_id(link)
			if lid not in links:
				links[lid] = link

network = {'nodes': list(nodes.values()), 'links': list(links.values())}

if args.connected:
	shared.make_connected(network)

if args.formatted:
	json.dump(network, sys.stdout, indent="  ", sort_keys=True)
else:
	json.dump(network, sys.stdout, sort_keys=True)

