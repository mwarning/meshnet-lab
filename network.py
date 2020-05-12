#!/usr/bin/env python3

import argparse
import time
import json
import sys
import os

block_arp = False
block_multicast = False
verbosity = 'normal'

def eprint(s):
    sys.stderr.write(s + '\n')

def exec(cmd):
    rc = os.system(cmd)
    if rc != 0:
        eprint(f'Abort, command failed: {cmd}')
        eprint('Network might be in an undefined state!')
        exit(1)

def configure_interface(nsname, ifname):
    # up interface
    exec(f'ip netns exec "{nsname}" ip link set dev "{ifname}" up')

    # disable arp / multicast
    # we do not want the OS to send packets on its own,
    # but many mesh protocols need arp/multicast on each link to work
    if block_arp:
        exec(f'ip netns exec "{nsname}" ip link set dev "{ifname}" arp off')

    if block_multicast:
        exec(f'ip netns exec "{nsname}" ip link set dev "{ifname}" multicast off')

def split_link_obj(link, direction):
    obj = {}
    for key, value in link.items():
        if key == 'source' or key == 'target':
            continue

        if direction == 'source':
            if key.startswith('source_'):
                obj[key[7:]] = value
            elif key.startswith('target_'):
                continue
            else:
                obj[key] = value

        if direction == 'target':
            if key.startswith('target_'):
                obj[key[7:]] = value
            elif key.startswith('source_'):
                continue
            else:
                obj[key] = value
    return obj

def format_link_command(command, link, direction, ifname):
    link = split_link_obj(link, direction)

    if not isinstance(command, str):
        # threat as lambda
        return command(link, ifname)
    else:
        command = command.replace('{{ifname}}', ifname)
        for key, value in node.items():
            command = command.replace('{{{}}}'.format(key), str(value))

        return command

def format_node_command(command, node):
    if not isinstance(command, str):
        # threat as lambda
        return command(node, 'uplink')
    else:
        command = command.replace('{{ifname}}', 'uplink')
        for key, value in node.items():
            command = command.replace('{{{}}}'.format(key), str(value))

        return command

def remove_node(node):
    name = str(node['id'])

    if verbosity == 'verbose':
        print(f'  remove node {name}')

    # remove veth pair upname/downname (removes both)
    exec(f'ip netns exec "switch" ip link delete "dl-{name}"')

    # remove bridge (assume that it does not have an interfaces anymore)
    exec(f'ip netns exec "switch" ip link delete "br-{name}" type bridge')

    # remove network namespace
    exec(f'ip netns del "ns-{name}"')

def create_node(node, node_command):
    name = str(node['id'])

    if verbosity == 'verbose':
        print('  create node {}'.format(name))

    nsname = f'ns-{name}'
    brname = f'br-{name}'
    upname = 'uplink'
    downname = f'dl-{name}'

    exec(f'ip netns add "{nsname}"')

    # up localhost
    exec(f'ip netns exec "{nsname}" ip link set dev "lo" up')

    # create bridge
    exec(f'ip netns exec "switch" ip link add name "{brname}" type bridge')
    configure_interface("switch", brname)

    # Disable STP (should be off by default anyway)
    exec(f'ip netns exec "switch" ip link set "{brname}" type bridge stp_state 0')

    # Make the bridge to act as a hub
    exec(f'ip netns exec "switch" ip link set "{brname}" type bridge ageing_time 0')
    exec(f'ip netns exec "switch" ip link set "{brname}" type bridge forward_delay 0')

    # create interface pair in switch namespace
    exec(f'ip netns exec "switch" ip link add name "{upname}" type veth peer name "{downname}"')

    # move uplink from namespace 'switch' into the nodes namespace
    exec(f'ip netns exec "switch" ip link set "{upname}" netns "{nsname}"')

    # put uplinkport into bridge
    exec(f'ip netns exec "switch" ip link set "{downname}" master "{brname}"')

    configure_interface('switch', downname)
    configure_interface(nsname, upname)

    if node_command is not None:
        exec(f'ip netns exec "ns-{name}" ' + format_node_command(node_command, node))

def update_node(node, node_command=None):
    name = str(node['id'])

    if verbosity == 'verbose':
        print(f'  update node {name}')

    if node_command is not None:
        exec(f'ip netns exec "ns-{name}" ' + format_node_command(node_command, node))

def remove_link(link):
    source = str(link['source'])
    target = str(link['target'])

    if verbosity == 'verbose':
        print(f'  remove link {source} <-> {target}')

    ifname1 = f've-{source}-{target}'
    ifname2 = f've-{target}-{source}'

    exec(f'ip netns exec "switch" ip link del "{ifname1}" type veth peer name "{ifname2}"')

def update_link(link, link_command=None):
    source = str(link['source'])
    target = str(link['target'])

    if verbosity == 'verbose':
        print(f'  update link {source} <-> {target}')

    ifname1 = f've-{source}-{target}'
    ifname2 = f've-{target}-{source}'

    if link_command is not None:
        # source -> target
        exec('ip netns exec "switch" ' + format_link_command(link_command, link, 'source', ifname1))
        # target -> source
        exec('ip netns exec "switch" ' + format_link_command(link_command, link, 'target', ifname2))

