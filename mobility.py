#!/usr/bin/env python3

import random
import argparse
import bisect
import json
import math
import sys
import os


def eprint(s):
    sys.stderr.write(s + '\n')

def get_distance(source, target):
    sx = source.get('x', math.nan)
    sy = source.get('y', math.nan)
    sz = source.get('z', math.nan)
    tx = target.get('x', math.nan)
    ty = target.get('y', math.nan)
    tz = target.get('z', math.nan)

    if math.isnan(sx) and math.isnan(tx):
        sx = 0
        tx = 0
    if math.isnan(sy) and math.isnan(ty):
        sy = 0
        ty = 0
    if math.isnan(sz) and math.isnan(tz):
        sz = 0
        tz = 0

    return math.sqrt((sx - tx) * (sx - tx) + (sy - ty) * (sy - ty) + (sz - tz) * (sz - tz))

def move_nodes(network, add_x, add_y, add_z, mul_x, mul_y, mul_z):
    for node in network.get('nodes', []):
        if 'x' in node:
            node['x'] = add_x + multiply_x * float(node['x'])
        if 'y' in node:
            node['y'] = add_y + multiply_y * float(node['y'])
        if 'z' in node:
            node['z'] = add_z + multiply_z * float(node['z'])

def connect_range(network, max_distance=None, max_links=None):
    nodes = network.get('nodes', [])
    distances = []
    links = []

    for i in range(0, len(nodes)):
        for j in range(0, i):
            d = get_distance(nodes[i], nodes[j])
            if max_distance is not None and d > max_distance:
                continue

            link = {'source': i, 'target': j}

            if max_links is None:
                links.append(link)
            else:
                k = bisect.bisect_left(distances, d)
                distances.insert(k, d)
                links.insert(k, link)

                if len(links) >= max_links:
                    # remove last item
                    del distances[-1]
                    del links[-1]

    network['links'] = links

def randomize_positions(network, xy_range=1.0):
    #randomly placed nodes with no links with coordinates [0.0, 1.0).
    for node in network['nodes']:
        # value [0,1)
        node['x'] = xy_range * random.random()
        node['y'] = xy_range * random.random()

def move_random(network, distance, seed=None):
    if seed is not None:
        random.seed(seed)

    for node in network.get('nodes', []):
        dx = (0.5 - random.random()) if 'x' in node else 0.0
        dy = (0.5 - random.random()) if 'y' in node else 0.0
        dz = (0.5 - random.random()) if 'z' in node else 0.0
        dlen = math.sqrt(dx * dx + dy * dy + dz * dz)
        dx = distance * dx / dlen
        dy = distance * dy / dlen
        dz = distance * dz / dlen
        if 'x' in node:
            node['x'] = dx + float(node['x'])
        if 'y' in node:
            node['y'] = dy + float(node['y'])
        if 'z' in node:
            node['z'] = dz + float(node['z'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='JSON file of the network.')
    parser.add_argument('--formatted', action='store_true', help='Output formatted json.')
    subparsers = parser.add_subparsers(dest='action', required=True)

    parser_move = subparsers.add_parser('move', help='Move all nodes.')
    parser_move.add_argument('--add-x', type=float, default=0, help='Add value to all x coordiantes.')
    parser_move.add_argument('--add-y', type=float, default=0, help='Add value to all y coordiantes.')
    parser_move.add_argument('--add-z', type=float, default=0, help='Add value to all z coordiantes.')
    parser_move.add_argument('--mul-x', type=float, default=1, help='Multiply node coordiantes in X direction.')
    parser_move.add_argument('--mul-y', type=float, default=1, help='Multiply node coordiantes in Y direction.')
    parser_move.add_argument('--mul-z', type=float, default=1, help='Multiply node coordiantes in Z direction.')

    parser_random = subparsers.add_parser('random', help='Move nodes in random directions.')
    parser_random.add_argument('--distance', type=float, default=0, help='Move this amount.')
    parser_random.add_argument('--seed', type=int, help='Seed for random generator.')

    parser_connect = subparsers.add_parser('connect', help='Connect all nodes that are in range. Removes all existing list first.')
    parser_connect.add_argument('--distance', type=float, default=1, help='Connect nodes up to this distance.')
    parser_connect.add_argument('--max-links', type=int, help='Maximum number of links to create.')

    args = parser.parse_args()

    output = json.load(open(args.input))

    if args.action == 'move':
        move_nodes(output, args.add_x, args.add_y, args.add_z, args.multiply_x, args.multiply_y, args.multiply_z)
    elif args.action == 'connect':
        connect_range(output, args.distance, args.max_links)
    elif args.action == 'random':
        move_random(output, args.distance, args.seed)
    else:
        eprint('Unknown action: {}'.format(args.action))
        exit(1)

    if args.formatted:
        json.dump(output, sys.stdout, indent='  ')
    else:
        json.dump(output, sys.stdout)
