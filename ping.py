#!/usr/bin/env python3

import random
import datetime
import argparse
import math
import time
import sys
import os
import re

import shared
from shared import (
    eprint, create_process, exec, get_remote_mapping, millis,
    default_remotes, convert_to_neighbors, stop_all_terminals,
    format_size, Remote
)

'''
Dijkstra shortest path algorithm
'''
class Dijkstra:
    def __init__(self, network):
        self.dists_cache = {}
        self.prevs_cache = {}
        self.nodes = convert_to_neighbors(network)

    def find_shortest_distance(self, source, target):
        source = str(source)
        target = str(target)

        # try cache
        dists = self.dists_cache.get(source)
        if dists is not None:
            return dists[target]

        # calculate
        self._calculate_shortest_paths(source)

        # try again
        dists = self.dists_cache.get(source)
        if dists is not None:
            return dists[target]

        # should not happen...
        return None

    def get_shortest_path(self, source, target):
        source = str(source)
        target = str(target)

        # calculate
        self._calculate_shortest_paths(source)

        prevs = self.prevs_cache.get(source)
        if prevs is None:
            return None

        path = []
        next = target

        while True:
            prev = prevs[next]
            if prev is not None:
                next = prev
                path.append(next)
            else:
                break

        return path

    '''
    Calculate shortest path from source to every other node
    '''
    def _calculate_shortest_paths(self, initial):
        initial = str(initial)

        dists = {}
        prevs = {}
        q = {}

        for id in self.nodes:
            dists[id] = math.inf
            prevs[id] = None
            q[id] = None

        dists[initial] = 0

        def get_smallest(q, dists):
            dist = math.inf
            idx = None

            for k in q:
                d = dists[k]
                if d < dist:
                    idx = k
                    dist = d
            return idx

        for _ in range(len(self.nodes)):
            u = get_smallest(q, dists)
            if u is None:
                break
            del q[u]
            for v in self.nodes[u]:
                if v in q:
                    # distance update
                    alt = dists[u] + 1
                    if alt < dists[v]:
                        dists[v] = alt
                        prevs[v] = u

        self.dists_cache[initial] = dists
        self.prevs_cache[initial] = prevs

def _get_clusters_sets(neighbors):
    visited = {}

    for node in neighbors:
        visited[node] = False

    def dfs(node, cluster):
        visited[node] = True
        cluster.add(node)
        for neighbor in neighbors[node]:
            if not visited[neighbor]:
                dfs(neighbor, cluster)

    clusters = []
    for node in visited:
        if not visited[node]:
            cluster = set()
            dfs(node, cluster)
            clusters.append(cluster)

    sorted(clusters, key=lambda cluster: len(cluster))
    return clusters

def filter_paths(network, paths, min_hops=None, max_hops=None, path_count=None):
    dijkstra = Dijkstra(network)

    if min_hops is None:
        min_hops = 1

    if max_hops is None:
        max_hops = math.inf

    filtered = []
    for path in paths:
        d = dijkstra.find_shortest_distance(path[0], path[1])
        if d >= min_hops and d <= max_hops and d != math.inf:
            filtered.append(path)

    if path_count is not None:
        if len(filtered) < path_count:
            eprint(f'Only {len(filtered)} paths left after filtering. Required were at least {path_count}.')
            exit(1)

        if len(filtered) > path_count:
            filtered = filtered[:path_count]

    return filtered

