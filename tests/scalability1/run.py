#!/usr/bin/env python3

import os
import sys
import glob

sys.path.append('../../')
import software
import network
from shared import Remote
import shared
import traffic
import ping


# increase limit for all the parallel pings
os.system('ulimit -Sn 4096')

remotes= [Remote()]

shared.check_access(remotes)
software.copy(remotes, '../../protocols', '/var/')

software.clear(remotes)
network.clear(remotes)

prefix = os.environ.get('PREFIX', '')

# 100MBit LAN cable
def get_tc_command(link, ifname):
	return f'tc qdisc replace dev "{ifname}" root tbf rate 100mbit burst 8192 latency 1ms'

def run(protocol, files, csvfile):
	for path in sorted(glob.glob(files)):
		state = shared.load_json(path)
		(node_count, link_count) = shared.json_count(state)

		# Limit node count to 300
		#if node_count < 300:
		#	continue

		print(f'run {protocol} on {path}')

		network_start_ms = shared.millis()
		network.apply(state=state, link_command=get_tc_command, remotes=remotes)
		network_stop_ms = shared.millis()

		shared.sleep(10)

		software_start_ms = shared.millis()
		software.start(protocol, remotes)
		software_stop_ms = shared.millis()

		# Let the nodes start up and discover themselves.
		# Increase the value if the system is rather slow.
		shared.sleep(30)

		traffic_start_ms = shared.millis()
		traffic_begin = traffic.traffic(remotes)

		# Send <node_count> pings.
		# For a good routing algorithm, this should make the traffic per node constant.
		paths = ping.get_random_paths(state, 2 * node_count)
		paths = ping.filter_paths(state, paths, min_hops=2, path_count=node_count)
		ping_result = ping.ping(remotes=remotes, paths=paths, duration_ms=300000, verbosity='verbose')

		traffic_stop_ms = shared.millis()
		traffic_end = traffic.traffic(remotes)

		sysload_result = shared.sysload(remotes)

		# remove network and stop all started routing software
		software.clear(remotes)
		network.clear(remotes)

		# Add data to csv file
		network_startup_ms = network_stop_ms - network_start_ms
		software_startup_ms = software_stop_ms - software_start_ms
		traffic_measurement_ms = traffic_stop_ms - traffic_start_ms

		extra = (['node_count', 'network_startup_ms', 'software_startup_ms', 'traffic_measurement_ms'],
			[node_count, network_startup_ms, traffic_measurement_ms, software_startup_ms])
		shared.csv_update(csvfile, '\t', extra, (traffic_end - traffic_begin).getData(), ping_result.getData(), sysload_result)

		# Skip test if the successful pings drop below 60%
		if (100.0 * ping_result.received / ping_result.send) < 60:
			print('Less than 60%% successful pings => skip test')
			break

		# Skip test if network setup takes too long.
		# but this is not unusual for huge networks and we could continue anyway.
		if network_startup_ms > (60*60*1000):
			print('Network setup took more than one hour => skip test')
			break

for name in ['line', 'grid4', 'rtree']:
	for protocol in ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'ospf', 'yggdrasil']:
		with open(f"{prefix}scalability1-{protocol}-{name}.csv", 'w+') as csvfile:
			run(protocol, f"../../data/{name}/*.json", csvfile)

shared.stop_all_terminals()
