#!/usr/bin/env python3

import subprocess
import argparse
import hashlib
import random
import time
import math
import json
import sys
import re
import os

from shared import (
    eprint, exec, default_remotes, convert_to_neighbors, check_access,
    stop_all_terminals, format_duration, millis, wait_for_completion,
    get_current_state, link_id, Remote
)

disable_arp = False
disable_multicast = False
verbosity = 'normal'
mtu = 1500


# deterministic link id
def link_num(source, target, min, max):
    array = str.encode(link_id(source, target))
    digest = hashlib.md5(array).digest()[:8]
    n = int.from_bytes(digest, byteorder='little', signed=False)
    return int(min + ((float(n - 0) / float(2**64)) * (max - min)))

def configure_interface(remote, nsname, ifname):
    # up interface
    exec(remote, f'ip netns exec "{nsname}" ip link set dev "{ifname}" up mtu {mtu}')

    # disable arp / multicast
    # we do not want the OS to send packets on its own,
    # but many mesh protocols need arp/multicast on each link to work
    if disable_arp:
        exec(remote, f'ip netns exec "{nsname}" ip link set dev "{ifname}" arp off')

    if disable_multicast:
        exec(remote, f'ip netns exec "{nsname}" ip link set dev "{ifname}" multicast off')

def get_filtered_link(link, direction):
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
    link = get_filtered_link(link, direction)

    if not isinstance(command, str):
        # threat as lambda
        return command(link, ifname)
    else:
        command = command.replace('{{ifname}}', ifname)
        for key, value in node.items():
            command = command.replace(f'{{key}}', str(value))

        return command

def format_node_command(command, node):
    if not isinstance(command, str):
        # threat as lambda
        return command(node, 'uplink')
    else:
        command = command.replace('{{ifname}}', 'uplink')
        for key, value in node.items():
            command = command.replace(f'{{key}}', str(value))

        return command

def remove_node(node, rmap={}):
    name = str(node['id'])
    remote = rmap.get(name)

    # remove veth pair upname/downname (removes both)
    exec(remote, f'ip netns exec "switch" ip link delete "dl-{name}"')

    # remove bridge (assume that it does not have an interfaces anymore)
    exec(remote, f'ip netns exec "switch" ip link delete "br-{name}" type bridge')

    # remove network namespace
    exec(remote, f'ip netns del "ns-{name}"')

def create_node(node, node_command=None, rmap={}):
    name = str(node['id'])
    remote = rmap.get(name)

    nsname = f'ns-{name}'
    brname = f'br-{name}'
    upname = 'uplink'
    downname = f'dl-{name}'

    exec(remote, f'ip netns add "{nsname}"')

    # up localhost
    exec(remote, f'ip netns exec "{nsname}" ip link set dev "lo" up')

    # create bridge
    exec(remote, f'ip netns exec "switch" ip link add name "{brname}" type bridge')
    configure_interface(remote, "switch", brname)

    # Disable spanning tree protocol (should be off by default anyway)
    exec(remote, f'ip netns exec "switch" ip link set "{brname}" type bridge stp_state 0')

    # Make the bridge to act as a hub
    exec(remote, f'ip netns exec "switch" ip link set "{brname}" type bridge ageing_time 0')
    exec(remote, f'ip netns exec "switch" ip link set "{brname}" type bridge forward_delay 0')

    # create interface pair in switch namespace
    exec(remote, f'ip netns exec "switch" ip link add name "{upname}" type veth peer name "{downname}"')

    # move uplink from namespace 'switch' into the nodes namespace
    exec(remote, f'ip netns exec "switch" ip link set "{upname}" netns "{nsname}"')

    # put uplinkport into bridge
    exec(remote, f'ip netns exec "switch" ip link set "{downname}" master "{brname}"')

    configure_interface(remote, 'switch', downname)
    configure_interface(remote, nsname, upname)

    exec(remote, f'ip netns exec "ns-{name}" sysctl -w net.ipv6.conf.{upname}.hop_limit=255')
    exec(remote, f'ip netns exec "ns-{name}" sysctl -w net.ipv6.conf.default.hop_limit=255')
    exec(remote, f'ip netns exec "ns-{name}" sysctl -w net.ipv4.ip_default_ttl=255')

    if node_command is not None:
        exec(remote, f'ip netns exec "ns-{name}" {format_node_command(node_command, node)}')

