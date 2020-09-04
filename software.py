#!/usr/bin/env python3

import datetime
import argparse
import subprocess
import hashlib
import json
import math
import time
import sys
import os

from shared import (
    eprint, wait_for_completion, exec, default_remotes, check_access,
    millis, get_remote_mapping, stop_all_terminals, format_duration,
    get_current_state
)

verbosity = 'normal'

def get_mac_address(remote, id, interface):
    # print only MAC address
    stdout = exec(remote, f'ip netns exec "ns-{id}" ip -0 addr list dev {interface}', get_output=True)[0]
    for line in stdout.split('\n'):
        if 'link/ether ' in line:
            return line.split()[1]

    return None

def interface_up(remote, id, interface, ignore_error=False):
    exec(remote, f'ip netns exec "ns-{id}" ip link set "{interface}" up', ignore_error=ignore_error)

def interface_down(remote, id, interface, ignore_error=False):
    exec(remote, f'ip netns exec "ns-{id}" ip link set "{interface}" down', ignore_error=ignore_error)

def interface_flush(remote, id, interface):
    # we need to flush for IPv4 and IPv6
    exec(remote, f'ip netns exec "ns-{id}" ip -4 addr flush dev "{interface}"')
    exec(remote, f'ip netns exec "ns-{id}" ip -6 addr flush dev "{interface}"')

def set_addr6(remote, id, interface, prefix_len):
    def eui64_suffix(remote, id, interface):
        mac = get_mac_address(remote, id, interface)
        return '{:02x}{}:{}ff:fe{}:{}{}'.format(
            int(mac[0:2], 16) ^ 2, # byte with flipped bit
            mac[3:5], mac[6:8], mac[9:11], mac[12:14], mac[15:17]
        )

    exec(remote, 'ip netns exec "ns-{}" ip address add fdef:17a0:ffb1:300:{}/{} dev {}'.format(
        id,
        eui64_suffix(remote, id, interface),
        prefix_len,
        interface
    ))

def set_addr4(remote, id, interface, prefix_len):
    # map namespace to unique ip address
    array = str.encode(id)
    a = hashlib.md5(array).digest()[:4]

    exec(remote, 'ip netns exec "ns-{}" ip address add 10.{}.{}.{}/{} dev {}'.format(
        id,
        a[0],
        a[1],
        a[2],
        prefix_len,
        interface
    ))

def count_instances(protocol, rmap):
    if protocol == 'batman-adv':
        count = 0
        for (id, remote) in rmap.items():
            rcode = exec(remote, f'ip netns exec "ns-{id}" ip a l dev bat0', get_output=True, ignore_error=True)[2]
            if rcode == 0:
                count += 1
        return count
    else:
        remotes = {value.get('address', 'local'): value for key, value in rmap.items()}.values()
        program = {
            'babel': 'babeld',
            'bmx6': 'bmx6',
            'bmx7': 'bmx7',
            'cjdns': 'cjdroute',
            'olsr1': 'olsrd',
            'olsr2': 'olsrd2',
            'ospf': 'bird6',
            'yggdrasil': 'yggdrasil'
        }[protocol]

        # TODO: count in namespaces!
        count = 0
        for remote in remotes:
            count += int(exec(remote, f'pgrep -c {program}', get_output=True, ignore_error=True)[0].strip())

        return count

def start_cjdns_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]

        if verbosity == 'verbose':
            address = remote.get('address', 'local')
            print(f'start cjdns in {address}/ns-{id}')

        # traffic goes through tun0, uplink only needs to be up
        interface_down(remote, id, 'uplink')
        interface_up(remote, id, 'uplink')
        interface_flush(remote, id, 'uplink')
        exec(remote, f'cjdroute --genconf > /tmp/cjdns-{id}.conf')
        exec(remote, f'ip netns exec "ns-{id}" nohup cjdroute > /dev/null 2> /dev/null < /tmp/cjdns-{id}.conf &')

def stop_cjdns_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x cjdroute || true')
        exec(remote, f'rm -f /tmp/cjdns-*.conf')

def stop_cjdns_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]
        exec(remote, f'pkill -SIGKILL -x cjdroute --nslist ns-{id} || true')
        exec(remote, f'rm -f /tmp/cjdns-{id}.conf')

