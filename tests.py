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
# TODO: return IPv6 address of the broadest scope in general
def get_ipv6_address(nsname, interface):
    lladdr = None
    # print only IPv6 addresses
    output = os.popen('ip netns exec "{}" ip -6 addr list dev {}'.format(nsname, interface)).read()
    for line in output.split("\n"):
        if 'inet6 ' in line:
            addr = line.split()[1].split("/")[0]
            if addr.startswith('fe80'):
                lladdr = addr
            else:
                return addr

    return lladdr

def get_mac_address(nsname, interface):
    # print only MAC address
    output = os.popen('ip netns exec "{}" ip -0 addr list dev {}'.format(nsname, interface)).read()
    for line in output.split("\n"):
        if 'link/ether ' in line:
            return line.split()[1]

    return None

def eui64_suffix(nsname, interface):
    mac = get_mac_address(nsname, interface)
    return '{:02x}{}:{}ff:fe{}:{}{}'.format(
        int(mac[0:2], 16) ^ 2, # byte with flipped bit
        mac[3:5], mac[6:8], mac[9:11], mac[12:14], mac[15:17]
    )

class PingStatistics:
    def __init__(self, nssource, nstarget, interface, packets, wait):
        self.nssource = nssource
        self.nstarget = nstarget

        nstarget_addr = get_ipv6_address(nstarget, interface)
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
            print("{}: Cannot get any IPv6 address of interface {}".format(nstarget, interface))

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
    exec('rm -f /tmp/yggdrasil-*.conf')

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

        exec('ip netns exec "{}" babeld -D -I /tmp/babel-{}.pid "uplink"'.format(nsname, nsname))

def stop_babel_instances(nsnames):
    if args.verbosity == 'verbose':
        print("  stop babel in all namespaces")

    if len(nsnames) > 0:
        exec('rm -f /tmp/babel-*.pid')
        exec('pkill babeld')

def start_olsr2_instances(nsnames):
    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print("  start olsr2 on {}".format(nsname))

        # Create a configuration file
        # Print all settings: olsrd2_static --schema=all
        configfile = "/tmp/olsrd2-{}.conf".format(nsname)
        f = open(configfile, "w")
        f.write(
            '[global]\n'
            'fork       yes\n'
            'lockfile   -\n'
            '\n'
            # restrict to IPv6
            '[olsrv2]\n'
            'originator  -0.0.0.0/0\n'
            'originator  -::1/128\n'
            'originator  default_accept\n'
            '\n'
            # restrict to IPv6
            '[interface]\n'
            'bindto  -0.0.0.0/0\n'
            'bindto  -::1/128\n'
            'bindto  default_accept\n'
            )
        f.close()

        # TODO: down interface, flush interface, up interface, assign address
        exec('ip netns exec "{}" olsrd2 "uplink" --load {}'.format(nsname, configfile))
        exec('ip netns exec "{}" ip address add fdef:17a0:ffb1:300:{}/64 dev uplink'.format(
            nsname,
            eui64_suffix(nsname, 'uplink')
        ))

def stop_olsr2_instances(nsnames):
    if args.verbosity == 'verbose':
        print("  stop olsr2 in all namespaces")

    if len(nsnames) > 0:
        exec('pkill olsrd2')
        exec('rm -f /tmp/olsrd2-*.conf')

def start_routing_protocol(protocol, nsnames):
    if protocol == "batman-adv":
        start_batmanadv_instances(nsnames)
    elif protocol == "yggdrasil":
        start_yggdrasil_instances(nsnames)
    elif protocol == "babel":
        start_babel_instances(nsnames)
    elif protocol == "olsr2":
        start_olsr2_instances(nsnames)
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
    elif protocol == "olsr2":
        stop_olsr2_instances(nsnames)
    elif protocol == "none":
        stop_none_instances(nsnames)
    else:
        print('Error: unknown routing protocol: {}'.format(protocol))
        exit(1)

