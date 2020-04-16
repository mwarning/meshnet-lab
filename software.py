#!/usr/bin/env python3

import datetime
import argparse
import json
import math
import time
import sys
import os


def eprint(s):
    sys.stderr.write(s + '\n')

def exec(cmd, detach=False):
    rc = 0

    if args.verbosity == 'verbose':
        if detach:
            rc = os.system('{} &'.format(cmd))
        else:
            rc = os.system('{}'.format(cmd))
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
        eprint('Abort, invalid verbosity: {}'.format(args.verbosity))
        exit(1)

    if rc != 0:
        eprint('Abort, command failed: {}'.format(cmd))
        #todo: kill routing programs!
        #print('Cleanup done')
        exit(1)

# get time in milliseconds
def millis():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

def get_mac_address(nsname, interface):
    # print only MAC address
    output = os.popen('ip netns exec "{}" ip -0 addr list dev {}'.format(nsname, interface)).read()
    for line in output.split('\n'):
        if 'link/ether ' in line:
            return line.split()[1]

    return None

def format_duration(time_ms):
    d, remainder = divmod(time_ms, 24 * 60 * 60 * 1000)
    h, remainder = divmod(remainder, 60 * 60 * 1000)
    m, remainder = divmod(remainder, 60 * 1000)
    s, remainder = divmod(remainder, 1000)
    ms = remainder

    if d > 0:
        if h > 0:
            return "{}.{}d".format(int(d), int(h))
        return "{}d".format(int(d))
    elif h > 0:
        if m > 0:
            return "{}.{}h".format(int(h), int(m))
        return "{}h".format(int(h))
    elif m > 0:
        if s > 0:
            return "{}.{}m".format(int(m), int(s))
        return "{}m".format(int(m))
    elif s > 0:
        if ms > 0:
            return "{}.{}s".format(int(s), int(ms))
        return "{}s".format(int(s))
    else:
        return "{}ms".format(int(ms))

def reset_interface(nsname, interface):
    exec('ip netns exec "{}" ip link set "{}" down'.format(nsname, interface))
    exec('ip netns exec "{}" ip link set "{}" up'.format(nsname, interface))

def set_addr6(nsname, interface, prefix_len):
    def eui64_suffix(nsname, interface):
        mac = get_mac_address(nsname, interface)
        return '{:02x}{}:{}ff:fe{}:{}{}'.format(
            int(mac[0:2], 16) ^ 2, # byte with flipped bit
            mac[3:5], mac[6:8], mac[9:11], mac[12:14], mac[15:17]
        )

    exec('ip netns exec "{}" ip address add fdef:17a0:ffb1:300:{}/{} dev {}'.format(
        nsname,
        eui64_suffix(nsname, interface),
        prefix_len,
        interface
    ))

def set_addr4(nsname, interface, prefix_len):
    if not nsname.startswith('ns-'):
        eprint('namespace expected to start with ns-: {}'.format(nsname))
        exit(1)

    n = int(nsname[3:])
    a, b = divmod(n, 255)

    exec('ip netns exec "{}" ip address add 10.0.{}.{}/{} dev {}'.format(
        nsname,
        a,
        b,
        prefix_len,
        interface
    ))

def pkill(pname):
    for _ in range(0, 10):
        rc = os.system('pkill -9 {}'.format(pname))
        if rc != 0:
            # assume that there is no process left to kill
            return
        time.sleep(1)

    eprint('Failed to kill {}'.format(pname))
    exit(1)

def start_cjdns_instances(nsnames):
    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print('start cjdns on {}'.format(nsname))

        exec('cjdroute --genconf > /tmp/cjdns-{}.conf'.format(nsname))
        exec('ip netns exec "{}" cjdroute < /tmp/cjdns-{}.conf'.format(nsname, nsname), True)

def stop_cjdns_instances(nsnames):
    if args.verbosity == 'verbose':
       print('stop cjdns in all namespaces')

    exec('rm -f /tmp/cjdns-*.conf')
    if len(nsnames) > 0:
        pkill('cjdroute')

def start_yggdrasil_instances(nsnames):
    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print('start yggdrasil in {}'.format(nsname))

        # Create a configuration file
        configfile = '/tmp/yggdrasil-{}.conf'.format(nsname)
        f = open(configfile, 'w')
        f.write('AdminListen: none')
        f.close()

        reset_interface(nsname, 'uplink')
        exec('ip netns exec "{}" yggdrasil -useconffile {}'.format(nsname, configfile), True)

