#!/usr/bin/env python3

import datetime
import argparse
import subprocess
import json
import math
import time
import sys
import os

from shared import (
    eprint, wait_for_completion, exec, default_remotes,
    millis, get_remote_mapping, stop_all_terminals, format_duration
)

verbosity = 'normal'

def get_mac_address(remote, nsname, interface):
    # print only MAC address
    stdout = exec(remote, f'ip netns exec "{nsname}" ip -0 addr list dev {interface}', get_output=True)[0]
    for line in stdout.split('\n'):
        if 'link/ether ' in line:
            return line.split()[1]

    return None

def interface_up(remote, nsname, interface, ignore_error=False):
    exec(remote, f'ip netns exec "{nsname}" ip link set "{interface}" up', ignore_error=ignore_error)

def interface_down(remote, nsname, interface, ignore_error=False):
    exec(remote, f'ip netns exec "{nsname}" ip link set "{interface}" down', ignore_error=ignore_error)

def interface_flush(remote, nsname, interface):
    # we need to flush for IPv4 and IPv6
    exec(remote, f'ip netns exec "{nsname}" ip -4 addr flush dev "{interface}"')
    exec(remote, f'ip netns exec "{nsname}" ip -6 addr flush dev "{interface}"')

def set_addr6(remote, nsname, interface, prefix_len):
    def eui64_suffix(remote, nsname, interface):
        mac = get_mac_address(remote, nsname, interface)
        return '{:02x}{}:{}ff:fe{}:{}{}'.format(
            int(mac[0:2], 16) ^ 2, # byte with flipped bit
            mac[3:5], mac[6:8], mac[9:11], mac[12:14], mac[15:17]
        )

    exec(remote, 'ip netns exec "{}" ip address add fdef:17a0:ffb1:300:{}/{} dev {}'.format(
        nsname,
        eui64_suffix(remote, nsname, interface),
        prefix_len,
        interface
    ))

def set_addr4(remote, nsname, interface, prefix_len):
    if not nsname.startswith('ns-'):
        eprint(f'namespace expected to start with ns-: {nsname}')
        exit(1)

    n = int(nsname[3:])
    a, b = divmod(n, 255)

    exec(remote, 'ip netns exec "{}" ip address add 10.0.{}.{}/{} dev {}'.format(
        nsname,
        a,
        b,
        prefix_len,
        interface
    ))

def count_instances(protocol, rmap):
    if protocol == 'batman-adv':
        count = 0
        for (nsname, remote) in rmap.items():
            rcode = exec(remote, f'ip netns exec {nsname} ip a l dev bat0', get_output=True, ignore_error=True)[2]
            if rcode == 0:
                count += 1
        return count
    else:
        remotes = {value.get('address', 'local'): value for key, value in rmap.items()}.values()
        program = {'yggdrasil': 'yggdrasil', 'babel': 'babeld', 'olsr1': 'olsrd', 'olsr2': 'olsrd2', 'bmx6': 'bmx6', 'bmx7': 'bmx7', 'cjdns': 'cjdroute'}[protocol]

        # Hack, otherwise pgrep will not count all process on the next try.
        # To sleep for a few seconds does not help, there is probably a bug.
        for remote in remotes:
            exec(remote, f'pgrep -c {program} || true')

        # TODO: count in namespaces!
        count = 0
        for remote in remotes:
            count += int(exec(remote, f'pgrep -c {program}', get_output=True, ignore_error=True)[0].strip())

        return count

def start_cjdns_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]

        if verbosity == 'verbose':
            print(f'start cjdns on {nsname}')

        # traffic goes through tun0, uplink only needs to be up
        interface_down(remote, nsname, 'uplink')
        interface_up(remote, nsname, 'uplink')
        interface_flush(remote, nsname, 'uplink')
        exec(remote, f'cjdroute --genconf > /tmp/cjdns-{nsname}.conf')
        exec(remote, f'ip netns exec "{nsname}" nohup cjdroute > /dev/null 2> /dev/null < /tmp/cjdns-{nsname}.conf &')

def stop_cjdns_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x cjdroute || true')
        exec(remote, f'rm -f /tmp/cjdns-*.conf')

def stop_cjdns_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]
        exec(remote, f'pkill -SIGKILL -x cjdroute --nslist {nsname} || true')
        exec(remote, f'rm -f /tmp/cjdns-{nsname}.conf')

