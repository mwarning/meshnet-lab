#!/usr/bin/env python3

import random
import argparse
import json
import sys
import os
import glob
import math

def eprint(s):
    sys.stderr.write(s + '\n')

def create_grid(x_count, y_count, diag = False):
    nodes = []
    links = []

    if x_count < 1 or y_count < 1:
        return links

    def connect(x1, y1, x2, y2):
        # validate coordinates
        if (x2 < x_count) and (y2 < y_count):
            a = x1 * y_count + y1
            b = x2 * y_count + y2
            links.append({'source': a, 'target': b})

    for x in range(0, x_count):
        for y in range(0, y_count):
            nodes.append({'id': (x + y * x_count), 'x': x, 'y': y})
            if diag:
                connect(x, y, x + 1, y + 1)
                if y > 0:
                    connect(x, y, x + 1, y - 1)
            connect(x, y, x, y + 1)
            connect(x, y, x + 1, y)

    return {'nodes': nodes, 'links': links}

def create_line(count, loop = False):
    nodes = []
    links = []

    if count < 1:
        return links

    for i in range(0, count):
        if loop:
            nodes.append({'id': i, 'x': math.sin(i * 2 * math.pi / count), 'y': math.cos(i * 2 * math.pi / count)})
        else:
            nodes.append({'id': i, 'x': i, 'y': 0})

        if i > 0:
            links.append({'source': (i - 1), 'target': (i)})

    if loop and (count > 2):
        links.append({'source': (0), 'target': (count - 1)})

    return {'nodes': nodes, 'links': links}

def create_tree(depth, degree):
    nodes = []
    links = []
    i = 0
    j = 0

    for d in range(0, depth):
        for k in range(0, 0 + int(degree ** d)):
            nodes.append({'id': i, 'x': k, 'y': d})
            for _ in range(0, degree):
                j += 1
                links.append({'source': i, 'target': j})
            i += 1

    return {'nodes': nodes, 'links': links}

def create_random_tree(count, intra = 0):
    nodes = []
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
                nodes.append({'id': i, 'x': i, 'y': j})
                links[id] = {'source': i, 'target': j}
                break

    return {'nodes': nodes, 'links': list(links.values())}

def create_full(count):
    nodes = []
    links = []

    for i in range(0, count):
        nodes.append({'id': i})

    for i in range(0, count):
        for j in range(0, count):
            if i < j:
                links.append({'source': i, 'target': j})

    return {'nodes': nodes, 'links': links}

def create_nodes(count):
    nodes = []

    for i in range(0, count):
        nodes.append({'id': i})

    return {'nodes': nodes, 'links': []}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-tc', help='Value for each links source_tc.')
    parser.add_argument('--target-tc', help='Value for each links target_tc.')
    parser.add_argument('--no-nodes', action='store_true', help='Omit nodes from output.')
    parser.add_argument('--no-links', action='store_true', help='Omit links from output.')
    parser.add_argument('--formatted', action='store_true', help='Output formatted json.')

    subparsers = parser.add_subparsers(dest='topology', required=True)
    parser_grid4 = subparsers.add_parser('grid4', help='Create a grid structure with horizontal and vertical connections.')
    parser_grid4.add_argument('n', type=int, help='Node count in X direction.')
    parser_grid4.add_argument('m', type=int, help='Node count in Y direction.')
    parser_grid8 = subparsers.add_parser('grid8', help='Create a grid structure of horizontal, vertical and vertical connections.')
    parser_grid8.add_argument('n', type=int, help='Node count in X direction.')
    parser_grid8.add_argument('m', type=int, help='Node count in Y direction.')
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
    parser_full = subparsers.add_parser('full', help='Create a full mesh. Every node is connected to everybody else.')
    parser_full.add_argument('n', type=int, help='Number of nodes.')
    parser_nodes = subparsers.add_parser('nodes', help='Create nodes.')
    parser_nodes.add_argument('count', type=int, help='Number of nodes.')

    args = parser.parse_args()

    output = None

    if args.topology == 'grid4':
        output = create_grid(args.n, args.m, diag = False)
    elif args.topology == 'grid8':
        output = create_grid(args.n, args.m, diag = True)
    elif args.topology == 'circle':
        output = create_line(args.n, loop = True)
    elif args.topology == 'line':
        output = create_line(args.n, loop = False)
    elif args.topology == 'tree':
        output = create_tree(args.depth, args.degree)
    elif args.topology == 'rtree':
        output = create_random_tree(args.count, args.intra)
    elif args.topology == 'full':
        output = create_full(args.n)
    elif args.topology == 'nodes':
        output = create_nodes(args.count)
    else:
        eprint('Unknown topology: {}'.format(args.topology))
        exit(1)

    for link in output['links']:
        if args.source_tc:
            link['source_tc'] = args.source_tc
        if args.target_tc:
            link['target_tc'] = args.target_tc

    if args.no_nodes:
        del output['nodes']

    if args.no_links:
        del output['links']

    if args.formatted:
        json.dump(output, sys.stdout, indent='  ')
    else:
        json.dump(output, sys.stdout)
