#!/usr/bin/env python3

import time
import json
import sys
import os
import re
import glob

verbose = True
test_uplink = "uplink"

def exec(cmd):
    rc = os.system(cmd)
    if rc != 0:
        print('Abort, command failed: {}'.format(cmd))
        #todo: kill routing programs!
        #print('Cleanup done')
        exit(1)

def get_addr(nsname, interface):
    output = os.popen('ip netns exec "{}" ip -6 addr list dev {}'.format(nsname, interface)).read()
    for line in output.split("\n"):
        if "inet6 fe80" in line:
            addr = line.split()[1].split("/")[0]
            if addr.startswith('fe80'):
                return addr
    return None

class PingStatistics:
    def __init__(self, nssource, nstarget, interface, packets, wait):
        self.nssource = nssource
        self.nstarget = nstarget

        nstarget_addr = get_addr(nstarget, interface)
        if nstarget_addr is not None:
            output = os.popen('ip netns exec "{}" ping -c {} -W {} -D -I {} {} '.format(nssource, packets, wait, interface, nstarget_addr)).read()
            #print(output)
            lines = output.split('\n')
            #print("lines: {}".format(len(lines)))
            #print("line: {}".format(lines[len(lines) - 3]))
            toks = re.split("[/ =,a-z%]+", lines[len(lines) - 3])
            #print("toks: {}".format(toks))
            self.packet_loss = int(toks[2])
            self.time = int(toks[3])
            #print("{} -> {}: packet_loss: {}".format(self.nssource, self.nstarget, self.packet_loss))
            
            '''
            toks = re.split("[/ =a-z]+", lines[len(lines) - 2])
            #print("line: {}".format(lines[len(lines) - 2]))
            #print("toks: {}".format(toks))
            self.min = float(toks[1])
            self.avg = float(toks[2])
            self.max = float(toks[3])
            self.mdev = float(toks[4])
            '''
        else:
            self.loss = 100
            self.time = 0
            print("Cannot get link local address of node {}".format(nsname))

class PingStatisticsSummary:
    def __init__(self):
        self.paths_tested = 0
        self.all_lost = 0
        self.all_reached = 0
        self.duration = 0

    def print(self):
        print("{} paths tested, reached: {}, lost: {} (duration: {})".format(
            self.paths_tested, self.all_reached, self.all_lost, self.duration
        ))

def get_ping_statistics(nsnames, interface, packets, wait):
    stats = []
    start_time = time.time()
    for node1 in nsnames:
        for node2 in nsnames:
            if node1 == node2:
                continue
            stats.append(PingStatistics(node1, node2, interface, packets, wait))

    summary = PingStatisticsSummary()
    summary.duration = time.time() - start_time
    summary.paths_tested = len(stats)
    for stat in stats:
        #print("{} -> {}: stat.packet_loss {}".format(stat.nssource, stat.nstarget, stat.packet_loss))
        if stat.packet_loss == 100:
            summary.all_lost += 1
        if stat.packet_loss == 0:
            summary.all_reached += 1

    return summary

class TrafficStatistics:
    def __init__(self, nsname):
        output = os.popen('ip netns exec "{}" ip -statistics link show dev uplink'.format(nsname)).read()
        self.nsname = nsname
        lines = output.split("\n")
        link_toks = lines[1].split()
        rx_toks = lines[3].split()
        tx_toks = lines[5].split()
        self.mac = link_toks[1]
        self.rx_bytes = int(rx_toks[0])
        self.rx_packets = int(rx_toks[1])
        self.tx_bytes = int(tx_toks[0])
        self.tx_packets = int(tx_toks[1])

class TrafficStatisticsSummary:
    def __init__(self):
        self.rx_bytes = 0
        self.rx_packets = 0
        self.tx_bytes = 0
        self.tx_packets = 0

    def print(self):
        print('packets: {}/{}, traffic: {}/{} (duration: {})'.format(
            self.rx_packets, self.tx_packets,
            format_bytes(self.rx_bytes), format_bytes(self.tx_bytes),
            self.duration
        ))

def format_bytes(size):
    power = 1000
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T', 5: 'E'}
    while size > power:
        size /= power
        n += 1
    return '{:.2f} {}B'.format(size, power_labels[n])

