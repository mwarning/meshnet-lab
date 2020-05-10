#!/usr/bin/env python3

import os
import sys
import glob

sys.path.append('../../')
import software
import network
import tools


tools.root()
software.clear()
network.clear()

# need to open more files (especially for traffic measurement processes)
os.system('ulimit -Sn 4096')

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
	for path in sorted(glob.glob(f'../../data/freifunk/*.json')):
		(node_count, link_count) = tools.json_count(path)
		dataset_name = os.path.basename(path)[9:-5]

		if node_count != 307:
			continue

		print(f'run {protocol} on {path}')

		network.change(from_state='none', to_state=path, link_command=get_tc_command)
		tools.sleep(10)

		wait_beg_ms = tools.millis()
		traffic_beg = tools.traffic()

		software.start(protocol)

		# Wait until 300s are over, else error
		tools.wait(wait_beg_ms, 300)

		ping_result = tools.ping(count=node_count, duration_ms=60000, verbosity='verbose')

		sysload_result = tools.sysload()

		traffic_end = tools.traffic()
		software.stop(protocol)

		# add data to csv file
		extra = (['dataset_name', 'node_count'], [dataset_name, node_count])
		tools.csv_update(csvfile, '\t', extra, (traffic_end - traffic_beg).getData(), ping_result.getData(), sysload_result)

		network.clear()

for protocol in ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'yggdrasil']:
	with open(f"{prefix}freifunk1-{protocol}.csv", 'w+') as csvfile:
		run(protocol, csvfile)