def start_yggdrasil_instances(ids, rmap):
    config = 'AdminListen: none'
    for id in ids:
        remote = rmap[id]

        if verbosity == 'verbose':
            address = remote.get('address', 'local')
            print(f'start yggdrasil in {address}/ns-{id}')

        # Create a configuration file
        exec(remote, f'echo "{config}" > /tmp/yggdrasil-{id}.conf')

        # yggdrasil uses a tun0 interface, uplink only needs an fe80:* address
        interface_down(remote, id, 'uplink')
        interface_up(remote, id, 'uplink')
        exec(remote, f'ip netns exec "ns-{id}" nohup yggdrasil -useconffile /tmp/yggdrasil-{id}.conf > /dev/null 2> /dev/null < /dev/null &')

def stop_yggdrasil_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x yggdrasil || true')
        exec(remote, f'rm -f /tmp/yggdrasil-*.conf')

def stop_yggdrasil_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]
        exec(remote, f'pkill -SIGKILL -x yggdrasil --nslist ns-{id} || true')
        exec(remote, f'rm -f /tmp/yggdrasil-{id}.conf')

def start_batmanadv_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]

        if verbosity == 'verbose':
            address = remote.get('address', 'local')
            print(f'start batman-adv in {address}/ns-{id}')

        # traffic goes through bat0, uplink only needs to be up
        interface_down(remote, id, 'uplink')
        interface_up(remote, id, 'uplink')
        interface_flush(remote, id, 'uplink')
        exec(remote, f'ip netns exec "ns-{id}" batctl meshif "bat0" interface add "uplink"')
        interface_up(remote, id, 'bat0')

def stop_batmanadv_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]
        exec(remote, f'ip netns exec "ns-{id}" batctl meshif "bat0" interface del "uplink" || true')

def stop_batmanadv_instances_all(remotes):
    rmap = get_remote_mapping(remotes)
    for id, remote in rmap.items():
        exec(remote, f'ip netns exec "ns-{id}" batctl meshif "bat0" interface del "uplink" || true')

def start_babel_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]

        if verbosity == 'verbose':
            address = remote.get('address', 'local')
            print(f'start babel in {address}/ns-{id}')

        # babel needs the link local (fe80:*) and a regular IPv6 address
        interface_down(remote, id, 'uplink')
        interface_up(remote, id, 'uplink')
        set_addr6(remote, id, 'uplink', 64)
        exec(remote, f'ip netns exec "ns-{id}" babeld -D -I /tmp/babel-{id}.pid "uplink"')

def stop_babel_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x babeld || true')
        exec(remote, f'rm -f /tmp/babel-*.pid')

def stop_babel_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]
        exec(remote, f'pkill -SIGKILL -x babeld --nslist ns-{id} || true')
        exec(remote, f'rm -f /tmp/babel-{id}.pid')

def start_olsr1_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]

        if verbosity == 'verbose':
            address = remote.get('address', 'local')
            print(f'start olsr1 in {address}/ns-{id}')

        # OLSR1 IPv6 seems to be broken/buggy
        # Let's use IPv4 instead
        interface_down(remote, id, 'uplink')
        interface_up(remote, id, 'uplink')
        interface_flush(remote, id, 'uplink')
        set_addr4(remote, id, 'uplink', 32)
        exec(remote, f'ip netns exec "ns-{id}" olsrd -d 0 -i "uplink" -f /dev/null')

def stop_olsr1_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x olsrd || true')

def stop_olsr1_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]
        exec(remote, f'pkill -SIGKILL -x olsrd --nslist ns-{id} || true')

def start_olsr2_instances(ids, rmap):
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

    for id in ids:
        remote = rmap[id]
        if verbosity == 'verbose':
            address = remote.get('address', 'local')
            print(f'start olsr2 in {address}/ns-{id}')

        # Create a configuration file
        exec(remote, f'printf "{config}" > /tmp/olsrd2-{id}.conf')

        # olsr2 needs the fe80:* address (link local) and a regular IPv6 address (/128 or other)
        interface_down(remote, id, 'uplink')
        interface_up(remote, id, 'uplink')
        set_addr6(remote, id, 'uplink', 128)
        exec(remote, f'ip netns exec "ns-{id}" olsrd2 "uplink" --load /tmp/olsrd2-{id}.conf')