def get_traffic_statistics(nsnames):
    stats = []
    start_time = time.time()

    # fetch uplink statistics
    for nsname in nsnames:
        stats.append(TrafficStatistics(nsname))

    # sum all up
    summary = TrafficStatisticsSummary()
    summary.duration = time.time() - start_time
    for stat in stats:
        summary.rx_bytes += stat.rx_bytes
        summary.rx_packets += stat.rx_packets
        summary.tx_bytes += stat.tx_bytes
        summary.tx_packets += stat.tx_packets

    return summary

def start_none_instances(nsnames):
    pass

def stop_none_instances(nsnames):
    pass

def start_yggdrasil_instances():
    print("start yggdrasil")
    for name in nodes:
        nsname = 'ns-{}'.format(name)
        if verbose:
            print("  start yggdrasil on {}".format(nsname))

        exec('sudo ip netns exec "{}" sh -c \'echo "{{AdminListen: none}}" | yggdrasil -useconf &\''.format(nsname))

def stop_yggdrasil_instances():
    print("stop yggdrasil")
    for name in nodes:
        nsname = 'ns-{}'.format(name)
        if verbose:
            print("  stop yggdrasil on {}".format(nsname))

        exec('sudo ip netns exec "{}" pkill yggdrasil'.format(nsname))

def start_batmanadv_instances(nsnames):
    print("start batman-adv")
    for nsname in nsnames:
        if verbose:
            print('  start batman-adv on {}'.format(nsname))

        exec('ip netns exec "{}" batctl meshif "bat0" interface add "uplink"'.format(nsname))
        exec('ip netns exec "{}" ip link set "bat0" up'.format(nsname))

def stop_batmanadv_instances(nsnames):
    print("stop batman-adv")
    for nsname in nsnames:
        if verbose:
            print("  stop batman-adv on {}".format(nsname))

        exec('ip netns exec "{}" batctl meshif "bat0" interface del "uplink"'.format(nsname))

def start_babel_instances(nsnames):
    print("start babel")
    for nsname in nsnames:
        if verbose:
            print("  start babel on {}".format(nsname))

        exec('mkdir -p /var/run/babel')
        exec('ip netns exec "{}" babeld -D -I /var/run/babel/{}.pid "uplink"'.format(nsname, nsname))

def stop_babel_instances(nsnames):
    print("start babel")
    for nsname in nsnames:
        if verbose:
            print("  stop babel on {}".format(nsname))

        exec('rm -f /var/run/babel')
        exec('ip netns exec "{}" pkill babeld'.format(nsname, nsname))

def start_routing_protocol(protocol):
    if protocol == "batman-adv":
        start_batmanadv_instances(nsnames)
        uplink="bat0"
    elif protocol == "yggdrasil":
        start_yggdrasil_instances(nsnames)
    elif protocol == "babel":
        start_babel_instances(nsnames)
    elif protocol == "none":
        start_none_instances(nsnames)
    else:
        print('Error: unknown routing protocol: {}'.format(protocol))
        exit(1)

def stop_routing_protocol(protocol):
    if protocol == "batman-adv":
        stop_batmanadv_instances(nsnames)
    elif protocol == "yggdrasil":
        stop_yggdrasil_instances(nsnames)
    elif protocol == "babel":
        stop_babel_instances(nsnames)
    elif protocol == "none":
        stop_none_instances(nsnames)
    else:
        print('Error: unknown routing protocol: {}'.format(protocol))
        exit(1)

if os.popen('id -u').read().strip() != "0":
    print("Need to run as root.")
    exit(1)

if len(sys.argv) != 2:
    print("Usage: {} <routing-protocol>".format(sys.argv[0]))
    exit(1)

# get all nodes network name spaces
nsnames = [x for x in os.popen('ip netns list').read().split() if x.startswith('ns-')]

start_time = time.time()
print('Time to start {}: {}'.format(sys.argv[1], time.time() - start_time))

# The actual tests...
start_routing_protocol(sys.argv[1])

#print('Now: {}'.format(time.strftime("%Y-%m-%d %H:%M")))
#time.sleep(10)

print("get traffic statistics")
ts = get_traffic_statistics(nsnames)
ts.print()

print("ping all node pairs")
ps = get_ping_statistics(nsnames, test_uplink, 3, 1)
ps.print()

print("get traffic statistics")
ts = get_traffic_statistics(nsnames)
ts.print()

#time.sleep(10)
stop_routing_protocol(sys.argv[1])

print('done')