def update_node(node, node_command=None, rmap={}):
    name = str(node['id'])
    remote = rmap.get(name)

    if verbosity == 'normal':
        print(f'  update node {name}')

    if node_command is not None:
        exec(remote, f'ip netns exec "ns-{name}" {format_node_command(node_command, node)}')

def remove_link(link, rmap={}):
    source = str(link['source'])
    target = str(link['target'])
    remote1 = rmap.get(source)
    remote2 = rmap.get(target)

    ifname1 = f've-{source}-{target}'
    ifname2 = f've-{target}-{source}'

    if source == target:
        eprint(f'Warning: Cannot remove link with identical source ({source}) and target ({target}) => ignore')
        return

    if remote1 == remote2:
        exec(remote1, f'ip netns exec "switch" ip link del "{ifname1}" type veth peer name "{ifname2}"')
    else:
        # multiple remotes always have address set
        addr1 = remote1.address
        addr2 = remote2.address

        # ids do not have to be the same on both remotes - but it is simpler that way
        tunnel_id = link_num(addr1, addr2, min=1, max=2**32)
        session_id = link_num(source, target, min=1, max=2**32)

        exec(remote1, f'ip l2tp del session tunnel_id {tunnel_id} session_id {session_id}')
        if l2tp_session_count(remote1, tunnel_id) == 0:
            exec(remote1, f'ip l2tp del tunnel tunnel_id {tunnel_id}')

        exec(remote2, f'ip l2tp del session tunnel_id {tunnel_id} session_id {session_id}')
        if l2tp_session_count(remote2, tunnel_id) == 0:
            exec(remote2, f'ip l2tp del tunnel tunnel_id {tunnel_id}')

def update_link(link, link_command=None, rmap={}):
    source = str(link['source'])
    target = str(link['target'])
    remote1 = rmap.get(source)
    remote2 = rmap.get(target)

    ifname1 = f've-{source}-{target}'
    ifname2 = f've-{target}-{source}'

    if source == target:
        eprint(f'Warning: Cannot update link with identical source ({source}) and target ({target}) => ignore')
        return

    if link_command is not None:
        # source -> target
        exec(remote1, 'ip netns exec "switch" ' + format_link_command(link_command, link, 'source', ifname1))
        # target -> source
        exec(remote2, 'ip netns exec "switch" ' + format_link_command(link_command, link, 'target', ifname2))

def l2tp_session_count(remote, tunnel_id):
    return int(exec(remote, f'ip l2tp show session | grep -c "tunnel {tunnel_id}" || true', get_output=True)[0])

def l2tp_tunnel_exists(remote, tunnel_id):
    return int(exec(remote, f'ip l2tp show tunnel | grep -c "Tunnel {tunnel_id}" || true', get_output=True)[0]) != 0

