#!/usr/bin/env python3

import random
import datetime
import argparse
import json
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

'''
Add links to network to make sure
it is fully connected.
'''
def make_connected(network):
    neighbors = convert_to_neighbors(network)
    clusters = _get_clusters_sets(neighbors)

    def get_unique_id(neighbors, i = 0):
        if f'ic-{i}' not in neighbors:
             return f'ic-{i}'
        else:
            return get_unique_id(neighbors, i + 1)

    def get_center_node(neighbors, cluster):
        max_neighbors = 0
        center_node = None
        for sid, neighs in neighbors.items():
            if sid in cluster and len(neighs) >= max_neighbors:
                max_neighbors = len(neighs)
                center_node = sid
        return center_node

    if len(clusters) > 1:
        central = get_unique_id(neighbors)

        # connect all clusters via central node
        for cluster in clusters:
            center = get_center_node(neighbors, cluster)
            network['links'].append({'source': central, 'target': center, 'type': 'vpn'})

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

def root():
    if os.geteuid() != 0:
        eprint('Need to run as root.')
        exit(1)

def load_json(path):
    with open(path) as file:
        return json.load(file)
    return None

def seed_random(value):
    random.seed(value)

def sleep(seconds):
    time.sleep(seconds)

def wait(beg_ms, until_sec):
    now_ms = millis()

    # wait until time is over
    if (now_ms - beg_ms) < (until_sec * 1000):
        time.sleep(((until_sec * 1000) - (now_ms - beg_ms)) / 1000.0)
    else:
        eprint('Wait timeout already passed by {:.2f}sec'.format(((now_ms - beg_ms) - (until_sec * 1000)) / 1000))
        stop_all_terminals()
        exit(1)

def json_count(path):
    obj = path

    if isinstance(path, str):
        with open(path) as file:
            obj = json.load(file)

    links = obj.get('links', [])
    nodes = {}
    for link in links:
        nodes[link['source']] = 0;
        nodes[link['target']] = 0;
    links = obj.get('links', [])

    return (len(nodes), len(links))

def sysload(remotes=default_remotes):
    load1 = 0
    load5 = 0
    load15 = 0

    for remote in remotes:
        stdout = exec(remote, 'uptime', get_output=True)[0]
        t = stdout.split('load average:')[1].split(',')
        load1 += float(t[0])
        load5 += float(t[1])
        load15 += float(t[2])

    titles = ['load1', 'load5', 'load15']
    values = [load1 / len(remotes), load5 / len(remotes), load15 / len(remotes)]

    return (titles, values)

class _Traffic:
    def __init__(self):
        self.rx_bytes = 0
        self.rx_packets = 0
        self.rx_errors = 0
        self.rx_dropped = 0
        self.rx_overrun = 0
        self.rx_mcast = 0
        self.tx_bytes = 0
        self.tx_packets = 0
        self.tx_errors = 0
        self.tx_dropped = 0
        self.tx_carrier = 0
        self.tx_collsns = 0

    def getData(self):
        titles = ['rx_bytes', 'rx_packets', 'rx_errors', 'rx_dropped',
            'rx_overrun', 'rx_mcast', 'tx_bytes', 'tx_packets',
            'tx_errors', 'tx_dropped', 'tx_carrier', 'tx_collsns'
        ]

        values = [self.rx_bytes, self.rx_packets, self.rx_errors, self.rx_dropped,
            self.rx_overrun, self.rx_mcast, self.tx_bytes, self.tx_packets,
            self.tx_errors, self.tx_dropped, self.tx_carrier, self.tx_collsns
        ]

        return (titles, values)

    def __sub__(self, other):
        ts = _Traffic()
        ts.rx_bytes = self.rx_bytes - other.rx_bytes
        ts.rx_packets = self.rx_packets - other.rx_packets
        ts.rx_errors = self.rx_errors - other.rx_errors
        ts.rx_dropped = self.rx_dropped - other.rx_dropped
        ts.rx_overrun = self.rx_overrun - other.rx_overrun
        ts.rx_mcast = self.rx_mcast - other.rx_mcast
        ts.tx_bytes = self.tx_bytes - other.tx_bytes
        ts.tx_packets = self.tx_packets - other.tx_packets
        ts.tx_errors = self.tx_errors - other.tx_errors
        ts.tx_dropped = self.tx_dropped - other.tx_dropped
        ts.tx_carrier = self.tx_carrier - other.tx_carrier
        ts.tx_collsns = self.tx_collsns - other.tx_collsns
        return ts

