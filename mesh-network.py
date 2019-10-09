#!/usr/bin/env python3

import time
import json
import sys
import os


nodes = {}

def exec(cmd):
    rc = os.system(cmd)
    if rc != 0:
        print('Abort, command failed: {}'.format(cmd))
        os.system('ip -all netns delete')
        print('Cleanup done')
        exit(1)

def configure_interface(nsname, ifname):
    # up interface
    exec('ip netns exec "{}" ip link set dev "{}" up'.format(nsname, ifname))

    # disable arp & multicast (we do not want the OS to send packets on their own)
    exec('ip netns exec "{}" ip link set dev "{}" arp off'.format(nsname, ifname))
    exec('ip netns exec "{}" ip link set dev "{}" multicast off'.format(nsname, ifname))

def create_node(name):
    print("  create node {}".format(name))

    nsname = 'ns-{}'.format(name)
    brname = "br-{}".format(name)
    upname = "uplink"
    downname = "dl-{}".format(name)

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


def create_link(source, target, source_tc, target_tc):
    print("  create link {} <=> {}".format(source, target))

    if source not in nodes:
        create_node(source)
        nodes[source] = len(nodes)

    if target not in nodes:
        create_node(target)
        nodes[target] = len(nodes)

    # use numbers to shorten interface names
    id1 = nodes[source]
    id2 = nodes[target]
    nsname1 = "ns-{}".format(source)
    nsname2 = "ns-{}".format(target)
    ifname1 = "veth-{}-{}".format(id1, id2)
    ifname2 = "veth-{}-{}".format(id2, id1)

    br1name = "br-{}".format(source)
    br2name = "br-{}".format(target)

    # create pair of interfaces
    exec('ip netns exec "switch" ip link add "{}" type veth peer name "{}"'.format(ifname1, ifname2))

    configure_interface("switch", ifname1)
    configure_interface("switch", ifname2)

    # put into bridge
    exec('ip netns exec "switch" ip link set "{}" master "{}"'.format(ifname2, br2name))
    exec('ip netns exec "switch" ip link set "{}" master "{}"'.format(ifname1, br1name))

    # source -> target
    if source_tc is not None:
        exec('ip netns exec "switch" tc qdisc replace dev "{}" root {}'.format(ifname2, source_tc))

    # target -> source
    if target_tc is not None:
        exec('ip netns exec "switch" tc qdisc replace dev "{}" root {}'.format(ifname2, target_tc))

    # isolate interfaces (they can only speak to the downlink interface in the bridge they are)
    exec('ip netns exec "switch" bridge link set dev "{}" isolated on'.format(ifname1))
    exec('ip netns exec "switch" bridge link set dev "{}" isolated on'.format(ifname2))

def start_yggdrasil_instances():
    print("init yggdrasil")
    for name in nodes:
        print("  start yggdrasil on {}".format(name))

        nsname = 'ns-{}'.format(name)
        exec('sudo ip netns exec "{}" sh -c \'echo "{{\nAdminListen: none\n}}" | yggdrasil -useconf &\''.format(nsname))

def start_batmanadv_instances():
    print("init batman-adv")
    for name in nodes:
        print("  start batman-adv on {}".format(name))

        #ifnames = os.popen('ip netns exec "{}" ip a | awk -F \'[ @]+\' \'/veth-/{{print($2)}}\''.format(nsname)).read().strip()
        #exec('ip netns exec "{}" batctl meshif "bat0" interface add {}'.format(nsname, ifnames))
        nsname = 'ns-{}'.format(name)
        exec('ip netns exec "{}" batctl meshif "bat0" interface add uplink'.format(nsname))

def start_babel_instances():
    print("init babel")
    for name in nodes:
        exec('mkdir -p /var/run/babel')
        exec('rm -f /var/run/babel/*.pid')
        print("  start babel on {}".format(name))

        nsname = 'ns-{}'.format(name)
        exec('ip netns exec "{}" babeld -D -I /var/run/babel/{}.pid uplink &'.format(nsname, name))


class Statistics:
    def __init__(self, name, output):
        self.name = name
        self.valid = False
        lines = output.split("\n")
        if len(lines) == 7:
            link_toks = lines[1].split()
            rx_toks = lines[3].split()
            tx_toks = lines[5].split()
            self.mac = link_toks[1]
            self.rx_bytes = int(rx_toks[0])
            self.rx_packets = int(rx_toks[1])
            self.tx_bytes = int(tx_toks[0])
            self.tx_packets = int(tx_toks[1])
            self.valid = True
        else:
            print('warning: failed to parse statistics of {}'.format(name))

def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return '{:.2f} {}B'.format(size, power_labels[n])

def print_statistics():
    stats = []

    # fetch uplink statistics
    for name in nodes:
        nsname = 'ns-{}'.format(name)
        output = os.popen('ip netns exec "{}" ip -statistics link show dev uplink'.format(nsname)).read()
        stat = Statistics(name, output)
        if stat.valid:
            stats.append(stat)

    # sum all up
    rx_bytes = 0
    rx_packets = 0
    tx_bytes = 0
    tx_packets = 0

    for stat in stats:
        rx_bytes += stat.rx_bytes
        rx_packets += stat.rx_packets
        tx_bytes += stat.tx_bytes
        tx_packets += stat.tx_packets

    print('nodes: {}, packets: {}/{}, traffic: {}/{} (on uplink interfaces)'.format(
        len(stats), rx_packets, tx_packets, format_bytes(rx_bytes), format_bytes(tx_bytes)))


user_id = os.popen('id -u').read()

if user_id.strip() != "0":
    print("Need to run as root.")
    exit(1)

if len(sys.argv) != 3:
    print('usage: {} <batman-adv|yggdrasil> <json-file>'.format(sys.argv[0]))
    exit(1)


print("Cleanup old network")
os.system('ip -all netns delete')

# add switch namespace to contain all bridges (the wiring of the mesh)
exec('ip netns add "switch"')

# disable IPv6 in switch namespace (no need, less overhead)
exec('ip netns exec "switch" sysctl -q -w net.ipv6.conf.all.disable_ipv6=1')

print("Init network")
with open(sys.argv[2]) as file:
    data = json.load(file)
    for p in data['links']:
        create_link(p['source'], p['target'], p.get('source_tc'), p.get('target_tc'))

if sys.argv[1] == "batman-adv":
    start_batmanadv_instances()
elif sys.argv[1] == "yggdrasil":
    start_yggdrasil_instances()
elif sys.argv[1] == "babel":
    start_babel_instances()
else:
    print('Error: unknown routing protocol: {}'.format(sys.argv[1]))

print('done')

'''
print("Let's wait 10 seconds for things to settle...")
time.sleep(10)

print_statistics()

print("Now wait 5 minutes for the second measurement...")
time.sleep(5 * 60)

print_statistics()
'''