def create_link(link, link_command=None):
    source = str(link['source'])
    target = str(link['target'])

    if verbosity == 'verbose':
        print(f'  create link {source} <-> {target}')

    ifname1 = f've-{source}-{target}'
    ifname2 = f've-{target}-{source}'
    br1name = f'br-{source}'
    br2name = f'br-{target}'

    # create pair of interfaces
    exec(f'ip netns exec "switch" ip link add "{ifname1}" type veth peer name "{ifname2}"')

    configure_interface('switch', ifname1)
    configure_interface('switch', ifname2)

    # put into bridge
    exec(f'ip netns exec "switch" ip link set "{ifname2}" master "{br2name}"')
    exec(f'ip netns exec "switch" ip link set "{ifname1}" master "{br1name}"')

    # isolate interfaces (they can only speak to the downlink interface in the bridge they are)
    exec(f'ip netns exec "switch" bridge link set dev "{ifname1}" isolated on')
    exec(f'ip netns exec "switch" bridge link set dev "{ifname2}" isolated on')

    #link_cmd = lambda (link, name, ifname): 'tc qdisc replace dev "{}" root {}'
    if link_command is not None:
        # source -> target
        exec('ip netns exec "switch" ' + format_link_command(link_command, link, 'source', ifname1))
        # target -> source
        exec('ip netns exec "switch" ' + format_link_command(link_command, link, 'target', ifname2))

class _Task:
    def __init__(self):
        self.links_create = []
        self.links_update = []
        self.links_remove = []
        self.nodes_create = []
        self.nodes_update = []
        self.nodes_remove = []

def _process_json(json_data):
    links = {}
    nodes = {}

    for node in json_data.get('nodes', []):
        name = str(node['id'])
        if len(name) > 6:
            eprint('Node name too long: {}'.format(name))
            exit(1)

        nodes[name] = node

    for link in json_data.get('links', []):
        source = str(link['source'])
        target = str(link['target'])

        if len(source) > 6:
            eprint(f'Node name too long: {source}')
            exit(1)

        if len(target) > 6:
            eprint(f'Node name too long: {target}')
            exit(1)

        if source not in nodes:
            nodes[source] = {'id': source}

        if target not in nodes:
            nodes[target] = {'id': target}

        if source > target:
            links[source + '->' + target] = link
        else:
            links[target + '->' + source] = link

    return (links, nodes)

def _get_task(old_state, new_state):
    (links_old, nodes_old) = _process_json(old_state)
    (links_new, nodes_new) = _process_json(new_state)

    def obj_equal(link1, link2):
        if len(link1) != len(link2):
            return False

        for key1, value1 in link1.items():
            value2 = link2.get(key1)
            if value1 != value2:
                return False

        return True

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
            if not obj_equal(new, old):
                task.links_update.append(new)

    for key in nodes_new:
        if key in nodes_old:
            new = nodes_new[key]
            old = nodes_old[key]
            if not obj_equal(new, old):
                task.nodes_update.append(new)

    for key in nodes_old:
        if key not in nodes_new:
            task.nodes_remove.append(nodes_old[key])

    for key in nodes_new:
        if key not in nodes_old:
            task.nodes_create.append(nodes_new[key])

    return task

def clear():
    os.system('ip -all netns delete')

def change(from_state={}, to_state={}, node_command=None, link_command=None):
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

    data = _get_task(from_state, to_state)

    # add "switch" namespace
    if len(from_state) == 0:
        if verbosity == 'verbose':
            print('  create "switch"')
        # add switch if it does not exist yet
        exec('ip netns add "switch" || true')
        # disable IPv6 in switch namespace (no need, less overhead)
        exec('ip netns exec "switch" sysctl -q -w net.ipv6.conf.all.disable_ipv6=1')

    for node in data.nodes_update:
        update_node(node, node_command)

    for link in data.links_update:
        update_link(link, link_command)

    for node in data.nodes_create:
        create_node(node, node_command)

    for link in data.links_create:
        create_link(link, link_command)

    for link in data.links_remove:
        remove_link(link)

    for node in data.nodes_remove:
        remove_node(node)

    # remove "switch" namespace
    if len(to_state) == 0:
        if verbosity == 'verbose':
            print('  remove "switch"')
        exec('ip netns del "switch" || true')

    return to_state

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Create a virtual network based on linux network names and virtual network interfaces:\n ./network.py change none test.json')
    parser.set_defaults(from_state='none', to_state='none')

    parser.add_argument('--verbosity', choices=['verbose', 'normal', 'quiet'], default='normal', help='Set verbosity.')
    parser.add_argument('--link-command', help='Execute a command to change link properties. JSON elements are accessible. E.g. "myscript.sh {ifname} {tq}"')
    parser.add_argument('--node-command', help='Execute a command to change link properties. JSON elements are accessible. E.g. "myscript.sh {ifname} {id}"')
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
    verbosity = args.verbosity

    if os.geteuid() != 0:
        eprint('Need to run as root.')
        exit(1)

    if args.action == 'clear':
        clear()
    elif args.action == 'list':
        os.system('ip netns list')
    elif args.action == 'change':
        change(args.from_state, args.to_state, args.node_command, args.link_command)
    else:
        eprint('Invalid command: {}'.format(args.action))
        exit(1)