def stop_yggdrasil_instances(nsnames):
    if args.verbosity == 'verbose':
       print('stop yggdrasil in {} namespaces'.format(len(nsnames)))

    exec('rm -f /tmp/yggdrasil-*.conf')
    if len(nsnames) > 0:
        pkill('yggdrasil')

def start_batmanadv_instances(nsnames):
    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print('start batman-adv in {}'.format(nsname))

        reset_interface(nsname, 'uplink')
        exec('ip netns exec "{}" batctl meshif "bat0" interface add "uplink"'.format(nsname))
        reset_interface(nsname, 'bat0')

def stop_batmanadv_instances(nsnames):
    if args.verbosity == 'verbose':
        print('stop batman-adv in {} namespaces'.format(len(nsnames)))

    for nsname in nsnames:
        exec('ip netns exec "{}" batctl meshif "bat0" interface del "uplink"'.format(nsname))

def start_babel_instances(nsnames):
    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print('start babel in {}'.format(nsname))

        reset_interface(nsname, 'uplink')
        set_addr6(nsname, 'uplink', 64)
        exec('ip netns exec "{}" babeld -D -I /tmp/babel-{}.pid "uplink"'.format(nsname, nsname))

def stop_babel_instances(nsnames):
    if args.verbosity == 'verbose':
        print('stop babel in {} namespaces'.format(len(nsnames)))

    if len(nsnames) > 0:
        pkill('babeld')
        exec('rm -f /tmp/babel-*.pid')

def start_olsr1_instances(nsnames):
    for nsname in nsnames:
        reset_interface(nsname, 'uplink')
        # OLSR1 IPv6 seems to be broken/buggy
        set_addr4(nsname, 'uplink', 32)

    # olsr block and wait 5 seconds if no interface is ready
    time.sleep(1)

    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print('start olsr1 in {}'.format(nsname))

        exec('ip netns exec "{}" olsrd -d 0 -i "uplink" -f /dev/null'.format(nsname))

def stop_olsr1_instances(nsnames):
    if args.verbosity == 'verbose':
        print('stop olsr1 in {} namespaces'.format(len(nsnames)))

    if len(nsnames) > 0:
        pkill('olsrd')

def start_olsr2_instances(nsnames):
    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print('start olsr2 in {}'.format(nsname))

        # Create a configuration file
        # Print all settings: olsrd2_static --schema=all
        configfile = '/tmp/olsrd2-{}.conf'.format(nsname)
        f = open(configfile, 'w')
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

        reset_interface(nsname, 'uplink')
        set_addr6(nsname, 'uplink', 128)
        exec('ip netns exec "{}" olsrd2 "uplink" --load {}'.format(nsname, configfile))

def stop_olsr2_instances(nsnames):
    if args.verbosity == 'verbose':
        print('stop olsr2 in {} namespaces'.format(len(nsnames)))

    if len(nsnames) > 0:
        pkill('olsrd2')
        exec('rm -f /tmp/olsrd2-*.conf')

def start_bmx7_instances(nsnames):
    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print('start bmx7 in {}'.format(nsname))

        reset_interface(nsname, 'uplink')
        exec('ip netns exec "{0}" bmx7 --runtimeDir /tmp/bmx7_{0} --nodeRsaKey 6 /keyPath=/tmp/bmx7_{0}/rsa.der --trustedNodesDir=/tmp/bmx7_{0}/trusted dev=uplink'.format(nsname))

def stop_bmx7_instances(nsnames):
    if args.verbosity == 'verbose':
        print('stop bmx7 in {} namespaces'.format(len(nsnames)))

    if len(nsnames) > 0:
        pkill('bmx7')
        exec('rm -rf /tmp/bmx7_*')

def start_bmx6_instances(nsnames):
    for nsname in nsnames:
        if args.verbosity == 'verbose':
            print('start bmx6 in {}'.format(nsname))

        reset_interface(nsname, 'uplink')
        exec('ip netns exec "{}" bmx6 --runtimeDir /tmp/bmx6_{} dev=uplink'.format(nsname, nsname, nsname))

def stop_bmx6_instances(nsnames):
    if args.verbosity == 'verbose':
        print('stop bmx6 in {} namespaces'.format(len(nsnames)))

    if len(nsnames) > 0:
        pkill('bmx6')
        exec('rm -rf /tmp/bmx6_*')