def create_link(link, link_command=None, rmap={}):
    source = str(link['source'])
    target = str(link['target'])
    remote1 = rmap.get(source)
    remote2 = rmap.get(target)

    ifname1 = f've-{source}-{target}'
    ifname2 = f've-{target}-{source}'
    brname1 = f'br-{source}'
    brname2 = f'br-{target}'

    if source == target:
        eprint(f'Warning: Cannot create link with identical source ({source}) and target ({target}) => ignore')
        return

    if remote1 == remote2:
        # create veth interface pair
        exec(remote1, f'ip netns exec "switch" ip link add "{ifname1}" type veth peer name "{ifname2}"')
    else:
        # create l2tp connection
        addr1 = remote1.address
        addr2 = remote2.address

        # ids and port do not have to be the same on both remotes - but it is simpler that way
        tunnel_id = link_num(addr1, addr2, min=1, max=2**32)
        session_id = link_num(source, target, min=1, max=2**32)
        port = link_num(addr1, addr2, min=1024, max=2**16)

        if not l2tp_tunnel_exists(remote1, tunnel_id):
            exec(remote1, f'ip l2tp add tunnel tunnel_id {tunnel_id} peer_tunnel_id {tunnel_id} encap udp local {addr1} remote {addr2} udp_sport {port} udp_dport {port}')
        exec(remote1, f'ip l2tp add session name {ifname1} tunnel_id {tunnel_id} session_id {session_id} peer_session_id {session_id}')
        exec(remote1, f'ip link set "{ifname1}" netns "switch"')

        if not l2tp_tunnel_exists(remote2, tunnel_id):
            exec(remote2, f'ip l2tp add tunnel tunnel_id {tunnel_id} peer_tunnel_id {tunnel_id} encap udp local {addr2} remote {addr1} udp_sport {port} udp_dport {port}')
        exec(remote2, f'ip l2tp add session name {ifname2} tunnel_id {tunnel_id} session_id {session_id} peer_session_id {session_id}')
        exec(remote2, f'ip link set "{ifname2}" netns "switch"')

    configure_interface(remote1, 'switch', ifname1)
    configure_interface(remote2, 'switch', ifname2)

    # put into bridge
    exec(remote1, f'ip netns exec "switch" ip link set "{ifname1}" master "{brname1}"')
    exec(remote2, f'ip netns exec "switch" ip link set "{ifname2}" master "{brname2}"')

    # isolate interfaces (they can only speak to the downlink interface in the bridge they are)
    exec(remote1, f'ip netns exec "switch" bridge link set dev "{ifname1}" isolated on')
    exec(remote2, f'ip netns exec "switch" bridge link set dev "{ifname2}" isolated on')

    # e.g. execute tc command on link
    if link_command is not None:
        # source -> target
        exec(remote1, 'ip netns exec "switch" ' + format_link_command(link_command, link, 'source', ifname1))
        # target -> source
        exec(remote2, 'ip netns exec "switch" ' + format_link_command(link_command, link, 'target', ifname2))

class _Task:
    def __init__(self):
        self.links_create = []
        self.links_update = []
        self.links_remove = []
        self.nodes_create = []
        self.nodes_update = []
        self.nodes_remove = []

def _process_json(json_data):
    # in reality, only '@', ':', '/' and whitespace should cause problems
    name_re = re.compile(r'^[\w-]{1,6}$')
    links = {}
    nodes = {}

    for node in json_data.get('nodes', []):
        name = str(node['id'])
        if not name_re.match(name):
            eprint(f'Invalid node name: {name}')
            stop_all_terminals()
            exit(1)

        nodes[name] = node

    for link in json_data.get('links', []):
        source = str(link['source'])
        target = str(link['target'])

        if len(source) > 6:
            eprint(f'Node name too long: {source}')
            stop_all_terminals()
            exit(1)

        if len(target) > 6:
            eprint(f'Node name too long: {target}')
            stop_all_terminals()
            exit(1)

        if source not in nodes:
            nodes[source] = {'id': source}

        if target not in nodes:
            nodes[target] = {'id': target}

        if source > target:
            links[f'{source}-{target}'] = link
        else:
            links[f'{target}-{source}'] = link

    return (links, nodes)

'''
Decide what nodex/links need to be changed
'''
def _get_task(old_state, new_state):
    (links_old, nodes_old) = _process_json(old_state)
    (links_new, nodes_new) = _process_json(new_state)

    # if some property (e.g. for tc) has changed
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

def show(remotes=default_remotes):
    check_access(remotes)

    for remote_id, remote in enumerate(remotes):
        nodes = exec(remote, 'ip netns list', get_output=True)[0].count('ns-')
        veth = int(exec(remote, 'ip netns exec switch ip addr list | grep -c "@ve-" || true', get_output=True)[0]) // 2
        l2tp = int(exec(remote, 'ip l2tp show session | grep -c "ve-" || true', get_output=True)[0])
        label = remote.address or 'local'
        print(f'{label}: {nodes} nodes, {veth} veth links, {l2tp} l2tp links')

def clear(remotes=default_remotes):
    check_access(remotes)

    for remote in remotes:
        exec(remote, 'ip -all netns delete || true')
        # removal of all l2tp tunnels - removes all sessions as well
        exec(remote, 'ip l2tp show tunnel | grep Tunnel | tr "," " " | cut -d" " -f2 | xargs -r -n1 ip l2tp del tunnel tunnel_id')

