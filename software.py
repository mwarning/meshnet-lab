#!/usr/bin/env python3

import datetime
import argparse
import subprocess
import json
import math
import time
import sys
import os


verbosity = 'normal'

def eprint(s):
    sys.stderr.write(s + '\n')

def _exec(cmd, detach=False, ignore_error=False):
    rc = 0

    if verbosity == 'verbose':
        if detach:
            rc = os.system('({}) &'.format(cmd))
        else:
            rc = os.system('({})'.format(cmd))
    elif verbosity == 'normal':
        if detach:
            rc = os.system('({}) > /dev/null &'.format(cmd))
        else:
            rc = os.system('({}) > /dev/null'.format(cmd))
    elif verbosity == 'quiet':
        if detach:
            rc = os.system('({}) > /dev/null 2>&1 &'.format(cmd))
        else:
            rc = os.system('({}) > /dev/null 2>&1'.format(cmd))
    else:
        eprint('Abort, invalid verbosity: {}'.format(verbosity))
        exit(1)

    if rc != 0 and not ignore_error:
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

def interface_up(nsname, interface, ignore_error=False):
    _exec(f'ip netns exec "{nsname}" ip link set "{interface}" up', ignore_error=ignore_error)

def interface_down(nsname, interface, ignore_error=False):
    _exec(f'ip netns exec "{nsname}" ip link set "{interface}" down', ignore_error=ignore_error)

def set_addr6(nsname, interface, prefix_len):
    def eui64_suffix(nsname, interface):
        mac = get_mac_address(nsname, interface)
        return '{:02x}{}:{}ff:fe{}:{}{}'.format(
            int(mac[0:2], 16) ^ 2, # byte with flipped bit
            mac[3:5], mac[6:8], mac[9:11], mac[12:14], mac[15:17]
        )

    _exec('ip netns exec "{}" ip address add fdef:17a0:ffb1:300:{}/{} dev {}'.format(
        nsname,
        eui64_suffix(nsname, interface),
        prefix_len,
        interface
    ))

def set_addr4(nsname, interface, prefix_len):
    if not nsname.startswith('ns-'):
        eprint(f'namespace expected to start with ns-: {nsname}')
        exit(1)

    n = int(nsname[3:])
    a, b = divmod(n, 255)

    _exec('ip netns exec "{}" ip address add 10.0.{}.{}/{} dev {}'.format(
        nsname,
        a,
        b,
        prefix_len,
        interface
    ))

