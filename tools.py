#!/usr/bin/env python3

import random
import datetime
import argparse
import subprocess
import json
import math
import time
import sys
import os
import re


def convert_network(network):
    nodes = {}

    # create a structure we can use efficiently
    for node in network.get('nodes', []):
        nodes.setdefault(str(node['id']), [])

    for link in network.get('links', []):
        source = str(link['source'])
        target = str(link['target'])
        nodes.setdefault(source, []).append(target)
        nodes.setdefault(target, []).append(source)

    return nodes

class Dijkstra:
    def __init__(self, network):
        self.dists_cache = {}
        self.prevs_cache = {}
        self.nodes = convert_network(network)

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

def get_valid_path_count(network, paths = []):
    dijkstra = Dijkstra(network)
    count = 0

    for path in paths:
        d = dijkstra.find_shortest_distance(path[0], path[1])
        if d is not None:
            count +=1

    return count

def eprint(s):
    sys.stderr.write(s + '\n')

def root():
    if os.geteuid() != 0:
        eprint('Need to run as root.')
        exit(1)

def seed_random(seed):
    random.seed(seed)

def sleep(seconds):
    time.sleep(seconds)

def wait(beg_ms, until_sec):
    now_ms = millis()

    # wait until time is over
    if (now_ms - beg_ms) < (until_sec * 1000):
        time.sleep(((until_sec * 1000) - (now_ms - beg_ms)) / 1000.0)
    else:
        eprint('Wait timeout already passed by {:.2f}sec'.format(((now_ms - beg_ms) - (until_sec * 1000)) / 1000))
        exit(1)

def json_count(path):
    obj = json.load(open(path))
    links = obj.get('links', [])
    nodes = {}
    for link in links:
        nodes[link['source']] = 0;
        nodes[link['target']] = 0;
    links = obj.get('links', [])
    return (len(nodes), len(links))

def sysload():
    p = subprocess.Popen(['uptime'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out, err) = p.communicate()
    t = out.decode().split('load average:')[1].split(',')
    load1 = t[0].strip()
    load5 = t[1].strip()
    load15 = t[2].strip()

    titles = ['load1', 'load5', 'load15']
    values = [load1, load5, load15]

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

def traffic(nsnames=None):
    if nsnames is None:
        nsnames = [x for x in os.popen('ip netns list').read().split() if x.startswith('ns-')]

    ts = _Traffic()

    for nsname in nsnames:
        command = ['ip', 'netns', 'exec', nsname , 'ip', '-statistics', 'link', 'show', 'dev', 'uplink']
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (output, err) = process.communicate()
        lines = output.decode().split('\n')
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

# get time in milliseconds
def millis():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

# get random node pairs (not unique, not path to self)
def get_random_paths(network=None, count=10):
    if network is None:
        # all ns-* network namespaces
        nodes = [x[3:] for x in os.popen('ip netns list').read().split() if x.startswith('ns-')]
    else:
        nodes = list(convert_network(network).keys())

    if len(nodes) < 2 and count > 0:
        eprint('Not enough nodes to get any pairs!')
        exit(1)

    pairs = []
    while len(pairs) < count:
        e1 = random.choice(nodes)
        e2 = random.choice(nodes)
        if e1 == e2:
            continue

        pairs.append((e1, e2))

    return pairs

'''
Return an IP address of the interface in this preference order:
1. IPv4 not link local
2. IPv6 not link local
3. IPv6 link local
4. IPv4 link local
'''
def _get_ip_address(id, interface):
    lladdr6 = None
    lladdr4 = None
    output = os.popen('ip netns exec "ns-{}" ip addr list dev {}'.format(id, interface)).read()
    for line in output.split('\n'):
        if 'inet ' in line:
            addr4 = line.split()[1].split('/')[0]
            if addr4.startswith('169.254.'):
                lladdr4 = addr4
            else:
                return addr4
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
    transmitted = 0
    received = 0
    rtt_min = 0.0
    rtt_max = 0.0
    rtt_avg = 0.0

    def __init__(self, transmitted = 0, received = 0, rtt_min = 0.0, rtt_max = 0.0, rtt_avg = 0.0):
        self.transmitted = transmitted
        self.received = received
        self.rtt_min = rtt_min
        self.rtt_max = rtt_max
        self.rtt_avg = rtt_avg

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

def ping(protocol, count=10, duration_ms=1000, verbosity='normal'):
    paths = get_random_paths(network=None, count=count)
    return ping_paths(protocol, paths, duration_ms, verbosity)

def ping_paths(protocol, paths, duration_ms=1000, verbosity='normal'):
    def get_uplink(protocol):
        # some protocols use their own interface as entry point to the mesh
        if protocol == 'batman-adv':
            return 'bat0'
        elif protocol == 'yggdrasil':
            return 'tun0'
        elif protocol == 'cjdns':
            return 'tun0'
        else:
            return 'uplink'

    interface = get_uplink(protocol)
    ping_deadline=1
    ping_count=1
    processes = []

    start_ms = millis()
    started = 0
    path_count = len(paths)
    while started < path_count:
        # number of expected tests to have been run
        started_expected = math.ceil(path_count * ((millis() - start_ms) / duration_ms))
        if started_expected > started:
            for _ in range(0, started_expected - started):
                if len(paths) == 0:
                    break
                (source, target) = paths.pop()
                target_addr = _get_ip_address(target, interface)

                if target_addr is None:
                    eprint('Cannot get address of {} in ns-{}'.format(interface, target))
                    # count as started
                    started += 1
                else:
                    if verbosity == 'verbose':
                        print('[{:06}] Ping {} => {} ({} / {})'.format(millis() - start_ms, source, target, target_addr, interface))

                    command = ['ip', 'netns', 'exec', f'ns-{source}' ,'ping', '-c', f'{ping_count}', '-w', f'{ping_deadline}', '-D', target_addr]
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    processes.append(process)
                    started += 1
        else:
            # sleep a small amount
            time.sleep(duration_ms / path_count / 1000.0 / 10.0)

    stop1_ms = millis()

    # wait until duration_ms is over
    if (stop1_ms - start_ms) < duration_ms:
        time.sleep((duration_ms - (stop1_ms - start_ms)) / 1000.0)

    stop2_ms = millis()

    result_packets_send = 0
    result_packets_received = 0
    result_rtt_avg = 0.0

    # wait/collect for results from pings (prolongs testing up to 1 second!)
    for process in processes:
        process.wait()
        (output, err) = process.communicate()
        result = _parse_ping(output.decode())

        result_packets_send += ping_count
        result_packets_received += result.received
        result_rtt_avg += result.rtt_avg

    result_rtt_avg_ms = 0.0 if result_packets_received == 0 else (result_rtt_avg / result_packets_received)
    result_duration_ms = stop1_ms - start_ms
    result_filler_ms = stop2_ms - stop1_ms

    if verbosity != 'quiet':
        print('{}: send: {}, received: {}, arrived: {}%, measurement span: {}ms + {}ms'.format(
            protocol,
            result_packets_send,
            result_packets_received,
            '-' if (result_packets_send == 0) else '{:0.2f}'.format(100.0 * (result_packets_received / result_packets_send)),
            result_duration_ms,
            result_filler_ms
        ))

    titles = ['packets_send', 'packets_received', 'duration_ms', 'rtt_avg_ms']
    values = [result_packets_send, result_packets_received,
        int(result_duration_ms + result_filler_ms), int(result_rtt_avg_ms)]

    return (titles, values)