def start_yggdrasil_instances(nsnames, rmap):
    config = 'AdminListen: none'
    for nsname in nsnames:
        remote = rmap[nsname]

        if verbosity == 'verbose':
            print(f'start yggdrasil in {nsname}')

        # Create a configuration file
        exec(remote, f'echo "{config}" > /tmp/yggdrasil-{nsname}.conf')

        # yggdrasil uses a tun0 interface, uplink only needs an fe80:* address
        interface_down(remote, nsname, 'uplink')
        interface_up(remote, nsname, 'uplink')
        exec(remote, f'ip netns exec "{nsname}" nohup yggdrasil -useconffile /tmp/yggdrasil-{nsname}.conf > /dev/null 2> /dev/null < /dev/null &')

def stop_yggdrasil_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x yggdrasil || true')
        exec(remote, f'rm -f /tmp/yggdrasil-*.conf')

def stop_yggdrasil_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]
        exec(remote, f'pkill -SIGKILL -x yggdrasil --nslist {nsname} || true')
        exec(remote, f'rm -f /tmp/yggdrasil-{nsname}.conf')

def start_batmanadv_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]

        if verbosity == 'verbose':
            print(f'start batman-adv in {nsname}')

        # traffic goes through bat0, uplink only needs to be up
        interface_down(remote, nsname, 'uplink')
        interface_up(remote, nsname, 'uplink')
        interface_flush(remote, nsname, 'uplink')
        exec(remote, f'ip netns exec "{nsname}" batctl meshif "bat0" interface add "uplink"')
        interface_up(remote, nsname, 'bat0')

def stop_batmanadv_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]
        exec(remote, f'ip netns exec "{nsname}" batctl meshif "bat0" interface del "uplink" || true')

def start_babel_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]

        if verbosity == 'verbose':
            address = remote.get('address', 'local')
            print(f'start babel in {address}/{nsname}')

        # babel needs the link local (fe80:*) and a regular IPv6 address
        interface_down(remote, nsname, 'uplink')
        interface_up(remote, nsname, 'uplink')
        set_addr6(remote, nsname, 'uplink', 64)
        exec(remote, f'ip netns exec "{nsname}" babeld -D -I /tmp/babel-{nsname}.pid "uplink"')

def stop_babel_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x babeld || true')
        exec(remote, f'rm -f /tmp/babel-*.pid')

def stop_babel_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]
        exec(remote, f'pkill -SIGKILL -x babeld --nslist {nsname} || true')
        exec(remote, f'rm -f /tmp/babel-{nsname}.pid')

def start_olsr1_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]

        if verbosity == 'verbose':
            address = remote.get('address', 'local')
            print(f'start olsr1 in {address}/{nsname}')

        # OLSR1 IPv6 seems to be broken/buggy
        # Let's use IPv4 instead
        interface_down(remote, nsname, 'uplink')
        interface_up(remote, nsname, 'uplink')
        interface_flush(remote, nsname, 'uplink')
        set_addr4(remote, nsname, 'uplink', 32)
        exec(remote, f'ip netns exec "{nsname}" olsrd -d 0 -i "uplink" -f /dev/null')

def stop_olsr1_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x olsrd || true')

def stop_olsr1_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]
        exec(remote, f'pkill -SIGKILL -x olsrd --nslist {nsname} || true')

def start_olsr2_instances(nsnames, rmap):
    config = (
        r'[global]\n'
        r'fork       yes\n'
        r'lockfile   -\n'
        r'\n'
        # restrict to IPv6
        r'[olsrv2]\n'
        r'originator  -0.0.0.0/0\n'
        r'originator  -::1/128\n'
        r'originator  default_accept\n'
        r'\n'
        # restrict to IPv6
        r'[interface]\n'
        r'bindto  -0.0.0.0/0\n'
        r'bindto  -::1/128\n'
        r'bindto  default_accept\n'
    )

    for nsname in nsnames:
        remote = rmap[nsname]
        if verbosity == 'verbose':
            address = remote.get('address', 'local')
            print(f'start olsr2 in {address}/{nsname}')

        # Create a configuration file
        exec(remote, f'echo "{config}" > /tmp/olsrd2-{nsname}.conf')

        # olsr2 needs the fe80:* address (link local) and a regular IPv6 address (/128 or other)
        interface_down(remote, nsname, 'uplink')
        interface_up(remote, nsname, 'uplink')
        set_addr6(remote, nsname, 'uplink', 128)
        exec(remote, f'ip netns exec "{nsname}" olsrd2 "uplink" --load /tmp/olsrd2-{nsname}.conf')

def stop_olsr2_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x olsrd2 || true')
        exec(remote, f'rm -f /tmp/olsrd2-*.conf')

def stop_olsr2_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]
        exec(remote, f'pkill -SIGKILL -x olsrd2 --nslist {nsname} || true')
        exec(remote, f'rm -f /tmp/olsrd2-{nsname}.conf')