def pkill(pname):
    matched = 0
    for i in range(0, 6):
        signal = '-SIGTERM' if i < 4 else '-SIGKILL'
        out = subprocess.Popen(['pkill', '-c', signal, '-x', pname], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        matched = matched if matched > 0 else int(out.communicate()[0])

        if out.returncode != 0:
            return matched

        time.sleep(i * i * 0.05)

    eprint(f'Failed to kill {nsname}')
    exit(1)

def start_cjdns_instances(nsnames):
    for nsname in nsnames:
        if verbosity == 'verbose':
            print(f'start cjdns on {nsname}')

        _exec(f'cjdroute --genconf > /tmp/cjdns-{nsname}.conf')
        _exec(f'ip netns exec "{nsname}" cjdroute < /tmp/cjdns-{nsname}.conf', detach=True)

def stop_cjdns_instances(nsnames):
    matched = pkill('cjdroute')

    if matched > 0:
        _exec('rm -f /tmp/cjdns-*.conf')

    return matched

def start_yggdrasil_instances(nsnames):
    for nsname in nsnames:
        if verbosity == 'verbose':
            print(f'start yggdrasil in {nsname}')

        # Create a configuration file
        configfile = f'/tmp/yggdrasil-{nsname}.conf'
        f = open(configfile, 'w')
        f.write('AdminListen: none')
        f.close()

        _exec('ip netns exec "{}" yggdrasil -useconffile {}'.format(nsname, configfile), detach=True)

def stop_yggdrasil_instances(nsnames):
    matched = pkill('yggdrasil')

    if matched > 0:
        _exec('rm -f /tmp/yggdrasil-*.conf')

    return matched

def start_batmanadv_instances(nsnames):
    for nsname in nsnames:
        if verbosity == 'verbose':
            print(f'start batman-adv in {nsname}')

        _exec(f'ip netns exec "{nsname}" batctl meshif "bat0" interface add "uplink"')
        interface_up(nsname, 'bat0')

def stop_batmanadv_instances(nsnames):
    count = 0

    for nsname in nsnames:
        rc = os.system(f'ip netns exec "{nsname}" batctl meshif "bat0" interface del "uplink" > /dev/null 2>&1')
        if rc == 0:
            count += 1

    return count

def start_babel_instances(nsnames):
    for nsname in nsnames:
        if verbosity == 'verbose':
            print(f'start babel in {nsname}')

        set_addr6(nsname, 'uplink', 64)
        _exec(f'ip netns exec "{nsname}" babeld -D -I /tmp/babel-{nsname}.pid "uplink"')

def stop_babel_instances(nsnames):
    matched = pkill('babeld')

    if matched > 0:
        _exec('rm -f /tmp/babel-*.pid')

    return matched

def start_olsr1_instances(nsnames):
    for nsname in nsnames:
        if verbosity == 'verbose':
            print(f'start olsr1 in {nsname}')

        # OLSR1 IPv6 seems to be broken/buggy
        set_addr4(nsname, 'uplink', 32)
        _exec(f'ip netns exec "{nsname}" olsrd -d 0 -i "uplink" -f /dev/null')

def stop_olsr1_instances(nsnames):
    matched = pkill('olsrd')

    # IPv4 address is not flushed when the device goes down
    for nsname in nsnames:
        _exec(f'ip netns exec "{nsname}" ip addr flush dev "uplink"')

    return matched

def start_olsr2_instances(nsnames):
    for nsname in nsnames:
        if verbosity == 'verbose':
            print(f'start olsr2 in {nsname}')

        # Create a configuration file
        # Print all settings: olsrd2_static --schema=all
        configfile = f'/tmp/olsrd2-{nsname}.conf'
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

        set_addr6(nsname, 'uplink', 128)
        _exec(f'ip netns exec "{nsname}" olsrd2 "uplink" --load {configfile}')

def stop_olsr2_instances(nsnames):
    matched = pkill('olsrd2')

    if matched > 0:
        _exec('rm -f /tmp/olsrd2-*.conf')

    return matched

def start_bmx7_instances(nsnames):
    for nsname in nsnames:
        if verbosity == 'verbose':
            print(f'start bmx7 in {nsname}')

        _exec(f'ip netns exec "{nsname}" bmx7 --runtimeDir /tmp/bmx7_{nsname} --nodeRsaKey 6 /keyPath=/tmp/bmx7_{nsname}/rsa.der --trustedNodesDir=/tmp/bmx7_{nsname}/trusted dev=uplink')

def stop_bmx7_instances(nsnames):
    matched = pkill('bmx7')

    if matched > 0:
        _exec('rm -rf /tmp/bmx7_*')

    return matched

def start_bmx6_instances(nsnames):
    for nsname in nsnames:
        if verbosity == 'verbose':
            print(f'start bmx6 in {nsname}')

        _exec(f'ip netns exec "{nsname}" bmx6 --runtimeDir /tmp/bmx6_{nsname} dev=uplink')

def stop_bmx6_instances(nsnames):
    matched = pkill('bmx6')

    if matched > 0:
        _exec('rm -rf /tmp/bmx6_*')

    return matched

def start_routing_protocol(protocol, nsnames, ignore_error=False):
    beg_ms = millis()

    for nsname in nsnames:
        interface_up(nsname, 'uplink', ignore_error)

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
        eprint(f'Error: unknown routing protocol: {protocol}')
        exit(1)

    end_ms = millis()
    if verbosity != 'quiet':
        print('Started {} {} instances in {}'.format(len(nsnames), protocol, format_duration(end_ms - beg_ms)))

def stop_routing_protocol(protocol, nsnames, ignore_error=False):
    count = 0
    beg_ms = millis()

    if protocol == 'batman-adv':
        count = stop_batmanadv_instances(nsnames)
    elif protocol == 'yggdrasil':
        count = stop_yggdrasil_instances(nsnames)
    elif protocol == 'babel':
        count = stop_babel_instances(nsnames)
    elif protocol == 'olsr1':
        count = stop_olsr1_instances(nsnames)
    elif protocol == 'olsr2':
        count = stop_olsr2_instances(nsnames)
    elif protocol == 'bmx6':
        count = stop_bmx6_instances(nsnames)
    elif protocol == 'bmx7':
        count = stop_bmx7_instances(nsnames)
    elif protocol == 'cjdns':
        count = stop_cjdns_instances(nsnames)
    elif protocol == 'none':
        count = 0
    else:
        eprint('Error: unknown routing protocol: {}'.format(protocol))
        exit(1)

    for nsname in nsnames:
        interface_down(nsname, 'uplink', ignore_error=ignore_error)

    end_ms = millis()
    if not ignore_error and verbosity != 'quiet':
        print('Stopped {} {} instances in {}'.format(count, protocol, format_duration(end_ms - beg_ms)))

def get_all_nsnames():
    # all ns-* network namespaces
    return [x for x in os.popen('ip netns list').read().split() if x.startswith('ns-')]

def get_nsnames(from_state, to_state):
    if isinstance(from_state, str):
        if from_state == 'none':
            from_state = {}
        else:
            with open(from_state) as file:
                from_state = json.load(file)

    if isinstance(to_state, str):
        if to_state == 'none':
            to_state = {}
        else:
            with open(to_state) as file:
                to_state = json.load(file)

    def get_nsname_set(state):
        nodes = set()

        for link in state.get('links', []):
            nodes.add('ns-{}'.format(link['source']))
            nodes.add('ns-{}'.format(link['target']))

        for node in state.get('nodes', []):
            nodes.add('ns-{}'.format(node['id']))

        return nodes

    from_nsnames = get_nsname_set(from_state)
    to_nsnames = get_nsname_set(to_state)

    if len(from_nsnames) == 0 and len(to_nsnames) == 0:
        all = get_all_nsnames()
        return (all, all)

    a = from_nsnames.difference(to_nsnames)
    b = to_nsnames.difference(from_nsnames)

    # (old_nsnames, new_nsnames)
    return (a, b)


protocol_choices = ['none', 'babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'yggdrasil']

def start(protocol):
    start_routing_protocol(protocol, get_all_nsnames())

def stop(protocol):
    stop_routing_protocol(protocol, get_all_nsnames())

def change(protocol, from_state = {}, to_state = {}):
    (old_nsnames, new_nsnames) = get_nsnames(from_state, to_state)

    stop_routing_protocol(protocol, old_nsnames)
    start_routing_protocol(protocol, new_nsnames)

def clear():
    nsnames = get_all_nsnames()
    for protocol in protocol_choices:
        stop_routing_protocol(protocol, nsnames, True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbosity', choices=['verbose', 'normal', 'quiet'], default='normal', help='Set verbosity.')
    subparsers = parser.add_subparsers(dest='action', required=True, help='Action')

    parser_start = subparsers.add_parser('start', help='Start protocol daemons in every namespace.')
    parser_start.add_argument('protocol', choices=protocol_choices, help='Routing protocol to start.')
    parser_start.add_argument('from_state', nargs='?', default='none',help='From state')
    parser_start.add_argument('to_state', nargs='?', default='none',help='To state')

    parser_stop = subparsers.add_parser('stop', help='Stop protocol daemons in every namespace.')
    parser_stop.add_argument('protocol', choices=protocol_choices, help='Routing protocol to stop.')
    parser_stop.add_argument('from_state', nargs='?', default='none',help='From state')
    parser_stop.add_argument('to_state', nargs='?', default='none',help='To state')

    parser_change = subparsers.add_parser('change', help='Stop/Start protocol daemons in every namespace.')
    parser_change.add_argument('protocol', choices=protocol_choices, help='Routing protocol to change.')
    parser_change.add_argument('from_state', nargs='?', default='none', help='From state')
    parser_change.add_argument('to_state', nargs='?', default='none', help='To state')

    parser_clear = subparsers.add_parser('clear', help='Stop all routing protocols.')
    parser_clear.set_defaults(from_state='none', to_state='none')

    args = parser.parse_args()

    if os.geteuid() != 0:
        eprint('Need to run as root.')
        exit(1)

    verbosity = args.verbosity

    (old_nsnames, new_nsnames) = get_nsnames(args.from_state, args.to_state)

    if args.action == 'start':
        start_routing_protocol(args.protocol, new_nsnames)
    elif args.action == 'stop':
        stop_routing_protocol(args.protocol, old_nsnames)
    elif args.action == 'change':
        stop_routing_protocol(args.protocol, old_nsnames)
        start_routing_protocol(args.protocol, new_nsnames)
    elif args.action == 'clear':
        for protocol in protocol_choices:
            stop_routing_protocol(protocol, old_nsnames, True)
    else:
        eprint('Unknown action: {}'.format(args.action))
        exit(1)
