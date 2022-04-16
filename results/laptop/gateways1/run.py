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


def run(protocol, tasks, csvfile):
	for path, gateways in tasks:
		state = shared.load_json(path)
		(node_count, link_count) = shared.json_count(state)

		# Limit node count to 300
		if node_count > 300:
			continue

		print(f'run {protocol} on {path}')

		network.apply(state=state, remotes=remotes)

		shared.sleep(10)

		software_start_ms = shared.millis()
		software.start(protocol, remotes)
		software_startup_ms = shared.millis() - software_start_ms

		shared.sleep(30)

		start_ms = shared.millis()
		traffic_beg = traffic.traffic(remotes)

		paths = ping.get_paths_to_gateways(state, gateways)
		ping_result = ping.ping(remotes=remotes, paths=paths, duration_ms=300000, verbosity='verbose')

		traffic_ms = shared.millis() - start_ms
		traffic_end = traffic.traffic(remotes)

		sysload_result = shared.sysload(remotes)

		software.clear(remotes)
		network.clear(remotes)

		# add data to csv file
		extra = (['node_count', 'traffic_ms', 'software_startup_ms'], [node_count, traffic_ms, software_startup_ms])
		shared.csv_update(csvfile, '\t', extra, (traffic_end - traffic_beg).getData(), ping_result.getData(), sysload_result)

# return list of (json-path, [gateway-node-id])
def get_tasks(files):
	gateway_count = 1

	# make the same "random" choices every time 
	shared.seed_random(12356)

	tasks = []
	for path in sorted(glob.glob(files)):
		state = shared.load_json(path)
		tasks.append((path, ping.get_random_nodes(state, gateway_count)))
	return tasks

for name in ['line', 'grid4', 'rtree']:
	tasks = get_tasks(f"../../data/{name}/*.json")
	for protocol in ['babel', 'batman-adv', 'bmx6', 'cjdns', 'olsr1', 'olsr2', 'yggdrasil']:
		with open(f"{prefix}gateways1-{protocol}-{name}.csv", 'w+') as csvfile:
			run(protocol, tasks, csvfile)

shared.stop_all_terminals()
