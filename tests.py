#!/usr/bin/env python3

import random
import datetime
import argparse
import time
import sys
import os
import re


def exec(cmd, detach=False):
    rc = 0

    if args.verbosity == 'verbose':
        if detach:
            rc = os.system("{} &".format(cmd))
        else:
            rc = os.system("{}".format(cmd))
    elif args.verbosity == 'normal':
        if detach:
            rc = os.system('{} > /dev/null &'.format(cmd))
        else:
            rc = os.system('{} > /dev/null'.format(cmd))
    elif args.verbosity == 'quiet':
        if detach:
            rc = os.system('{} > /dev/null 2>&1 &'.format(cmd))
        else:
            rc = os.system('{} > /dev/null 2>&1'.format(cmd))
    else:
        print('Abort, invalid verbosity: {}'.format(args.verbosity))
        exit(1)

    if rc != 0:
        print('Abort, command failed: {}'.format(cmd))
        #todo: kill routing programs!
        #print('Cleanup done')
        exit(1)

def now():
    return datetime.datetime.now()

def get_random_samples(items, npairs):
    samples = {}
    i = 0

    while i < (npairs * 4) and len(samples) != npairs:
        i += 1
        e1 = random.choice(items)
        e2 = random.choice(items)
        if e1 == e2:
            continue
        key = "{}-{}".format(e1, e2)
        if key not in samples:
            samples[key] = (e1, e2)

    return samples.values()

# get IPv6 address, use fe80:: address as fallback
def get_addr(nsname, interface):
    lladdr = None
    output = os.popen('ip netns exec "{}" ip -6 addr list dev {}'.format(nsname, interface)).read()
    for line in output.split("\n"):
        if 'inet6 ' in line:
            addr = line.split()[1].split("/")[0]
            if addr.startswith('fe80'):
                lladdr = addr
            else:
                return addr

    return None

class PingStatistics:
    def __init__(self, nssource, nstarget, interface, packets, wait):
        self.nssource = nssource
        self.nstarget = nstarget

        nstarget_addr = get_addr(nstarget, interface)
        if nstarget_addr is not None:
            if args.verbosity == 'verbose':
                print('Ping {} => {} ({} / {})'.format(nssource, nstarget, nstarget_addr, interface))

            # perform the ping!
            output = os.popen('ip netns exec "{}" ping -c {} -W {} -D {} '.format(nssource, packets, wait, nstarget_addr)).read()
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
            self.packet_loss = 100
            self.time = 0
            print("{}: Cannot get link local address of interface {}".format(nstarget, interface))

class PingStatisticsSummary:
    def __init__(self):
        self.paths_tested = 0
        self.lost = 0
        self.reached = 0
        self.duration = 0

    def print(self):
        print("{} paths tested, reached: {}, lost: {} (duration: {})".format(
            self.paths_tested, self.reached, self.lost, self.duration
        ))

