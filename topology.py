#!/usr/bin/env python3

import random
import argparse
import json
import sys
import os
import glob


def eprint(s):
    sys.stderr.write(s + '\n')

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
parser.add_argument('--source-tc', help='Value for each links source_tc.')
parser.add_argument('--target-tc', help='Value for each links target_tc.')
parser.add_argument('--formatted', action='store_true', help='Output formatted json.')

subparsers = parser.add_subparsers(dest='topology', required=True)
parser_lattice4 = subparsers.add_parser('lattice4', help='Create a lattice structure with horizontal and vertical connections.')
parser_lattice4.add_argument('n', type=int, help='Node count in X direction.')
parser_lattice4.add_argument('m', type=int, help='Node count in Y direction.')
parser_lattice8 = subparsers.add_parser('lattice8', help='Create a lattice structure of horizontal, vertical and vertical connections.')
parser_lattice8.add_argument('n', type=int, help='Node count in X direction.')
parser_lattice8.add_argument('m', type=int, help='Node count in Y direction.')
parser_circle = subparsers.add_parser('circle', help='Create nodes connected into a circle.')
parser_circle.add_argument('n', type=int, help='Node count.')
parser_line = subparsers.add_parser('line', help='Create nodes connected in a line.')
parser_line.add_argument('n', type=int, help='Node count.')
parser_tree = subparsers.add_parser('tree', help='Create nodes connected in a balanced regular tree.')
parser_tree.add_argument('depth', type=int, help='Depth of the tree.')
parser_tree.add_argument('degree', type=int, help='Number of tree branches.')
parser_rtree = subparsers.add_parser('rtree', help='Create nodes connected in a random tree.')
parser_rtree.add_argument('count', type=int, help='Number of nodes.')
parser_rtree.add_argument('intra', type=int, help='Intraconnections that disrupt the tree structure.')

args = parser.parse_args()

links = []

if args.topology == 'lattice4':
    links = create_lattice(args.n, args.m, diag = False)
elif args.topology == 'lattice8':
    links = create_lattice(args.n, args.m, diag = True)
elif args.topology == 'circle':
    links = create_line(args.n, loop = True)
elif args.topology == 'line':
    links = create_line(args.n, loop = False)
elif args.topology == 'tree':
    links = create_tree(args.depth, args.degree)
elif args.topology == 'rtree':
    links = create_random_tree(args.count, args.intra)
else:
    eprint('Unknown topology: {}\n'.format(args.topology))
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