def traffic(remotes=default_remotes, ids=None, interface=None, rmap=None):
    if rmap is None:
        rmap = get_remote_mapping(remotes)

    if ids is None:
        ids = list(rmap.keys())

    if interface is None:
        interface = 'uplink'

    ts = _Traffic()

    for id in ids:
        remote = rmap[id]
        stdout = exec(remote, f'ip netns exec ns-{id} ip -statistics link show dev {interface}', get_output=True)[0]
        lines = stdout.split('\n')
        link_toks = lines[1].split()
        rx_toks = lines[3].split()
        tx_toks = lines[5].split()
        ts.rx_bytes += int(rx_toks[0])
        ts.rx_packets += int(rx_toks[1])
        ts.rx_errors += int(rx_toks[2])
        ts.rx_dropped += int(rx_toks[3])
        ts.rx_overrun += int(rx_toks[4])
        ts.rx_mcast += int(rx_toks[5])
        ts.tx_bytes += int(tx_toks[0])
        ts.tx_packets += int(tx_toks[1])
        ts.tx_errors += int(tx_toks[2])
        ts.tx_dropped += int(tx_toks[3])
        ts.tx_carrier += int(tx_toks[4])
        ts.tx_collsns += int(tx_toks[5])

    return ts

# add titles and values to a CSV file
def csv_update(file, delimiter, *args):
    titles = list()
    values = list()

    for arg in args:
        titles += arg[0]
        values += arg[1]

    # convert elements to str
    for i in range(0, len(titles)):
        titles[i] = str(titles[i])

    # convert elements to str
    for i in range(0, len(values)):
        values[i] = str(values[i])

    if file.tell() == 0:
        file.write(delimiter.join(titles) + '\n')

    file.write(delimiter.join(values) + '\n')

'''
Get list of random unique pairs (no self references, no different directions)
'''
def _get_random_paths(nodes, count=10, seed=None):
    if count > (len(nodes) * (len(nodes) - 1) // 2):
        eprint(f'Path count ({count}) too big to generate unique paths.')
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

'''
Return an IP address of the interface in this preference order:
1. IPv4 not link local
2. IPv6 not link local
3. IPv6 link local
4. IPv4 link local
'''
def _get_ip_address(remote, id, interface):
    lladdr6 = None
    lladdr4 = None

    stdout, stderr, rcode = exec(remote, f'ip netns exec "ns-{id}" ip addr list dev {interface}', get_output=True)
    lines = stdout.split('\n')

    for line in lines:
        if 'inet ' in line:
            addr4 = line.split()[1].split('/')[0]
            if addr4.startswith('169.254.'):
                lladdr4 = addr4
            else:
                return addr4

    for line in lines:
        if 'inet6 ' in line:
            addr6 = line.split()[1].split('/')[0]
            if addr6.startswith('fe80:'):
                lladdr6 = addr6
            else:
                return addr6

    if lladdr6 is not None:
        return lladdr6
    else:
        return lladdr4

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

def ping_paths(paths, duration_ms=1000, remotes=default_remotes, interface=None, verbosity='normal'):
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

                target_addr = _get_ip_address(target_remote, target, interface)

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
    parser = argparse.ArgumentParser()
    parser.add_argument('--remotes', help='Distribute nodes and links on remotes described in the JSON file.')
    subparsers = parser.add_subparsers(dest='action', required=True)

    parser_traffic = subparsers.add_parser('traffic', help='Measure mean traffic.')
    parser_traffic.add_argument('--interface', help='Interface to measure traffic on.')
    parser_traffic.add_argument('--duration', type=int, help='Measurement duration in seconds.')

    parser_ping = subparsers.add_parser('ping', help='Ping various nodes.')
    parser_ping.add_argument('--input', help='JSON state of the network.')
    parser_ping.add_argument('--interface', help='Interface to send data over (autodetected).')
    parser_ping.add_argument('--min-hops', type=int, help='Minimum hops to ping. Needs --input.')
    parser_ping.add_argument('--max-hops', type=int, help='Maximum hops to ping. Needs --input.')
    parser_ping.add_argument('--pings', type=int, default=10, help='Number of pings (unique, no self, no reverse paths).')
    parser_ping.add_argument('--duration', type=int, default=1000, help='Spread pings over duration in ms.')

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

    if args.action == 'traffic':
        rmap = get_remote_mapping(args.remotes)
        if args.duration:
            ds = args.duration
            ts_beg = traffic(args.remotes, interface=args.interface, rmap=rmap)
            time.sleep(ds)
            ts_end = traffic(args.remotes, interface=args.interface, rmap=rmap)
            ts = ts_end - ts_beg
            n = ds * len(rmap)
            print(f'rx: {format_size(ts.rx_bytes / n)}/s, {ts.rx_packets / n:.2f} packets/s, {ts.rx_dropped / n:.2f} dropped/s (avg. per node)')
            print(f'tx: {format_size(ts.tx_bytes / n)}/s, {ts.tx_packets / n:.2f} packets/s, {ts.tx_dropped / n:.2f} dropped/s (avg. per node)')
        else:
            ts = traffic(args.remotes, interface=args.interface, rmap=rmap)
            print(f'rx: {format_size(ts.rx_bytes)} / {ts.rx_packets} packets / {ts.rx_dropped} dropped')
            print(f'tx: {format_size(ts.tx_bytes)} / {ts.tx_packets} packets / {ts.tx_dropped} dropped')
    elif args.action == 'ping':
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

        ping_paths(paths=paths, remotes=args.remotes, duration_ms=args.duration, interface=args.interface, verbosity='verbose')
    else:
        eprint(f'Unknown action: {args.action}')
        exit(1)

    stop_all_terminals()

if __name__ == "__main__":
    main()