def get_ping_statistics(pairs, interface):
    packets = 1
    wait = 1
    stats = []
    start_time = now()

    for (node1, node2) in pairs:
        stats.append(PingStatistics(node1, node2, interface, packets, wait))

    summary = PingStatisticsSummary()
    summary.duration = now() - start_time
    summary.paths_tested = len(stats)
    for stat in stats:
        if stat.packet_loss == 100:
            summary.lost += 1
        if stat.packet_loss == 0:
            summary.reached += 1

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
        print('received {} ({} bytes, {} packets), send: {} ({} bytes, {} packets)'.format(
            format_bytes(self.rx_bytes), self.rx_bytes, self.rx_packets,
            format_bytes(self.tx_bytes), self.tx_bytes, self.tx_packets
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
    start_time = now()

    # fetch uplink statistics
    for nsname in nsnames:
        stats.append(TrafficStatistics(nsname))

    # sum all up
    summary = TrafficStatisticsSummary()
    summary.duration = now() - start_time
    for stat in stats:
        summary.rx_bytes += stat.rx_bytes
        summary.rx_packets += stat.rx_packets
        summary.tx_bytes += stat.tx_bytes
        summary.tx_packets += stat.tx_packets

    return summary

def start_none_instances(nsnames):
    # nothing to do
    pass

def stop_none_instances(nsnames):
    # nothing to do
    pass

def start_yggdrasil_instances(nsnames):
    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print("  start yggdrasil on {}".format(nsname))

        # Create a configuration file
        configfile = "/tmp/yggdrasil-{}.conf".format(nsname)
        f = open(configfile, "w")
        f.write("AdminListen: none")
        f.close()

        exec('ip netns exec "{}" yggdrasil -useconffile {}'.format(nsname, configfile), True)

def stop_yggdrasil_instances(nsnames):
    if args.verbosity == 'verbose':
       print("  stop yggdrasil in all namespaces")

    if len(nsnames) > 0:
        exec('pkill yggdrasil')

def start_batmanadv_instances(nsnames):
    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print('  start batman-adv on {}'.format(nsname))

        exec('ip netns exec "{}" batctl meshif "bat0" interface add "uplink"'.format(nsname))
        exec('ip netns exec "{}" ip link set "bat0" up'.format(nsname))

def stop_batmanadv_instances(nsnames):
    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print("  stop batman-adv on {}".format(nsname))

        exec('ip netns exec "{}" batctl meshif "bat0" interface del "uplink"'.format(nsname))

def start_babel_instances(nsnames):
    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print("  start babel on {}".format(nsname))

        exec('mkdir -p /var/run/babel')
        exec('ip netns exec "{}" babeld -D -I /var/run/babel/{}.pid "uplink"'.format(nsname, nsname))

def stop_babel_instances(nsnames):
    if args.verbosity == 'verbose':
        print("  stop babel in all namespaces")

    if len(nsnames) > 0:
        exec('rm -f /var/run/babel')
        exec('pkill babeld')

def start_olsr_instances(nsnames):
    for nsname in nsnames:
        if verbose:
            print("  start olsr on {}".format(nsname))

        exec('ip netns exec "{}" olsrd -d 0 "uplink"'.format(nsname))

def stop_olsr_instances(nsnames):
    if args.verbosity == 'verbose':
        print("  stop olsr in all namespaces")

    if len(nsnames) > 0:
        exec('pkill olsrd')

def start_routing_protocol(protocol, nsnames):
    if protocol == "batman-adv":
        start_batmanadv_instances(nsnames)
    elif protocol == "yggdrasil":
        start_yggdrasil_instances(nsnames)
    elif protocol == "babel":
        start_babel_instances(nsnames)
    elif protocol == "olsr":
        start_olsr_instances(nsnames)
    elif protocol == "none":
        start_none_instances(nsnames)
    else:
        print('Error: unknown routing protocol: {}'.format(protocol))
        exit(1)

def stop_routing_protocol(protocol, nsnames):
    if protocol == "batman-adv":
        stop_batmanadv_instances(nsnames)
    elif protocol == "yggdrasil":
        stop_yggdrasil_instances(nsnames)
    elif protocol == "babel":
        stop_babel_instances(nsnames)
    elif protocol == "olsr":
        stop_olsr_instances(nsnames)
    elif protocol == "none":
        stop_none_instances(nsnames)
    else:
        print('Error: unknown routing protocol: {}'.format(protocol))
        exit(1)

# test convergence of the routing protocol
# we want to keep it running until stopped..
def check_convergence(nsnames, rounds, max_samples, cvsfile = None):
    if len(nsnames) < 2:
        print('Network needs at least two nodes!')
        exit(1)

    pairs = get_random_samples(nsnames, max_samples)

    prev_ts = get_traffic_statistics(nsnames)
    ts = prev_ts
    n = 0

    for n in range(1, rounds + 1):
        print('Start test ({}/{})'.format(n, rounds))
        start = now()
        time.sleep(1)
        ps = get_ping_statistics(pairs, uplink_interface)
        ts = get_traffic_statistics(nsnames)
        stop = now()

        print('pings reached: {:0.2f}% ({} paths tested)'.format(
            100 * ps.reached / (ps.lost + ps.reached), len(pairs)))

        d = now() - start
        seconds = d.seconds + d.microseconds / 1000000

        # output data:

        print('send: {}/s ({}/s per node)'.format(
            format_bytes((ts.tx_bytes - prev_ts.tx_bytes) / seconds),
            format_bytes((ts.tx_bytes - prev_ts.tx_bytes) / seconds / len(nsnames))
        ))

        print('received: {}/s ({}/s per node)'.format(
            format_bytes((ts.rx_bytes - prev_ts.rx_bytes) / seconds),
            format_bytes((ts.rx_bytes - prev_ts.rx_bytes) / seconds / len(nsnames))
        ))

        if cvsfile is not None:
            cvsfile.write('{} {} {} {:0.2f} {:0.2f}'.format(
                n,
                seconds,
                len(nsnames),
                (ts.rx_bytes - prev_ts.rx_bytes),
                (ts.tx_bytes - prev_ts.tx_bytes)
            ))

        if ps.reached == len(pairs):
            print('all instances reached after {} iterations'.format(n))
            break

        prev_ts = ts

def measure_traffic(nsnames, duration, cvsfile = None):
    if len(nsnames) < 2:
        print('Network of at least two nodes needed!')
        exit(1)

    print('meassure traffic over {} seconds...'.format(duration))
    start = now()
    ts1 = get_traffic_statistics(nsnames)
    time.sleep(duration)
    ts2 = get_traffic_statistics(nsnames)
    stop = now()
    d = now() - start
    seconds = d.seconds + d.microseconds / 1000000

    print('send: {}/s ({}/s per node)'.format(
        format_bytes((ts2.tx_bytes - ts1.tx_bytes) / seconds),
        format_bytes((ts2.tx_bytes - ts1.tx_bytes) / seconds / len(nsnames))
    ))
    print('received: {}/s ({}/s per node)'.format(
        format_bytes((ts2.rx_bytes - ts1.rx_bytes) / seconds),
        format_bytes((ts2.rx_bytes - ts1.rx_bytes) / seconds / len(nsnames))
    ))

    if cvsfile is not None:
        print('write line to cvs file')
        cvsfile.write('{} {:0.2f} {:0.2f}\n'.format(
            # measurement duration
            duration,
            # send bytes/s per node
            (ts2.tx_bytes - ts1.tx_bytes) / seconds / len(nsnames),
            # received bytes/s per node
            (ts2.rx_bytes - ts1.rx_bytes) / seconds / len(nsnames)
        ))

# some miscellaneous tests
def test_misc(nsnames):
    if len(nsnames) < 2:
        print('Network of at least two nodes needed!')
        exit(1)

    # create a list of 10 unique test pairs
    pairs = random.sample(list(zip(nsnames, nsnames)), 10)

    start_time = now()

    print('start {}'.format(protocol))
    start_routing_protocol(protocol)

    print("get traffic statistics")
    ts = get_traffic_statistics(nsnames)
    ts.print()

    print('wait 10 seconds')
    time.sleep(10)

    print("1. ping")
    ps = get_ping_statistics(pairs, uplink_interface)
    ps.print()

    print('wait 10 seconds')
    time.sleep(10)

    print("2. ping")
    ps = get_ping_statistics(pairs, uplink_interface)
    ps.print()

    print("get traffic statistics")
    ts = get_traffic_statistics(nsnames)
    ts.print()

    print('stop {}'.format(protocol))
    stop_routing_protocol(protocol)

    print('Whole test duration: {}'.format(now() - start_time))


parser = argparse.ArgumentParser()
parser.add_argument('protocol',
    choices=['none', 'babel', 'batman-adv', 'olsr', 'yggdrasil'],
    help='Routing protocol to set up.')
parser.add_argument('--verbosity',
    choices=['verbose', 'normal', 'quiet'],
    default='normal',
    help='Set verbosity.')
parser.add_argument('--cvsout',
    dest='cvsout',
    help='Write CSV formatted data to file.')

subparsers = parser.add_subparsers(dest='action', required=True, help='Action help')
parser_start = subparsers.add_parser('start', help='Start protocol daemons in every namespace.')
parser_stop = subparsers.add_parser('stop', help='Stop protocol daemons in every namespace.')
parser_test_misc = subparsers.add_parser('test_misc', help='Start some unspecified test.')
parser_measure_traffic = subparsers.add_parser('measure_traffic', help='Measure the traffic across the network.')
parser_measure_traffic.add_argument('duration', type=int, default=10, help='Measure traffic of this timespan in seconds.')
parser_check_convergence  = subparsers.add_parser('check_convergence', help='Test if every node is connected to each.')
parser_check_convergence.add_argument('rounds', type=int, default=1, help='Maximum number of rounds until all pings reach its target.')
parser_check_convergence.add_argument('samples', type=int, default=100, help='Maximum number of source/target routes to be tested.')

args = parser.parse_args()

if os.popen('id -u').read().strip() != "0":
    sys.stderr.write('Need to run as root.\n')
    exit(1)

# all ns-* network namespaces
nsnames = [x for x in os.popen('ip netns list').read().split() if x.startswith('ns-')]

# network interface to send packets to/from
uplink_interface = "uplink"

cvsfile = None
if args.cvsout is not None:
    cvsfile = open(args.cvsout, 'a+')

# batman-adv uses its own interface as entry point to the mesh
if args.protocol == 'batman-adv':
    uplink_interface = 'bat0'
elif args.protocol == 'yggdrasil':
    uplink_interface = 'tun0'


if args.action == 'start':
    start_routing_protocol(args.protocol, nsnames)
elif args.action == 'stop':
    stop_routing_protocol(args.protocol, nsnames)
elif args.action == 'measure_traffic':
    measure_traffic(nsnames, args.duration, cvsfile)
elif args.action == 'test_misc':
    test_misc(nsnames)
elif args.action == 'check_convergence':
    check_convergence(nsnames, args.rounds, args.samples, cvsfile)
else:
    sys.stderr.write('Unknown action: {}\n'.format(args.action))
    exit(1)
