#!/usr/bin/env python3

import time
import json
import sys
import os

verbose = True

def print_usage(prog_name):
    print((
        'Usage:\n'
        '  {} <from-json-file> <to-json-file>\n'
        '    Change network topology (use "none" as an alias for a file with no links).\n'
        '\n'
        '  {} list\n'
        '    List all network namespaces ("switch" is a special one).\n'
        '\n'
        '  {} cleanup\n'
        '    Remove entire network.\n'
    ).format(prog_name, prog_name, prog_name))

def exec(cmd):
    rc = os.system(cmd)
    if rc != 0:
        print('Abort, command failed: {}'.format(cmd))
        print('Network might be in an undefined state!')
        exit(1)

def configure_interface(nsname, ifname):
    # up interface
    exec('ip netns exec "{}" ip link set dev "{}" up'.format(nsname, ifname))

    # disable arp & multicast (we do not want the OS to send packets on their own)
    exec('ip netns exec "{}" ip link set dev "{}" arp off'.format(nsname, ifname))
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
    if link.source_tc is not None:
        exec('ip netns exec "switch" tc qdisc replace dev "{}" root {}'.format(ifname2, link.source_tc))

    # target -> source
    if link.target_tc is not None:
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
    if link.source_tc is not None:
        exec('ip netns exec "switch" tc qdisc replace dev "{}" root {}'.format(ifname2, link.source_tc))

    # target -> source
    if link.target_tc is not None:
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

class Data:
    def __init__(self):
        self.links_create = []
        self.links_update = []
        self.links_remove = []
        self.nodes_create = []
        self.nodes_remove = []

def parse_json_files(json_data):
    links = {}
    nodes = {}
    for link in json_data['links']:
        source = str(link['source'])
        target = str(link['target'])
        source_tc = link.get('source_tc')
        target_tc = link.get('target_tc')

        if len(source) > 6:
            print('node name too long: {}'.format(source))
            exit(1)

        if len(target) > 6:
            print('node name too long: {}'.format(target))
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

def get_data(arg1, arg2):
    # empty defaults
    old = json.loads('{"links":[]}')
    new = json.loads('{"links":[]}')

    if arg1 != 'none':
        old = json.load(open(arg1))

    if arg2 != 'none':
        new = json.load(open(arg2))

    (links_old, nodes_old) = parse_json_files(old)
    (links_new, nodes_new) = parse_json_files(new)

    data = Data()

    for key in links_new:
        if not key in links_old:
            data.links_create.append(links_new[key])

    for key in links_old:
        if key not in links_new:
            data.links_remove.append(links_old[key])

    for key in links_new:
        if key in links_old:
            new = links_new[key]
            old = links_old[key]
            if not new.cmp_tc(old):
                data.links_update.append(new)

    for key in nodes_old:
        if key not in nodes_new:
            data.nodes_remove.append(nodes_old[key])

    for key in nodes_new:
        if key not in nodes_old:
            data.nodes_create.append(nodes_new[key])

    return data


if os.popen('id -u').read().strip() != '0':
    print('Need to run as root.')
    exit(1)

if len(sys.argv) == 2 and sys.argv[1] == 'cleanup':
    os.system('ip -all netns delete')
    # TODO: kill all programs in network namespaces
elif len(sys.argv) == 2 and sys.argv[1] == 'list':
    os.system('ip netns list')
elif len(sys.argv) == 3:
    data = get_data(sys.argv[1], sys.argv[2])

    # makesure namespace switch exists (contains the entire wiring of the mesh)
    os.system('ip netns add "switch" > /dev/null 2>&1')
    # disable IPv6 in switch namespace (no need, less overhead)
    exec('ip netns exec "switch" sysctl -q -w net.ipv6.conf.all.disable_ipv6=1')

    #print("links_update: {}, links_create: {}, links_remove: {}".format(
    #    len(data.links_update), len(data.links_create), len(data.links_remove)))
    #print("nodes_create: {}, nodes_remove: {}".format(
    #    len(data.nodes_create), len(data.nodes_remove)))

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
else:
    print_usage(sys.argv[0])
    exit(1)
