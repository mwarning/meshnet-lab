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
		return f'{source}=>{target}'
	else:
		return f'{target}=>{source}'

with open(args.input, "r") as file:
	obj = json.load(file)

	for node in obj['nodes']:
		if 'is_online' in node:
			if not node['is_online']:
				continue

		e = {'id': len(nodes)}

		if 'location' in node:
			x = node['location'].get('latitude')
			y = node['location'].get('longitude')
			if y is not None and x is not None:
				e['x'] = float(x)
				e['y'] = float(y)


		if 'hostname' in node:
			e['name'] = node['hostname']

		nodes[node['node_id']] = e

	for link in obj['links']:
		source = link['source']
		target = link['target']

		if source not in nodes:
			continue

		if target not in nodes:
			continue

		e = {
			'source': nodes[source]['id'],
			'target': nodes[target]['id'],
			'source_tq': link['source_tq'],
			'target_tq': link['target_tq']
		}

		if link.get('type') == 'other':
			e['type'] = 'other'
		elif nodes[source].get('is_gateway', False) or nodes[target].get('is_gateway', False):
			e['type'] = 'vpn'
		else:
			e['type'] = 'wifi'

		links[link_id(e)] = e

	# add gateway nodes/links
	for node in obj['nodes']:
		if 'is_online' in node:
			if not node['is_online']:
				continue

		gateway = node.get('gateway')
		nexthop = node.get('gateway_nexthop')
		if gateway is not None and nexthop is not None:
			gw_node_id = gateway.replace(':', '')
			node_id = node['node_id']

			# add gateway
			if gw_node_id not in nodes:
				nodes[gw_node_id] = {'id': len(nodes), 'name': gw_node_id}

			link = {
				'source': nodes[gw_node_id]['id'],
				'target': nodes[node_id]['id'],
				'type': 'vpn'
			}

			# add link to gateway
			if link_id(link) not in links:
				links[link_id(link)] = link

network = {'nodes': list(nodes.values()), 'links': list(links.values())}

if args.connected:
	shared.make_connected(network)

if args.formatted:
	json.dump(network, sys.stdout, indent="  ", sort_keys=True)
else:
	json.dump(network, sys.stdout, sort_keys=True)
