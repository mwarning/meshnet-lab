#!/usr/bin/env python3

import random
import argparse
import json
import math
import sys
import os
import glob
import math

def eprint(message):
    sys.stderr.write(f"{message}\n")

def hex(number):
    return f"0x{number:04x}"

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
            links.append({'source': hex(a), 'target': hex(b)})

    for x in range(0, x_count):
        for y in range(0, y_count):
            nodes.append({'id': hex(x + y * x_count), 'x': x, 'y': y})
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
            nodes.append({'id': hex(i), 'x': math.sin(i * 2 * math.pi / count), 'y': math.cos(i * 2 * math.pi / count)})
        else:
            nodes.append({'id': hex(i), 'x': i, 'y': 0})

        if i > 0:
            links.append({'source': hex(i - 1), 'target': hex(i)})

    if loop and (count > 2):
        links.append({'source': hex(0), 'target': hex(count - 1)})

    return {'nodes': nodes, 'links': links}

def create_tree(depth, degree):
    nodes = []
    links = []
    i = 0
    j = 0

    for d in range(0, depth):
        for k in range(0, 0 + int(degree ** d)):
            nodes.append({'id': hex(i), 'x': k, 'y': d})
            for _ in range(0, degree):
                j += 1
                links.append({'source': hex(i), 'target': hex(j)})
            i += 1

    return {'nodes': nodes, 'links': links}

def create_random_tree(count, intra = 0):
    nodes = []
    links = {}

    # String representation of a link
    def get_id(i, j):
        if i > j:
            return f'{i}-{j}'
        else:
            return f'{j}-{i}'

    # Connect random nodes
    for i in range(1, count):
        # Connect node with random previous node
        while True:
            j = random.randint(0, i)
            id = get_id(i, j)
            if i != j and id not in links:
                nodes.append({'id': hex(i), 'x': i, 'y': j})
                links[id] = {'source': hex(i), 'target': hex(j)}
                break

    return {'nodes': nodes, 'links': list(links.values())}

def create_full(count):
    nodes = []
    links = []

    for i in range(0, count):
        nodes.append({'id': hex(i)})

    for i in range(0, count):
        for j in range(0, count):
            if i < j:
                links.append({'source': hex(i), 'target': hex(j)})

    return {'nodes': nodes, 'links': links}

def create_clusters(cluster_xy_count, cluster_xy_size):
    index_obj = {'index': 0}

    def re_index(cluster, index_obj):
        tmap = {}
        def tr(i):
            if i in tmap:
                return tmap[i]
            else:
                tmap[i] = str(index_obj['index'])
                index_obj['index'] += 1
                return tmap[i]

        for link in cluster["links"]:
            link['source'] = tr(link['source'])
            link['target'] = tr(link['target'])
        for node in cluster["nodes"]:
            node['id'] = tr(node['id'])

    def center(nodes):
        x, y = 0, 0
        for node in nodes:
            x += node['x']
            y += node['y']
        return (x / len(nodes), y / len(nodes))

    def position_at(cluster, x, y):
        count = len(cluster['nodes'])
        scale = int(math.sqrt(count))

        # center of the cluster
        center_x, center_y = center(cluster["nodes"])
        for node in cluster['nodes']:
            node['x'] = float('{:.2f}'.format(x + (node['x'] - center_x) / scale))
            node['y'] = float('{:.2f}'.format(y + (node['y'] - center_y) / scale))

    clusters = {}

    # get or create cluster
    def get_cluster(x, y):
        key = f'{x} => {y}'
        if key not in clusters:
            cluster = create_grid(cluster_xy_size, cluster_xy_size, False)
            re_index(cluster, index_obj)
            position_at(cluster, x, y)
            clusters[key] = cluster
        return clusters[key]

    def vlen(x, y):
        return math.sqrt(x ** 2 + y ** 2)

    # create link between both clusters
    def create_link(cluster1, cluster2):
        nodes1, nodes2 = cluster1['nodes'], cluster2['nodes']

        c1x, c1y = center(nodes1)
        c2x, c2y = center(nodes2)

        def nearest(x, y, nodes):
            d_node = None
            d_min = None
            for node in nodes:
                d = vlen(x - node['x'], y - node['y'])
                if d_min is None or d < d_min:
                    d_min = d
                    d_node = node
            return d_node
        n1 = nearest(c2x, c2y, nodes1)
        n2 = nearest(c1x, c1y, nodes2)
        return {'source': n1['id'], 'target': n2['id']}

    links = []
    nodes = []

    def connect(x1, y1, x2, y2):
        x_count = cluster_xy_count
        y_count = cluster_xy_count
        if (x2 < x_count) and (y2 < y_count):
            cluster1 = get_cluster(x1, y1)
            cluster2 = get_cluster(x2, y2)
            links.append(create_link(cluster1, cluster2))

    # connect clusters
    for x in range(0, cluster_xy_count):
        for y in range(0, cluster_xy_count):
            connect(x, y, x, y + 1)
            connect(x, y, x + 1, y)

    for cluster in clusters.values():
        links.extend(cluster['links'])
        nodes.extend(cluster['nodes'])

    return {'links': links, 'nodes': nodes}

def create_nodes(count):
    nodes = []

    for i in range(0, count):
        nodes.append({'id': hex(i)})

    return {'nodes': nodes, 'links': []}

def apply_offset(output, id_offset):
    def plus(id):
        if id.startswith("0x"):
            return "0x{:04x}".format(1 + int(id, 16))
        else:
            return str(int(id) + 1)

    for node in output['nodes']:
        node['id'] = plus(node['id'])

    for link in output['links']:
        link['source'] = plus(link['source'])
        link['target'] = plus(link['target'])

    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-tc', help='Value for each links source_tc.')
    parser.add_argument('--target-tc', help='Value for each links target_tc.')
    parser.add_argument('--no-nodes', action='store_true', help='Omit nodes from output.')
    parser.add_argument('--no-links', action='store_true', help='Omit links from output.')
    parser.add_argument('--formatted', action='store_true', help='Output formatted json.')
    parser.add_argument('--id-offset', type=int, help='Start node identifiers at given number (default: 0).')

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
    parser_clusters = subparsers.add_parser('clusters', help='Create a lattice of connected grids.')
    parser_clusters.add_argument('cluster_xy_count', type=int, help='Number of grids in one dimension.')
    parser_clusters.add_argument('cluster_xy_size', type=int, help='Cluster size in one dimension (it is a grid).')
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
    elif args.topology == 'clusters':
        output = create_clusters(args.cluster_xy_count, args.cluster_xy_size)
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

    if args.id_offset:
        apply_offset(output, args.id_offset)

    if args.formatted:
        json.dump(output, sys.stdout, indent='  ')
    else:
        json.dump(output, sys.stdout)
