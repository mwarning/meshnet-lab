#!/usr/bin/env python3

import argparse
import json


parser = argparse.ArgumentParser(
	description='Read a JSON file and output a value.')
parser.add_argument('input', help='Input JSON file')
parser.add_argument('action', choices=['count-nodes', 'count-links'], help='Action')

args = parser.parse_args()

if args.action == 'count-nodes':
	obj = json.load(open(args.input))
	nodes = obj.get('nodes', [])
	print(len(nodes))
elif args.action == 'count-links':
	obj = json.load(open(args.input))
	links = obj.get('links', [])
	print(len(links))
else:
	print('Unknown action: {}'.format(args.action))
	exit(1)
