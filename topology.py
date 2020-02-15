#!/usr/bin/env python3

import random
import argparse
import json
import sys
import os
import glob

def create_lattice(x_count, y_count, diag = False):
    links = []
    offset = 0

    if x_count < 1 or y_count < 1:
        return links

    def connect(x1, y1, x2, y2):
        # validate coordinates
        if (x2 < x_count) and (y2 < y_count):
            a = offset + x1 * y_count + y1
            b = offset + x2 * y_count + y2
            links.append({'source': a, 'target': b})

    for x in range(0, x_count):
        for y in range(0, y_count):
            if diag:
                connect(x, y, x + 1, y + 1)
                if y > 0:
                    connect(x, y, x + 1, y - 1)
            connect(x, y, x, y + 1)
            connect(x, y, x + 1, y)

    return links

def create_line(count, loop = False):
    links = []
    offset = 0

    if count < 1:
        return links

    for i in range(0, count):
        if i > 0:
            links.append({'source': (offset + i - 1), 'target': (offset + i)})

    if loop and (count > 2):
        links.append({'source': (offset + 0), 'target': (offset + count - 1)})

    return links

def create_tree(depth, degree):
    links = []
    i = 0
    j = 0

    for d in range(0, depth):
        for _ in range(0, 0 + int(degree ** d)):
            for _ in range(0, degree):
                j += 1
                links.append({'source': i, 'target': j})
            i += 1

    return links

def create_random_tree(count, intra = 0):
    links = {}

    def get_id(i, j):
        if i > j:
            return '{}-{}'.format(i, j)
        else:
            return '{}-{}'.format(j, i)

    # Connect random nodes
    for i in range(1, count):
        # Connect node with random previous node
        while True:
            j = random.randint(0, i)
            id = get_id(i, j)
            if i != j and id not in links:
                links[id] = {'source': i, 'target': j}
                break

    return list(links.values())


parser = argparse.ArgumentParser()
parser.add_argument('geometry',
    choices=['lattice4', 'lattice8', 'circle', 'line', 'tree', 'rtree'],
    help='Geometry to be created.')
parser.add_argument('ns', nargs='+', type=int,
    help='Number argumets for the geometry.')
parser.add_argument('--source-tc',
    help='Value for each links source_tc.')
parser.add_argument('--target-tc',
    help='Value for each links target_tc.')
parser.add_argument('--formatted',
    help='Output formatted json.')

args = parser.parse_args()

links = []

if args.geometry == 'lattice4':
  if len(args.ns) == 2:
    links = create_lattice(args.ns[0], args.ns[1], diag = False)
  else:
    sys.stderr.write('Number of x and y nodes expected for lattice4.\n')
    exit(1)
elif args.geometry == 'lattice8':
  if len(args.ns) == 2:
    links = create_lattice(args.ns[0], args.ns[1], diag = True)
  else:
    sys.stderr.write('Number of x and y nodes expected for lattice8.\n')
    exit(1)
elif args.geometry == 'circle':
  if len(args.ns) == 1:
    links = create_line(args.ns[0], loop = True)
  else:
    sys.stderr.write('Number of nodes expected for circle.\n')
    exit(1)
elif args.geometry == 'line':
  if len(args.ns) == 1:
    links = create_line(args.ns[0], loop = False)
  else:
    sys.stderr.write('Number of nodes expected for line.\n')
    exit(1)
elif args.geometry == 'tree':
  if len(args.ns) == 2:
    links = create_tree(args.ns[0], args.ns[1])
  else:
    sys.stderr.write('Depth and degree expected for tree.\n')
    exit(1)
elif args.geometry == 'rtree':
  if len(args.ns) == 2:
    links = create_random_tree(args.ns[0], args.ns[1])
  else:
    sys.stderr.write('Number of nodes and interconnections expected for random tree.\n')
    exit(1)
else:
  sys.stderr.write('Unknown geometry: {}\n'.format(args.geometry))
  exit(1)

for link in links:
    if args.source_tc:
        link['source_tc'] = args.source_tc
    if args.target_tc:
        link['target_tc'] = args.target_tc

if args.formatted:
    json.dump({'links': links}, sys.stdout, indent="  ")
else:
    json.dump({'links': links}, sys.stdout)
