#!/usr/bin/env python3

import argparse
import time
import json
import sys
import os

block_arp = False
block_multicast = False
verbose = False

def eprint(s):
    sys.stderr.write(s + '\n')

def exec(cmd):
    rc = os.system(cmd)
    if rc != 0:
        eprint('Abort, command failed: {}'.format(cmd))
        eprint('Network might be in an undefined state!')
        exit(1)

def configure_interface(nsname, ifname):
    # up interface
    exec('ip netns exec "{}" ip link set dev "{}" up'.format(nsname, ifname))

    # disable arp / multicast
    # we do not want the OS to send packets on its own,
    # but many mesh protocols need arp/multicast on each link to work
    if block_arp:
        exec('ip netns exec "{}" ip link set dev "{}" arp off'.format(nsname, ifname))

    if block_multicast:
        exec('ip netns exec "{}" ip link set dev "{}" multicast off'.format(nsname, ifname))

def remove_node(node):
    name = node.name
    if verbose:
        print('  remove node {}'.format(name))

    nsname = 'ns-{}'.format(name)
    brname = 'br-{}'.format(name)
    downname = 'dl-{}'.format(name)

    # remove veth pair upname/downname (removes both)
    exec('ip netns exec "switch" ip link delete "{}"'.format(downname))

    # remove bridge (assume that it does not have an interfaces anymore)
    exec('ip netns exec "switch" ip link delete "{}" type bridge'.format(brname))

    # remove network namespace
    exec('ip netns del "{}"'.format(nsname))

def create_node(node):
    name = node.name
    if verbose:
        print('  create node {}'.format(name))

    nsname = 'ns-{}'.format(name)
    brname = 'br-{}'.format(name)
    upname = 'uplink'
    downname = 'dl-{}'.format(name)

    exec('ip netns add "{}"'.format(nsname))

    # up localhost
    exec('ip netns exec "{}" ip link set dev "lo" up'.format(nsname))

    # create bridge
    exec('ip netns exec "switch" ip link add name "{}" type bridge'.format(brname))
    configure_interface("switch", brname)

    # Disable STP (should be off by default anyway)
    exec('ip netns exec "switch" ip link set "{}" type bridge stp_state 0'.format(brname))

    # Make the bridge to act as a hub
    exec('ip netns exec "switch" ip link set "{}" type bridge ageing_time 0'.format(brname))
    exec('ip netns exec "switch" ip link set "{}" type bridge forward_delay 0'.format(brname))

    # create interface pair in switch namespace
    exec('ip netns exec "switch" ip link add name "{}" type veth peer name "{}"'.format(upname, downname))

    # move uplink from namespace 'switch' into the nodes namespace
    exec('ip netns exec "switch" ip link set "{}" netns "{}"'.format(upname, nsname))

    # put uplinkport into bridge
    exec('ip netns exec "switch" ip link set "{}" master "{}"'.format(downname, brname))

    configure_interface("switch", downname)
    configure_interface(nsname, upname)

def remove_link(link):
    if verbose:
        print('  remove link {} <-> {}'.format(link.source, link.target))

    ifname1 = 've-{}-{}'.format(link.source, link.target)
    ifname2 = 've-{}-{}'.format(link.target, link.source)

    exec('ip netns exec "switch" ip link del "{}" type veth peer name "{}"'.format(ifname1, ifname2))

def update_link(link):
    if verbose:
        print('  update link {} <-> {}'.format(link.source, link.target))

    ifname1 = 've-{}-{}'.format(link.source, link.target)
    ifname2 = 've-{}-{}'.format(link.target, link.source)

    # source -> target
    if link.source_tc:
        exec('ip netns exec "switch" tc qdisc replace dev "{}" root {}'.format(ifname1, link.source_tc))

    # target -> source
    if link.target_tc:
        exec('ip netns exec "switch" tc qdisc replace dev "{}" root {}'.format(ifname2, link.target_tc))

def create_link(link):
    if verbose:
        print('  create link {} <-> {}'.format(link.source, link.target))

    nsname1 = 'ns-{}'.format(link.source)
    nsname2 = 'ns-{}'.format(link.target)
    ifname1 = 've-{}-{}'.format(link.source, link.target)
    ifname2 = 've-{}-{}'.format(link.target, link.source)

    br1name = 'br-{}'.format(link.source)
    br2name = 'br-{}'.format(link.target)

    # create pair of interfaces
    exec('ip netns exec "switch" ip link add "{}" type veth peer name "{}"'.format(ifname1, ifname2))

    configure_interface('switch', ifname1)
    configure_interface('switch', ifname2)

    # put into bridge
    exec('ip netns exec "switch" ip link set "{}" master "{}"'.format(ifname2, br2name))
    exec('ip netns exec "switch" ip link set "{}" master "{}"'.format(ifname1, br1name))

    # isolate interfaces (they can only speak to the downlink interface in the bridge they are)
    exec('ip netns exec "switch" bridge link set dev "{}" isolated on'.format(ifname1))
    exec('ip netns exec "switch" bridge link set dev "{}" isolated on'.format(ifname2))

    # source -> target
    if link.source_tc:
        exec('ip netns exec "switch" tc qdisc replace dev "{}" root {}'.format(ifname1, link.source_tc))

    # target -> source
    if link.target_tc:
        exec('ip netns exec "switch" tc qdisc replace dev "{}" root {}'.format(ifname2, link.target_tc))