def start_bmx7_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]

        if verbosity == 'verbose':
            print(f'start bmx7 in {nsname}')

        # not sure about the setup
        interface_down(remote, nsname, 'uplink')
        interface_up(remote, nsname, 'uplink')
        set_addr6(remote, nsname, 'uplink', 128)
        exec(remote, f'ip netns exec "{nsname}" bmx7 --runtimeDir /tmp/bmx7_{nsname} --nodeRsaKey 6 /keyPath=/tmp/bmx7_{nsname}/rsa.der --trustedNodesDir=/tmp/bmx7_{nsname}/trusted dev=uplink')

def stop_bmx7_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x bmx7 || true')
        exec(remote, f'rm -rf /tmp/bmx7-*')

def stop_bmx7_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]
        exec(remote, f'pkill -SIGKILL -x bmx7 --nslist {nsname} || true')
        exec(remote, f'rm -rf /tmp/bmx7_{nsname}')

def start_bmx6_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]

        if verbosity == 'verbose':
            print(f'start bmx6 in {nsname}')

        # bmx6 only needs the link local fe80:* address
        interface_down(remote, nsname, 'uplink')
        interface_up(remote, nsname, 'uplink')
        exec(remote, f'ip netns exec "{nsname}" bmx6 --runtimeDir /tmp/bmx6_{nsname} dev=uplink')

def stop_bmx6_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x bmx6 || true')
        exec(remote, f'rm -rf /tmp/bmx6-*')

def stop_bmx6_instances(nsnames, rmap):
    for nsname in nsnames:
        remote = rmap[nsname]
        exec(remote, f'pkill -SIGKILL -x bmx6 --nslist {nsname} || true')
        exec(remote, f'rm -rf /tmp/bmx6_{nsname}')

def start_routing_protocol(protocol, rmap, nsnames, ignore_error=False):
    beg_count = count_instances(protocol, rmap)
    beg_ms = millis()

    for nsname in nsnames:
        remote = rmap[nsname]
        interface_up(remote, nsname, 'uplink', ignore_error)

    if protocol == 'batman-adv':
        start_batmanadv_instances(nsnames, rmap)
    elif protocol == 'yggdrasil':
        start_yggdrasil_instances(nsnames, rmap)
    elif protocol == 'babel':
        start_babel_instances(nsnames, rmap)
    elif protocol == 'olsr1':
        start_olsr1_instances(nsnames, rmap)
    elif protocol == 'olsr2':
        start_olsr2_instances(nsnames, rmap)
    elif protocol == 'bmx6':
        start_bmx6_instances(nsnames, rmap)
    elif protocol == 'bmx7':
        start_bmx7_instances(nsnames, rmap)
    elif protocol == 'cjdns':
        start_cjdns_instances(nsnames, rmap)
    elif protocol == 'none':
        return
    else:
        eprint(f'Error: unknown routing protocol: {protocol}')
        exit(1)

    wait_for_completion()

    end_ms = millis()
    end_count = count_instances(protocol, rmap)

    count = end_count - beg_count
    if count != len(nsnames):
        eprint(f'Error: Failed to start {protocol} instances: {count}/{len(nsnames)} started')
        stop_all_terminals()
        exit(1)

    if verbosity != 'quiet':
        print('Started {} {} instances in {}'.format(count, protocol, format_duration(end_ms - beg_ms)))

def stop_routing_protocol(protocol, rmap, nsnames, ignore_error=False):
    beg_count = count_instances(protocol, rmap)
    beg_ms = millis()

    if protocol == 'batman-adv':
        stop_batmanadv_instances(nsnames, rmap)
    elif protocol == 'yggdrasil':
        stop_yggdrasil_instances(nsnames, rmap)
    elif protocol == 'babel':
        stop_babel_instances(nsnames, rmap)
    elif protocol == 'olsr1':
        stop_olsr1_instances(nsnames, rmap)
    elif protocol == 'olsr2':
        stop_olsr2_instances(nsnames, rmap)
    elif protocol == 'bmx6':
        stop_bmx6_instances(nsnames, rmap)
    elif protocol == 'bmx7':
        stop_bmx7_instances(nsnames, rmap)
    elif protocol == 'cjdns':
        stop_cjdns_instances(nsnames, rmap)
    elif protocol == 'none':
        pass
    else:
        eprint('Error: unknown routing protocol: {}'.format(protocol))
        exit(1)

    for nsname in nsnames:
        remote = rmap[nsname]
        interface_down(remote, nsname, 'uplink', ignore_error=ignore_error)

    wait_for_completion()

    end_ms = millis()
    end_count = count_instances(protocol, rmap)

    count = beg_count - end_count
    if count != len(nsnames):
        eprint(f'Error: Failed to stop {protocol} instances: {count}/{len(nsnames)} left')
        exit(1)

    if not ignore_error and verbosity != 'quiet':
        print('Stopped {} {} instances in {}'.format(len(nsnames), protocol, format_duration(end_ms - beg_ms)))