def start_routing_protocol(protocol, nsnames):
    beg_ms = millis()

    if protocol == 'batman-adv':
        start_batmanadv_instances(nsnames)
    elif protocol == 'yggdrasil':
        start_yggdrasil_instances(nsnames)
    elif protocol == 'babel':
        start_babel_instances(nsnames)
    elif protocol == 'olsr1':
        start_olsr1_instances(nsnames)
    elif protocol == 'olsr2':
        start_olsr2_instances(nsnames)
    elif protocol == 'bmx6':
        start_bmx6_instances(nsnames)
    elif protocol == 'bmx7':
        start_bmx7_instances(nsnames)
    elif protocol == 'cjdns':
        start_cjdns_instances(nsnames)
    elif protocol == 'none':
        return
    else:
        eprint('Error: unknown routing protocol: {}'.format(protocol))
        exit(1)

    end_ms = millis()
    if args.verbosity != 'quiet':
        print('Started {} instances in {}'.format(len(nsnames), format_duration(end_ms - beg_ms)))

def stop_routing_protocol(protocol, nsnames):
    beg_ms = millis()

    if protocol == 'batman-adv':
        stop_batmanadv_instances(nsnames)
    elif protocol == 'yggdrasil':
        stop_yggdrasil_instances(nsnames)
    elif protocol == 'babel':
        stop_babel_instances(nsnames)
    elif protocol == 'olsr1':
        stop_olsr1_instances(nsnames)
    elif protocol == 'olsr2':
        stop_olsr2_instances(nsnames)
    elif protocol == 'bmx6':
        stop_bmx6_instances(nsnames)
    elif protocol == 'bmx7':
        stop_bmx7_instances(nsnames)
    elif protocol == 'cjdns':
        stop_cjdns_instances(nsnames)
    elif protocol == 'none':
        return
    else:
        eprint('Error: unknown routing protocol: {}'.format(protocol))
        exit(1)

    end_ms = millis()
    if args.verbosity != 'quiet':
        print('Stopped {} instances in {}'.format(len(nsnames), format_duration(end_ms - beg_ms)))

def get_all_nsnames():
    # all ns-* network namespaces
    return [x for x in os.popen('ip netns list').read().split() if x.startswith('ns-')]

def get_nsnames(from_state, to_state):
    if from_state is None and to_state is None:
        all = get_all_nsnames()
        return (all, all)

    def get_node_set(path):
        data = None
        if path == 'none' or path is None:
            data = json.loads('{"links":[]}')
        else:
            data = json.load(open(path))

        nodes = set()
        for link in data['links']:
            nodes.add(str(link['source']))
            nodes.add(str(link['target']))

        return nodes

    from_nsnames = get_node_set(from_state)
    to_nsnames = get_node_set(to_state)
    a = from_nsnames.intersection(to_nsnames)
    b = to_nsnames.intersection(from_nsnames)
    # (old_nsnames, new_nsnames)
    return (a, b)

parser = argparse.ArgumentParser()
parser.add_argument('protocol',
    choices=['none', 'babel', 'batman-adv', 'olsr1', 'olsr2', 'bmx6', 'bmx7', 'yggdrasil', 'cjdns'],
    help='Routing protocol to set up.')
parser.add_argument('--verbosity',
    choices=['verbose', 'normal', 'quiet'],
    default='normal',
    help='Set verbosity.')

subparsers = parser.add_subparsers(dest='action', required=True, help='Action')

parser_start = subparsers.add_parser('start', help='Start protocol daemons in every namespace.')
parser_start.add_argument('from_state', nargs='?', help='From state')
parser_start.add_argument('to_state', nargs='?', help='To state')
parser_stop = subparsers.add_parser('stop', help='Stop protocol daemons in every namespace.')
parser_stop.add_argument('from_state', nargs='?', help='From state')
parser_stop.add_argument('to_state', nargs='?', help='To state')
parser_change = subparsers.add_parser('change', help='Stop/Start protocol daemons in every namespace.')
parser_change.add_argument('from_state', nargs='?', help='From state')
parser_change.add_argument('to_state', nargs='?', help='To state')

args = parser.parse_args()

if os.popen('id -u').read().strip() != '0':
    eprint('Need to run as root.')
    exit(1)

# network interface to send packets to/from
uplink_interface = 'uplink'

# batman-adv uses its own interface as entry point to the mesh
if args.protocol == 'batman-adv':
    uplink_interface = 'bat0'
elif args.protocol == 'yggdrasil':
    uplink_interface = 'tun0'

(old_nsnames, new_nsnames) = get_nsnames(args.from_state, args.to_state)

if args.action == 'start':
    start_routing_protocol(args.protocol, new_nsnames)
elif args.action == 'stop':
    stop_routing_protocol(args.protocol, old_nsnames)
elif args.action == 'change':
    stop_routing_protocol(args.protocol, old_nsnames)
    start_routing_protocol(args.protocol, new_nsnames)
else:
    eprint('Unknown action: {}'.format(args.action))
    exit(1)