'''
Get a dict to map nodes to remote computers
'''
def _get_remote_mapping(cur_state, new_state, remotes, cur_state_rmap):
    def partition_into_subgraph_nodes(neighbor_map, nodes, rmap, remotes):
        random.shuffle(nodes)
        # remote_id => [<node_ids>]
        partitions = {}

        # keep running nodes on the same partition
        for node_id, remote in rmap.items():
            remote_id = remotes.index(remote)
            partitions.setdefault(remote_id, []).append(node_id)
            if node_id not in nodes:
                eprint(f'Node {node_id} not in previous state!')
                stop_all_terminals()
                exit(1)
            nodes.remove(node_id)

        for remote_id in range(len(remotes)):
            if len(nodes) == 0:
                break
            if remote_id not in partitions:
                partitions[remote_id] = [nodes.pop()]

        # find neighbor node of cluster
        def grow_cluster(cluster, nodes):
            for node in nodes:
                for cluster_node in cluster:
                    if node in neighbor_map[cluster_node]:
                        cluster.append(node)
                        nodes.remove(node)
                        return
            # cannot extend cluster via neighbor => use left over node
            cluster.append(nodes.pop())

        while len(nodes) > 0:
            # get smallest cluster (remote) key
            key = min(partitions.keys(), key=lambda k: len(partitions[k]))
            grow_cluster(partitions[key], nodes)

        return partitions

    # get node distribution balance
    def get_variance(partition):
        median = 0
        for remote_id, cluster in partition.items():
            median += len(cluster)
        median /= len(partition)

        q = 0
        for remote_id, cluster in partition.items():
            q = (len(cluster) - median) ** 2

        return math.sqrt(q / len(partition))

    def partition_to_map(partition, remotes):
        node_to_remote_map = {}
        for remote_id, node_ids in partition.items():
            for node_id in node_ids:
                node_to_remote_map[node_id] = remotes[remote_id]
        return node_to_remote_map

    '''
    # debug output
    def debug_partition(partition, remotes):
        print('partitioning:')

        for remote_id, cluster in partition.items():
            print('  {}: {} nodes'.format(remotes[remote_id].get('address', 'local'), len(cluster)))

        interconnects = 0
        node_to_remote_map = partition_to_map(partition, remotes)
        for link in new_state.get('links', []):
            if node_to_remote_map[str(link['source'])] is not node_to_remote_map[str(link['target'])]:
                interconnects += 1
        print(f'  l2tp links: {interconnects}')
    '''

    # try multiple random (connected) partitions and select the best
    neighbor_map = convert_to_neighbors(cur_state, new_state)
    tries = 20
    lowest_variance = math.inf
    best_partition = []

    # shortcut: if no mapping on multiple remotes is needed
    if len(remotes) == 1 and len(cur_state_rmap) == 0:
        return partition_to_map({0: neighbor_map.keys()}, remotes)

    for _ in range(tries):
        partition = partition_into_subgraph_nodes(neighbor_map, list(neighbor_map.keys()), cur_state_rmap, remotes)
        if partition:
            variance = get_variance(partition)
            if variance < lowest_variance:
                lowest_variance = variance
                best_partition = partition

    if len(best_partition) == 0:
        eprint('No network partition found.')
        stop_all_terminals()
        exit(1)

    #if verbosity in ['verbose', 'normal']:
    #    debug_partition(best_partition, remotes)

    # node_id => remote
    return partition_to_map(best_partition, remotes)

def state_empty(state):
    return (len(state.get('links', []))) == 0 and (len(state.get('nodes', [])) == 0)