def stop_olsr2_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x olsrd2 || true')
        exec(remote, f'rm -f /tmp/olsrd2-*.conf')

def stop_olsr2_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]
        exec(remote, f'pkill -SIGKILL -x olsrd2 --nslist ns-{id} || true')
        exec(remote, f'rm -f /tmp/olsrd2-{id}.conf')

def start_ospf_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]

        '''
            The route id can be any 32bit identifier
            as integer or as IPv4 address.
        '''
        digest = hashlib.md5(str.encode(id)).digest()[:4]
        router_id = int.from_bytes(digest, byteorder='little', signed=False)

        # unlikely...
        if router_id == 0:
            router_id = 1

        config = (
            rf'router id {router_id};\n'
            r'\n'
            r'protocol kernel {\n'
            r'  scan time 60;\n'
            r'  import all;\n'
            r'  export all;\n'
            r'}\n'
            r'\n'
            r'protocol ospf v3 {\n'
            r'  area 0 { interface \"uplink\" {}; };\n'
            r'  import all;\n'
            r'  export all;\n'
            r'}\n'
            r'\n'
            r'protocol device {\n'
            r'  scan time 60;\n'
            r'}\n'
        )

        if verbosity == 'verbose':
            address = remote.get('address', 'local')
            print(f'start ospf in {address}/ns-{id}')

        # Create a configuration file
        exec(remote, f'printf "{config}" > /tmp/bird6-ospf-{id}.conf')

        # olsr2 needs the fe80:* address (link local) and a regular IPv6 address (/128 or other)
        interface_down(remote, id, 'uplink')
        interface_up(remote, id, 'uplink')
        set_addr6(remote, id, 'uplink', 128)
        exec(remote, f'ip netns exec "ns-{id}" bird6 -P /tmp/bird6-ospf-{id}.pid -s /tmp/bird6-ospf-{id}.ctl -c /tmp/bird6-ospf-{id}.conf')

def stop_ospf_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x bird6 || true')
        exec(remote, f'rm -f /tmp/bird6-ospf-*.conf')

def stop_ospf_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]
        exec(remote, f'pkill -SIGKILL -x bird6 --nslist ns-{id} || true')
        exec(remote, f'rm -f /tmp/bird6-ospf-{id}.conf')

def start_bmx7_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]

        if verbosity == 'verbose':
            address = remote.get('address', 'local')
            print(f'start bmx7 in {address}/ns-{id}')

        # not sure about the setup
        interface_down(remote, id, 'uplink')
        interface_up(remote, id, 'uplink')
        set_addr6(remote, id, 'uplink', 128)
        exec(remote, f'ip netns exec "ns-{id}" bmx7 --runtimeDir /tmp/bmx7_{id} --nodeRsaKey 6 /keyPath=/tmp/bmx7_{id}/rsa.der --trustedNodesDir=/tmp/bmx7_{id}/trusted dev=uplink')

def stop_bmx7_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x bmx7 || true')
        exec(remote, f'rm -rf /tmp/bmx7-*')

def stop_bmx7_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]
        exec(remote, f'pkill -SIGKILL -x bmx7 --nslist ns-{id} || true')
        exec(remote, f'rm -rf /tmp/bmx7_{id}')

def start_bmx6_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]

        if verbosity == 'verbose':
            address = remote.get('address', 'local')
            print(f'start bmx6 in {address}/ns-{id}')

        # bmx6 only needs the link local fe80:* address
        interface_down(remote, id, 'uplink')
        interface_up(remote, id, 'uplink')
        exec(remote, f'ip netns exec "ns-{id}" bmx6 --runtimeDir /tmp/bmx6_{id} dev=uplink')

def stop_bmx6_instances_all(remotes):
    for remote in remotes:
        exec(remote, f'pkill -SIGKILL -x bmx6 || true')
        exec(remote, f'rm -rf /tmp/bmx6-*')

def stop_bmx6_instances(ids, rmap):
    for id in ids:
        remote = rmap[id]
        exec(remote, f'pkill -SIGKILL -x bmx6 --nslist ns-{id} || true')
        exec(remote, f'rm -rf /tmp/bmx6_{id}')