def _get_nsnames(rmap, from_state, to_state):
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
        all = list(rmap.keys())
        return (all, all)

    a = from_nsnames.difference(to_nsnames)
    b = to_nsnames.difference(from_nsnames)

    # (old_nsnames, new_nsnames)
    return (a, b)


protocol_choices = ['none', 'babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'yggdrasil']

def start(protocol, remotes=default_remotes):
    rmap = get_remote_mapping(remotes)
    nsnames = list(rmap.keys())
    start_routing_protocol(protocol, rmap, nsnames)

def stop(protocol, remotes=default_remotes):
    rmap = get_remote_mapping(remotes)
    nsnames = list(rmap.keys())
    stop_routing_protocol(protocol, rmap, nsnames)

def change(protocol, from_state = {}, to_state = {}, remotes=default_remotes):
    rmap = get_remote_mapping(remotes)
    (old_nsnames, new_nsnames) = _get_nsnames(rmap, from_state, to_state)

    stop_routing_protocol(protocol, rmap, old_nsnames)
    start_routing_protocol(protocol, rmap, new_nsnames)

def clear(remotes=default_remotes):
    #stop_batman_adv_instances_all(remotes)
    stop_yggdrasil_instances_all(remotes)
    stop_babel_instances_all(remotes)
    stop_olsr1_instances_all(remotes)
    stop_olsr2_instances_all(remotes)
    stop_bmx6_instances_all(remotes)
    stop_bmx7_instances_all(remotes)
    stop_cjdns_instances_all(remotes)

    #rmap = get_remote_mapping(remotes)
    #nsnames = list(rmap.keys())
    #for protocol in protocol_choices:
    #    stop_routing_protocol(protocol, rmap, nsnames, True)

def run(command, rmap, quiet=False):
    for (nsname, remote) in rmap.items():
        cmd = command.replace('{name}', nsname[3:])

        if quiet:
            exec(remote, f'ip netns exec "{nsname}" {cmd}', get_output=False, ignore_error=True)
        else:
            stdout, stderr, rcode = exec(remote, f'ip netns exec "{nsname}" {cmd}', get_output=True, ignore_error=True)

            if stdout or stderr:
                print(f'{nsname}')
                if stdout:
                    print(stdout)
                if stderr:
                    eprint(stderr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbosity', choices=['verbose', 'normal', 'quiet'], default='normal', help='Set verbosity.')
    parser.add_argument('--remotes', help='Distribute nodes and links on remotes described in the JSON file.')
    parser.set_defaults(from_state='none', to_state='none')
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

    parser_run = subparsers.add_parser('run', help='Execute any command in every namespace.')
    parser_run.add_argument('command', help='Shell command that is run. {name} is replaced by the nodes name.')
    parser_run.add_argument('--quiet', action='store_true', help='Do not output stdout and stderr.')
    parser_run.add_argument('from_state', nargs='?', default='none', help='From state')
    parser_run.add_argument('to_state', nargs='?', default='none', help='To state')

    parser_clear = subparsers.add_parser('clear', help='Stop all routing protocols.')

    args = parser.parse_args()

    if args.remotes:
        with open(args.remotes) as file:
            args.remotes = json.load(file)
    else:
        args.remotes = default_remotes

    # need root for local setup
    for remote in args.remotes:
        if remote.get('address') is None:
            if os.geteuid() != 0:
                eprint('Need to run as root.')
                exit(1)

    verbosity = args.verbosity

    # get node to remote mapping
    rmap = get_remote_mapping(args.remotes)

    # get nodes that have been added or will be removed
    (old_nsnames, new_nsnames) = _get_nsnames(rmap, args.from_state, args.to_state)

    if args.action == 'start':
        start_routing_protocol(args.protocol, rmap, new_nsnames)
    elif args.action == 'stop':
        stop_routing_protocol(args.protocol, rmap, old_nsnames)
    elif args.action == 'change':
        stop_routing_protocol(args.protocol, rmap, old_nsnames)
        start_routing_protocol(args.protocol, rmap, new_nsnames)
    elif args.action == 'clear':
        clear(args.remotes)
    elif args.action == 'run':
        run(args.command, rmap, args.quiet)
    else:
        eprint('Unknown action: {}'.format(args.action))
        exit(1)

    stop_all_terminals()