def apply(state={}, node_command=None, link_command=None, remotes=default_remotes):
    check_access(remotes)

    new_state = state
    (cur_state, cur_state_rmap) = get_current_state(remotes)

    # handle different new_state types
    if isinstance(new_state, str):
        if new_state == 'none':
            new_state = {}
        else:
            if not os.path.isfile(new_state):
                eprint(f'File not found: {new_state}')
                stop_all_terminals()
                exit(1)

            with open(new_state) as file:
                new_state = json.load(file)

    # map each node to a remote or local computer
    # distribute evenly with minimized interconnects
    rmap = _get_remote_mapping(cur_state, new_state, remotes, cur_state_rmap)
    data = _get_task(cur_state, new_state)

    beg_ms = millis()

    # add "switch" namespace
    if state_empty(cur_state):
        for remote in remotes:
            # add switch if it does not exist yet
            exec(remote, 'ip netns add "switch" || true')
            # disable IPv6 in switch namespace (no need, less overhead)
            exec(remote, 'ip netns exec "switch" sysctl -q -w net.ipv6.conf.all.disable_ipv6=1')

    for node in data.nodes_update:
        update_node(node, node_command, rmap)

    for link in data.links_update:
        update_link(link, link_command, rmap)

    for node in data.nodes_create:
        create_node(node, node_command, rmap)

    for link in data.links_create:
        create_link(link, link_command, rmap)

    for link in data.links_remove:
        remove_link(link, rmap)

    for node in data.nodes_remove:
        remove_node(node, rmap)

    # remove "switch" namespace
    if state_empty(new_state):
        for remote in remotes:
            exec(remote, 'ip netns del "switch" || true')

    # wait for tasks to complete
    wait_for_completion()
    end_ms = millis()

    if verbosity != 'quiet':
        print('Network setup in {}:'.format(format_duration(end_ms - beg_ms)))
        print(f'  nodes: {len(data.nodes_create)} created, {len(data.nodes_remove)} removed, {len(data.nodes_update)} updated')
        print(f'  links: {len(data.links_create)} created, {len(data.links_remove)} removed, {len(data.links_update)} updated')

    return new_state


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Create a virtual network based on linux network names and virtual network interfaces:\n ./network.py change none test.json')

    parser.add_argument('--verbosity', choices=['verbose', 'normal', 'quiet'], default='normal', help='Set verbosity.')
    parser.add_argument('--link-command', help='Execute a command to change link properties. JSON elements are accessible. E.g. "myscript.sh {ifname} {tq}"')
    parser.add_argument('--node-command', help='Execute a command to change link properties. JSON elements are accessible. E.g. "myscript.sh {ifname} {id}"')
    parser.add_argument('--disable-arp', action='store_true', help='Disable ARP support on each interface.')
    parser.add_argument('--disable-multicast', action='store_true', help='Disable Multicast support each interface.')
    parser.add_argument('--remotes', help='Distribute nodes and links on remotes described in the JSON file.')
    parser.add_argument('--mtu', type=int, default=1500, help='Set Maximum Transfer Unit (MTU) on each interface.')

    subparsers = parser.add_subparsers(dest='action', required=True)

    parser_change = subparsers.add_parser('apply', help='Create or change a virtual network.')
    parser_change.add_argument('new_state', help='JSON file that describes the target topology. Use "none" to remove all network namespaces.')
    subparsers.add_parser('show', help='List all Linux network namespaces. Namespace "switch" is the special cable cabinet namespace.')
    subparsers.add_parser('clear', help='Remove all Linux network namespaces. Processes still might need to be killed.')

    args = parser.parse_args()

    global disable_arp
    global disable_multicast
    global verbosity
    global mtu

    disable_arp = args.disable_arp
    disable_multicast = args.disable_multicast
    verbosity = args.verbosity
    mtu = args.mtu

    if args.remotes:
        if not os.path.isfile(args.remotes):
            eprint(f'File not found: {args.remotes}')
            stop_all_terminals()
            exit(1)

        with open(args.remotes) as file:
            args.remotes = [Remote.from_json(obj) for obj in json.load(file)]
    else:
        args.remotes = default_remotes

    if args.action == 'clear':
        clear(args.remotes)
    elif args.action == 'show':
        show(args.remotes)
    elif args.action == 'apply':
        apply(args.new_state, args.node_command, args.link_command, args.remotes)
    else:
        eprint(f'Invalid command: {args.action}')
        exit(1)
    stop_all_terminals()

if __name__ == "__main__":
    main()