def start_routing_protocol(protocol, rmap, ids, ignore_error=False):
    beg_count = count_instances(protocol, rmap)
    beg_ms = millis()

    for id in ids:
        remote = rmap[id]
        interface_up(remote, id, 'uplink', ignore_error)

    if protocol == 'babel':
        start_babel_instances(ids, rmap)
    elif protocol == 'batman-adv':
        start_batmanadv_instances(ids, rmap)
    elif protocol == 'bmx6':
        start_bmx6_instances(ids, rmap)
    elif protocol == 'bmx7':
        start_bmx7_instances(ids, rmap)
    elif protocol == 'cjdns':
        start_cjdns_instances(ids, rmap)
    elif protocol == 'olsr1':
        start_olsr1_instances(ids, rmap)
    elif protocol == 'olsr2':
        start_olsr2_instances(ids, rmap)
    elif protocol == 'ospf':
        start_ospf_instances(ids, rmap)
    elif protocol == 'yggdrasil':
        start_yggdrasil_instances(ids, rmap)
    elif protocol == 'none':
        return
    else:
        eprint(f'Error: unknown routing protocol: {protocol}')
        exit(1)

    wait_for_completion()

    # wait for last started process to fork
    # otherwise we might have one extra counted instance
    time.sleep(0.5)

    end_ms = millis()
    end_count = count_instances(protocol, rmap)

    count = end_count - beg_count
    if count != len(ids):
        eprint(f'Error: Failed to start {protocol} instances: {count}/{len(ids)} started')
        stop_all_terminals()
        exit(1)

    if verbosity != 'quiet':
        print('Started {} {} instances in {}'.format(count, protocol, format_duration(end_ms - beg_ms)))

def stop_routing_protocol(protocol, rmap, ids, ignore_error=False):
    beg_count = count_instances(protocol, rmap)
    beg_ms = millis()

    if protocol == 'babel':
        stop_babel_instances(ids, rmap)
    elif protocol == 'batman-adv':
        stop_batmanadv_instances(ids, rmap)
    elif protocol == 'bmx6':
        stop_bmx6_instances(ids, rmap)
    elif protocol == 'bmx7':
        stop_bmx7_instances(ids, rmap)
    elif protocol == 'cjdns':
        stop_cjdns_instances(ids, rmap)
    elif protocol == 'olsr1':
        stop_olsr1_instances(ids, rmap)
    elif protocol == 'olsr2':
        stop_olsr2_instances(ids, rmap)
    elif protocol == 'ospf':
        stop_ospf_instances(ids, rmap)
    elif protocol == 'yggdrasil':
        stop_yggdrasil_instances(ids, rmap)
    elif protocol == 'none':
        pass
    else:
        eprint('Error: unknown routing protocol: {}'.format(protocol))
        exit(1)

    for id in ids:
        remote = rmap[id]
        interface_down(remote, id, 'uplink', ignore_error=ignore_error)

    wait_for_completion()

    # wait for last stopped process to disappear
    # otherwise we might have one extra counted instance
    time.sleep(0.5)

    end_ms = millis()
    end_count = count_instances(protocol, rmap)

    count = beg_count - end_count
    if count != len(ids):
        eprint(f'Error: Failed to stop {protocol} instances: {count}/{len(ids)} left')
        exit(1)

    if not ignore_error and verbosity != 'quiet':
        print('Stopped {} {} instances in {}'.format(len(ids), protocol, format_duration(end_ms - beg_ms)))

def _get_update(to_state, remotes):
    (from_state, rmap) = get_current_state(remotes)

    if to_state == None:
        to_state = {}
    elif isinstance(to_state, str):
        with open(to_state) as file:
            to_state = json.load(file)

    def get_id_set(state):
        nodes = set()

        if state is not None:
            for link in state.get('links', []):
                nodes.add(str(link['source']))
                nodes.add(str(link['target']))

            for node in state.get('nodes', []):
                nodes.add(str(node['id']))

        return nodes

    from_ids = get_id_set(from_state)
    to_ids = get_id_set(to_state)

    a = from_ids.difference(to_ids)
    b = to_ids.difference(from_ids)

    # (old_ids, new_ids)
    return (a, b, rmap)

protocol_choices = ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'ospf', 'yggdrasil', 'none']

def start(protocol, remotes=default_remotes):
    rmap = get_remote_mapping(remotes)
    ids = list(rmap.keys())
    start_routing_protocol(protocol, rmap, ids)

