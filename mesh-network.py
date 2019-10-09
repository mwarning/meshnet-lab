#!/usr/bin/env python3

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
    downname = "downlink-{}".format(name)

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
        nodes[source] = True

    if target not in nodes:
        create_node(target)
        nodes[target] = True

    nsname1 = "ns-{}".format(source)
    nsname2 = "ns-{}".format(target)
    ifname1 = "veth-{}-{}".format(source, target)
    ifname2 = "veth-{}-{}".format(target, source)

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
        print("  start banel on {}".format(name))

        nsname = 'ns-{}'.format(name)
        exec('sudo ip netns exec "{}" babeld uplink &'.format(nsname))


def get_statistics(nsname):
    # todo: parse output
    exec('ip netns exec "{}" ip -statistics link show'.format(nsname))

def run_test():
    pass

user_id = os.popen('id -u').read()

if user_id.strip() != "0":
    print("Need to run as root.")
    exit(1)

if len(sys.argv) != 3:
    print('usage: {} <batman-adv|yggdrasil> <json-file>'.format(sys.argv[0]))
    exit(1)


os.system('ip -all netns delete')

# add switch namespace to contain all bridges (the wiring of the mesh)
exec('ip netns add "switch"')

# disable IPv6 in namespace
exec('ip netns exec "switch" sysctl -w net.ipv6.conf.all.disable_ipv6=1 > /dev/null')

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

run_test()

print('done')