class Link:
    def __init__(self, source, target, source_tc, target_tc):
        self.source = source
        self.target = target
        self.source_tc = source_tc
        self.target_tc = target_tc

    def cmp_tc(link):
        return self.source_tc == link.source_tc and self.target_tc == link.target_tc

class Node:
    def __init__(self, name):
        self.name = name

class _Task:
    def __init__(self):
        self.links_create = []
        self.links_update = []
        self.links_remove = []
        self.nodes_create = []
        self.nodes_remove = []

def _process_json(json_data, force_tc = None):
    links = {}
    nodes = {}

    for node in json_data.get('nodes', []):
        name = str(node['id'])
        if len(name) > 6:
            eprint('Node name too long: {}'.format(name))
            exit(1)

        nodes[name] = Node(name)

    for link in json_data.get('links', []):
        source = str(link['source'])
        target = str(link['target'])
        source_tc = link.get('source_tc')
        target_tc = link.get('target_tc')

        if force_tc is not None:
            source_tc = force_tc
            target_tc = force_tc

        if len(source) > 6:
            eprint('Node name too long: {}'.format(source))
            exit(1)

        if len(target) > 6:
            eprint('Node name too long: {}'.format(target))
            exit(1)

        if source not in nodes:
            nodes[source] = Node(source)

        if target not in nodes:
            nodes[target] = Node(target)

        if source > target:
            links[source + '_' + target] = Link(source, target, source_tc, target_tc)
        else:
            links[target + '_' + source] = Link(target, source, target_tc, source_tc)

    return (links, nodes)

def _get_task(old_state, new_state, force_tc=None):
    (links_old, nodes_old) = _process_json(old_state, force_tc)
    (links_new, nodes_new) = _process_json(new_state, force_tc)

    def tc_equal(link1, link2):
        return (link1.source_tc == link2.source_tc) and (link1.target_tc == link2.target_tc)

    task = _Task()

    for key in links_new:
        if not key in links_old:
            task.links_create.append(links_new[key])

    for key in links_old:
        if key not in links_new:
            task.links_remove.append(links_old[key])

    for key in links_new:
        if key in links_old:
            new = links_new[key]
            old = links_old[key]
            if not tc_equal(new, old):
                task.links_update.append(new)

    for key in nodes_old:
        if key not in nodes_new:
            task.nodes_remove.append(nodes_old[key])

    for key in nodes_new:
        if key not in nodes_old:
            task.nodes_create.append(nodes_new[key])

    return task

def clear():
    os.system('ip -all netns delete')

def change(from_state={}, to_state={}, force_tc=None):
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

    data = _get_task(from_state, to_state, force_tc)

    # add "switch" namespace
    if len(from_state) == 0:
        if verbose:
            print('  create "switch"')
        # add switch if it does not exist yet
        exec('ip netns add "switch" || true')
        # disable IPv6 in switch namespace (no need, less overhead)
        exec('ip netns exec "switch" sysctl -q -w net.ipv6.conf.all.disable_ipv6=1')

    for link in data.links_update:
        update_link(link)

    for node in data.nodes_create:
        create_node(node)

    for link in data.links_create:
        create_link(link)

    for link in data.links_remove:
        remove_link(link)

    for node in data.nodes_remove:
        remove_node(node)

    # remove "switch" namespace
    if len(to_state) == 0:
        if verbose:
            print('  remove "switch"')
        exec('ip netns del "switch" || true')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Create a virtual network based on linux network names and virtual network interfaces:\n ./network.py change none test.json')
    parser.set_defaults(from_state='none', to_state='none')

    parser.add_argument('--verbose', action='store_true', help='Verbose execution.')
    parser.add_argument('--force-tc', help='Overwrite source_tc/target_tc (traffic control) parameters from JSON.')
    parser.add_argument('--block-arp', action='store_true', help='Block ARP packets.')
    parser.add_argument('--block-multicast', action='store_true', help='Block multicast packets.')

    subparsers = parser.add_subparsers(dest='action', required=True)

    parser_change = subparsers.add_parser('change', help='Create or change a virtual network.')
    parser_change.add_argument('from_state', help='JSON file that describes the current topology. Use "none" if no namespace network exists.')
    parser_change.add_argument('to_state', help='JSON file that describes the target topology. Use "none" to remove all network namespaces.')
    subparsers.add_parser('list', help='List all Linux network namespaces. Namespace "switch" is the special cable cabinet namespace.')
    subparsers.add_parser('clear', help='Remove all Linux network namespaces. Processes still might need to be killed.')

    args = parser.parse_args()

    block_arp = args.block_arp
    block_multicast = args.block_multicast
    verbose = args.verbose

    if os.geteuid() != 0:
        eprint('Need to run as root.')
        exit(1)

    if args.action == 'clear':
        clear()
    elif args.action == 'list':
        os.system('ip netns list')
    elif args.action == 'change':
        change(args.from_state, args.to_state, args.force_tc)
    else:
        eprint('Invalid command: {}'.format(args.action))
        exit(1)