'''
Get list of random unique pairs (no self references, no different directions)
'''
def _get_random_paths(nodes, count=10, seed=None):
    if count > (len(nodes) * (len(nodes) - 1) // 2):
        eprint(f'Not enough nodes to generate {count} unique paths.')
        stop_all_terminals()
        exit(1)

    if seed is not None:
        random.seed(seed)

    def decode(items, i):
        k = math.floor((1 + math.sqrt(1 + 8 * i)) / 2)
        return (items[k], items[i - k * (k - 1) // 2])

    def rand_pair(n):
        return decode(random.randrange(n * (n - 1) // 2))

    def rand_pairs(items, npairs):
        n = len(items)
        return [decode(items, i) for i in random.sample(range(n * (n - 1) // 2), npairs)]

    return rand_pairs(nodes, count)

# get random node pairs (unique, no self, no reverses)
def get_random_paths(network=None, count=10, seed=None):
    nodes = list(convert_to_neighbors(network).keys())
    return _get_random_paths(nodes=nodes, count=count, seed=seed)

def get_random_nodes(network, count):
    nodes = list(convert_to_neighbors(network).keys())
    return random.sample(nodes, count)

# get all paths to neares gateways
def get_paths_to_gateways(network, gateways):
    nodes = list(convert_to_neighbors(network).keys())

    dijkstra = Dijkstra(network)

    paths = []

    # remove gateways from nodes list
    for gateway in gateways:
        nodes.remove(gateway)

    for node in nodes:
        distance_min = math.inf
        gateway_min = None
        for gateway in gateways:
            d = dijkstra.find_shortest_distance(gateway, node)
            if distance_min == math.inf or d <= distance_min:
                distance_min = d
                gateway_min = gateway

        if gateway_min is not None:
            paths.append((node, gateway))

    return paths

'''
Return an IP address of the interface in this preference order:
1. IPv4 not link local
2. IPv6 not link local
3. IPv6 link local
4. IPv4 link local
'''
def _get_ip_address(remote, id, interface, address_type=None):
    lladdr6 = None
    lladdr4 = None
    addr6 = None
    addr4 = None

    stdout, stderr, rcode = exec(remote, f'ip netns exec "ns-{id}" ip addr list dev {interface}', get_output=True)
    lines = stdout.split('\n')

    for line in lines:
        if 'inet ' in line:
            addr4 = line.split()[1].split('/')[0]
            if addr4.startswith('169.254.'):
                lladdr4 = addr4
            else:
                break

    for line in lines:
        if 'inet6 ' in line:
            addr6 = line.split()[1].split('/')[0]
            if addr6.startswith('fe80:'):
                lladdr6 = addr6
            else:
                break

    if address_type is None:
        if addr4 is not None:
            return addr4

        if addr6 is not None:
            return addr6

        if lladdr6 is not None:
            return lladdr6
        else:
            return lladdr4

    if address_type == '4':
        if addr4 is not None:
            return addr4
        else:
            return lladdr4

    if address_type == '6':
        if addr6 is not None:
            return addr6
        else:
            return lladdr6

    return None

class _PingResult:
    send = 0
    transmitted = 0
    received = 0
    rtt_min = 0.0
    rtt_max = 0.0
    rtt_avg = 0.0

    def getData(self):
        titles = ['packets_send', 'packets_received', 'rtt_avg_ms']
        values = [self.send, self.received, self.rtt_avg]
        return (titles, values)

_numbers_re = re.compile('[^0-9.]+')

def _parse_ping(output):
    ret = _PingResult()
    for line in output.split('\n'):
        if 'packets transmitted' in line:
            toks = _numbers_re.split(line)
            ret.transmitted = int(toks[0])
            ret.received = int(toks[1])
        if line.startswith('rtt min/avg/max/mdev'):
            toks = _numbers_re.split(line)
            ret.rtt_min = float(toks[1])
            ret.rtt_avg = float(toks[2])
            ret.rtt_max = float(toks[3])
            #ret.rtt_mdev = float(toks[4])

    return ret

def _get_interface(remote, source):
    # some protocols use their own interface as entry point to the mesh
    for interface in ['tun0', 'bat0']:
        rcode = exec(remote, f'ip netns exec ns-{source} ip addr list dev {interface}', get_output=True, ignore_error=True)[2]
        if rcode == 0:
            return interface
    return 'uplink'

def ping(paths, duration_ms=1000, remotes=default_remotes, interface=None, verbosity='normal', address_type=None):
    ping_deadline=1
    ping_count=1
    processes = []
    start_ms = millis()
    started = 0
    rmap = get_remote_mapping(remotes)
    path_count = len(paths)
    while started < path_count:
        # number of expected tests to have been run
        started_expected = math.ceil(path_count * ((millis() - start_ms) / duration_ms))
        if started_expected > started:
            for _ in range(0, started_expected - started):
                if len(paths) == 0:
                    break
                (source, target) = paths.pop()

                source_remote = rmap[source]
                target_remote = rmap[target]

                if interface is None:
                    interface = _get_interface(source_remote, source)

                target_addr = _get_ip_address(target_remote, target, interface, address_type)

                if target_addr is None:
                    eprint(f'Cannot get address of {interface} in ns-{target}')
                    # count as started
                    started += 1
                else:
                    debug = '[{:06}] Ping {} => {} ({} / {})'.format(millis() - start_ms, source, target, target_addr, interface)
                    process = create_process(source_remote, f'ip netns exec ns-{source} ping -c {ping_count} -w {ping_deadline} -D -I {interface} {target_addr}')
                    processes.append((process, debug))
                    started += 1
        else:
            # sleep a small amount
            time.sleep(duration_ms / path_count / 1000.0 / 10.0)

    stop1_ms = millis()

    # wait until duration_ms is over
    if (stop1_ms - start_ms) < duration_ms:
        time.sleep((duration_ms - (stop1_ms - start_ms)) / 1000.0)

    stop2_ms = millis()

    ret = _PingResult()

    # wait/collect for results from pings (prolongs testing up to 1 second!)
    for (process, debug) in processes:
        process.wait()
        (output, err) = process.communicate()
        result = _parse_ping(output.decode())
        result.send = ping_count # TODO: nicer

        ret.send += result.send
        ret.transmitted += result.transmitted
        ret.received += result.received
        ret.rtt_avg += result.rtt_avg

        if verbosity != 'quiet':
            if result.send != result.received:
                print(f'{debug} => failed')
            else:
                # success
                print(f'{debug}')

    ret.rtt_avg = 0 if ret.received == 0 else int(ret.rtt_avg / ret.received)
    result_duration_ms = stop1_ms - start_ms
    result_filler_ms = stop2_ms - stop1_ms

    if verbosity != 'quiet':
        print('send: {}, received: {}, arrived: {}%, measurement span: {}ms'.format(
            ret.send,
            ret.received,
            '-' if (ret.send == 0) else '{:0.2f}'.format(100.0 * (ret.received / ret.send)),
            result_duration_ms + result_filler_ms
        ))

    return ret

def check_access(remotes):
    shared.check_access(remotes)

def main():
    parser = argparse.ArgumentParser(description='Ping various nodes.')
    parser.add_argument('--remotes', help='Distribute nodes and links on remotes described in the JSON file.')
    parser.add_argument('--input', help='JSON state of the network.')
    parser.add_argument('--interface', help='Interface to send data over (autodetected).')
    parser.add_argument('--min-hops', type=int, help='Minimum hops to ping. Needs --input.')
    parser.add_argument('--max-hops', type=int, help='Maximum hops to ping. Needs --input.')
    parser.add_argument('--pings', type=int, default=10, help='Number of pings (unique, no self, no reverse paths).')
    parser.add_argument('--duration', type=int, default=1000, help='Spread pings over duration in ms.')
    parser.add_argument('-4', action='store_true', help='Force use of IPv4 addresses.')
    parser.add_argument('-6', action='store_true', help='Force use of IPv6 addresses.')

    args = parser.parse_args()

    if args.remotes:
        if not os.path.isfile(args.remotes):
            eprint(f'File not found: {args.remotes}')
            stop_all_terminals()
            exit(1)

        with open(args.remotes) as file:
            args.remotes = [Remote.from_json(obj) for obj in json.load(file)]
    else:
        args.remotes = default_remotes

    # need root for local setup
    for remote in args.remotes:
        if remote.address is None:
            if os.geteuid() != 0:
                eprint('Need to run as root.')
                exit(1)

    paths = None

    if args.input:
        state = json.load(args.input)
        paths = get_random_paths(network=state, count=args.pings)
        paths = filter_paths(state, paths, min_hops=args.min_hops, max_hops=args.max_hops)
    else:
        if args.min_hops is not None or args.max_hops is not None:
            eprint('No min/max hops available without topology information (--input)')
            stop_all_terminals()
            exit(1)

        rmap = get_remote_mapping(args.remotes)
        all = list(rmap.keys())
        paths = _get_random_paths(nodes=all, count=args.pings)

    address_type = None
    if getattr(args, '4'):
        address_type = '4'
    if getattr(args, '6'):
        address_type = '6'

    ping(paths=paths, remotes=args.remotes, duration_ms=args.duration, interface=args.interface, verbosity='verbose', address_type=address_type)

    stop_all_terminals()

if __name__ == "__main__":
    main()
