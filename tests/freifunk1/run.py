#!/usr/bin/env python3

import os
import sys
import glob

sys.path.append('../../')
import software
import network
from shared import Remote
import shared

# increase limit for all the parallel pings
os.system('ulimit -Sn 4096')

remotes= [Remote()] #[Remote('192.168.44.133'), Remote('192.168.44.137')]

shared.check_access(remotes)

software.clear(remotes)
network.clear(remotes)

prefix = os.environ.get('PREFIX', '')

# LAN cable and WiFi connection mix
def get_tc_command(link, ifname):
	'''
	# How to include packet loss:
	loss = 100 * (1 - link.get('tq', 1))
	(
		'sh -c "('
		f'tc qdisc del dev {ifname} root;'
		f'tc qdisc add dev {ifname} root handle 1: netem delay 10ms loss {loss}%;'
		f'tc qdisc add dev {ifname} parent 1: handle 2: tbf rate 1mbit burst 8192 latency 5ms;'
		')"'
	)
	'''
	if link.get('type') == 'wifi':
		return f'tc qdisc replace dev "{ifname}" root tbf rate 20mbit burst 8192 latency 5ms'
	else:
		return f'tc qdisc replace dev "{ifname}" root tbf rate 100mbit burst 8192 latency 1ms'

def run(protocol, csvfile):
	shared.seed_random(1377)

	for path in sorted(glob.glob(f'../../data/freifunk/*.json')):
		state = shared.load_json(path)

		(node_count, link_count) = shared.json_count(state)
		dataset_name = '{}-{:04d}'.format(os.path.basename(path)[9:-5], node_count)

		# limit to what the host can handle
		if node_count > 310:
			continue

		print(f'run {protocol} on {path}')

		state = network.apply(state=state, link_command=get_tc_command, remotes=remotes)
		shared.sleep(10)

		software.start(protocol, remotes)

		shared.sleep(300)

		start_ms = shared.millis()
		traffic_beg = traffic.traffic(remotes)

		paths = ping.get_random_paths(state, 2 * node_count)
		paths = shared.filter_paths(state, paths, min_hops=2, path_count=node_count)
		ping_result = shared.ping(remotes=remotes, paths=paths, duration_ms=300000, verbosity='verbose')

		sysload_result = shared.sysload(remotes)

		traffic_ms = shared.millis() - start_ms
		traffic_end = traffic.traffic(remotes)
		software.clear(remotes)

		# add data to csv file
		extra = (['dataset_name', 'node_count', 'traffic_ms'], [dataset_name, node_count, traffic_ms])
		shared.csv_update(csvfile, '\t', extra, (traffic_end - traffic_beg).getData(), ping_result.getData(), sysload_result)

		network.clear(remotes)

for protocol in ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'ospf', 'yggdrasil']:
	with open(f"{prefix}freifunk1-{protocol}.csv", 'w+') as csvfile:
		run(protocol, csvfile)

shared.stop_all_terminals()