def stop(protocol, remotes=default_remotes):
    rmap = get_remote_mapping(remotes)
    ids = list(rmap.keys())
    stop_routing_protocol(protocol, rmap, ids)

def apply(protocol, to_state = {}, remotes=default_remotes):
    (old_ids, new_ids, rmap) = _get_update(to_state, remotes)

    stop_routing_protocol(protocol, rmap, old_ids)
    start_routing_protocol(protocol, rmap, new_ids)

def clear(remotes=default_remotes):
    stop_babel_instances_all(remotes)
    stop_batmanadv_instances_all(remotes)
    stop_bmx6_instances_all(remotes)
    stop_bmx7_instances_all(remotes)
    stop_cjdns_instances_all(remotes)
    stop_olsr1_instances_all(remotes)
    stop_olsr2_instances_all(remotes)
    stop_ospf_instances_all(remotes)
    stop_yggdrasil_instances_all(remotes)

def run(command, rmap, quiet=False):
    for (id, remote) in rmap.items():
        cmd = command.replace('{name}', id[3:])

        if quiet:
            exec(remote, f'ip netns exec "ns-{id}" {cmd}', get_output=False, ignore_error=True)
        else:
            stdout, stderr, rcode = exec(remote, f'ip netns exec "ns-{id}" {cmd}', get_output=True, ignore_error=True)

            if stdout or stderr:
                print(f'{id}')
                if stdout:
                    print(stdout)
                if stderr:
                    eprint(stderr)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbosity', choices=['verbose', 'normal', 'quiet'], default='normal', help='Set verbosity.')
    parser.add_argument('--remotes', help='Distribute nodes and links on remotes described in the JSON file.')
    parser.set_defaults(to_state=None)

    subparsers = parser.add_subparsers(dest='action', required=True, help='Action')

    parser_start = subparsers.add_parser('start', help='Start protocol daemons in every namespace.')
    parser_start.add_argument('protocol', choices=protocol_choices, help='Routing protocol to start.')
    parser_start.add_argument('to_state', nargs='?', default=None,help='To state')

    parser_stop = subparsers.add_parser('stop', help='Stop protocol daemons in every namespace.')
    parser_stop.add_argument('protocol', choices=protocol_choices, help='Routing protocol to stop.')
    parser_stop.add_argument('to_state', nargs='?', default=None,help='To state')

    parser_change = subparsers.add_parser('apply', help='Stop/Start protocol daemons in every namespace.')
    parser_change.add_argument('protocol', choices=protocol_choices, help='Routing protocol to change.')
    parser_change.add_argument('to_state', nargs='?', default=None, help='To state')

    parser_run = subparsers.add_parser('run', help='Execute any command in every namespace.')
    parser_run.add_argument('command', nargs=argparse.REMAINDER, help='Shell command that is run. {name} is replaced by the nodes name.')
    parser_run.add_argument('--quiet', action='store_true', help='Do not output stdout and stderr.')
    parser_run.add_argument('to_state', nargs='?', default=None, help='To state')

    parser_clear = subparsers.add_parser('clear', help='Stop all routing protocols.')

    args = parser.parse_args()

    if args.remotes:
        with open(args.remotes) as file:
            args.remotes = json.load(file)
    else:
        args.remotes = default_remotes

    check_access(args.remotes)

    verbosity = args.verbosity

    # get nodes that have been added or will be removed
    (old_ids, new_ids, rmap) = _get_update(args.to_state, args.remotes)

    if args.action == 'start':
        if args.to_state:
            start_routing_protocol(args.protocol, rmap, new_ids)
        else:
            all = old_ids.union(new_ids)
            start_routing_protocol(args.protocol, rmap, all)
    elif args.action == 'stop':
        if args.to_state:
            stop_routing_protocol(args.protocol, rmap, old_ids)
        else:
            all = old_ids.union(new_ids)
            stop_routing_protocol(args.protocol, rmap, all)
    elif args.action == 'apply':
        stop_routing_protocol(args.protocol, rmap, old_ids)
        start_routing_protocol(args.protocol, rmap, new_ids)
    elif args.action == 'clear':
        clear(args.remotes)
    elif args.action == 'run':
        run(' '.join(args.command), rmap, args.quiet)
    else:
        eprint('Unknown action: {}'.format(args.action))
        exit(1)

    stop_all_terminals()

if __name__ == "__main__":
    main()