# test convergence of the routing protocol
# we want to keep it running until stopped..
def test_convergence(nsnames, max_samples, wait, cvsfile = None):
    if len(nsnames) < 2:
        print('Network needs at least two nodes!')
        exit(1)

    pairs = get_random_samples(nsnames, max_samples)

    ts_beg = get_traffic_statistics(nsnames)
    start = now()
    time.sleep(wait)
    ps = get_ping_statistics(pairs, uplink_interface)
    stop = now()
    ts_end = get_traffic_statistics(nsnames)

    print('pings reached: {:0.2f}% ({} paths tested)'.format(
        100 * ps.reached / (ps.lost + ps.reached), len(pairs)))

    d = now() - start
    seconds = d.seconds + d.microseconds / 1000000

    # output data

    print('received: {}/s ({}/s per node)'.format(
        format_bytes((ts_end.rx_bytes - ts_beg.rx_bytes) / seconds),
        format_bytes((ts_end.rx_bytes - ts_beg.rx_bytes) / seconds / len(nsnames))
    ))

    print('send: {}/s ({}/s per node)'.format(
        format_bytes((ts_end.tx_bytes - ts_beg.tx_bytes) / seconds),
        format_bytes((ts_end.tx_bytes - ts_beg.tx_bytes) / seconds / len(nsnames))
    ))

    if cvsfile is not None:
        cvsfile.write('{:0.2f} {:0.2f} {:0.2f} {:0.2f}\n'.format(
            # duration of the ping period
            seconds,
            # reached pings in %
            100 * ps.reached / (ps.lost + ps.reached),
            # received data during ping tests
            (ts_end.rx_bytes - ts_beg.rx_bytes) / seconds / len(nsnames),
            # send data during pings tests
            (ts_end.tx_bytes - ts_beg.tx_bytes) / seconds / len(nsnames)
        ))

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

    print('received: {}/s ({}/s per node)'.format(
        format_bytes((ts2.rx_bytes - ts1.rx_bytes) / seconds),
        format_bytes((ts2.rx_bytes - ts1.rx_bytes) / seconds / len(nsnames))
    ))

    print('send: {}/s ({}/s per node)'.format(
        format_bytes((ts2.tx_bytes - ts1.tx_bytes) / seconds),
        format_bytes((ts2.tx_bytes - ts1.tx_bytes) / seconds / len(nsnames))
    ))

    if cvsfile is not None:
        print('write line to cvs file')
        cvsfile.write('{} {:0.2f} {:0.2f}\n'.format(
            # measurement duration
            duration,
            # received bytes/s per node
            (ts2.rx_bytes - ts1.rx_bytes) / seconds / len(nsnames),
            # send bytes/s per node
            (ts2.tx_bytes - ts1.tx_bytes) / seconds / len(nsnames)
        ))

parser = argparse.ArgumentParser()
parser.add_argument('protocol',
    choices=['none', 'babel', 'batman-adv', 'olsr2', 'yggdrasil'],
    help='Routing protocol to set up.')
parser.add_argument('--verbosity',
    choices=['verbose', 'normal', 'quiet'],
    default='normal',
    help='Set verbosity.')
parser.add_argument('--seed',
    type=int,
    help='Seed the random generator.')
parser.add_argument('--cvsout',
    dest='cvsout',
    help='Write CSV formatted data to file.')

subparsers = parser.add_subparsers(dest='action', required=True, help='Action help')
parser_start = subparsers.add_parser('start', help='Start protocol daemons in every namespace.')
parser_stop = subparsers.add_parser('stop', help='Stop protocol daemons in every namespace.')
parser_measure_traffic = subparsers.add_parser('measure_traffic', help='Measure the traffic across the network.')
parser_measure_traffic.add_argument('--duration', type=int, default=10, help='Measure traffic of this timespan in seconds.')
parser_test_convergence  = subparsers.add_parser('test_convergence', help='Test if every node is connected to each.')
parser_test_convergence.add_argument('--samples', type=int, default=100, help='Maximum number of source/target routes to be tested.')
parser_test_convergence.add_argument('--wait', type=int, default=1, help='Seconds to wait for a ping to arrive.')
parser_test_convergence.add_argument('--exit-early', action='store_true', help='Exit when every ping on all tested paths arrived.')

args = parser.parse_args()

if os.popen('id -u').read().strip() != "0":
    sys.stderr.write('Need to run as root.\n')
    exit(1)

random.seed(args.seed)

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
elif args.action == 'test_convergence':
    test_convergence(nsnames, args.samples, args.wait, cvsfile)
else:
    sys.stderr.write('Unknown action: {}\n'.format(args.action))
    exit(1)
