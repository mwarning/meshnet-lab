#!/usr/bin/env python3

import threading
import datetime
import argparse
import time
import json
import sys
import os
import re

import shared
from shared import (
    eprint, create_process, exec, get_remote_mapping, millis,
    default_remotes, convert_to_neighbors, stop_all_terminals,
    wait_for_completion, format_size, Remote, get_thread_id
)

class _Traffic:
    def __init__(self):
        self.rx_bytes = 0
        self.rx_packets = 0
        self.rx_errors = 0
        self.rx_dropped = 0
        self.rx_overrun = 0
        self.rx_mcast = 0
        self.tx_bytes = 0
        self.tx_packets = 0
        self.tx_errors = 0
        self.tx_dropped = 0
        self.tx_carrier = 0
        self.tx_collsns = 0

    def getData(self):
        titles = ['rx_bytes', 'rx_packets', 'rx_errors', 'rx_dropped',
            'rx_overrun', 'rx_mcast', 'tx_bytes', 'tx_packets',
            'tx_errors', 'tx_dropped', 'tx_carrier', 'tx_collsns'
        ]

        values = [self.rx_bytes, self.rx_packets, self.rx_errors, self.rx_dropped,
            self.rx_overrun, self.rx_mcast, self.tx_bytes, self.tx_packets,
            self.tx_errors, self.tx_dropped, self.tx_carrier, self.tx_collsns
        ]

        return (titles, values)

    def __sub__(self, other):
        ts = _Traffic()
        ts.rx_bytes = self.rx_bytes - other.rx_bytes
        ts.rx_packets = self.rx_packets - other.rx_packets
        ts.rx_errors = self.rx_errors - other.rx_errors
        ts.rx_dropped = self.rx_dropped - other.rx_dropped
        ts.rx_overrun = self.rx_overrun - other.rx_overrun
        ts.rx_mcast = self.rx_mcast - other.rx_mcast
        ts.tx_bytes = self.tx_bytes - other.tx_bytes
        ts.tx_packets = self.tx_packets - other.tx_packets
        ts.tx_errors = self.tx_errors - other.tx_errors
        ts.tx_dropped = self.tx_dropped - other.tx_dropped
        ts.tx_carrier = self.tx_carrier - other.tx_carrier
        ts.tx_collsns = self.tx_collsns - other.tx_collsns
        return ts

def traffic(remotes=default_remotes, ids=None, interface=None, rmap=None):
    if rmap is None:
        rmap = get_remote_mapping(remotes)

    if ids is None:
        ids = list(rmap.keys())

    if interface is None:
        interface = 'uplink'

    ts = _Traffic()
    ts_lock = threading.Lock()

    def collectResults(returncode, stdout, errout):
        js = json.loads(stdout)
        stats64 = js[0]['stats64']
        rx = stats64['rx']
        tx = stats64['tx']

        ts_lock.acquire()
        ts.rx_bytes += rx['bytes']
        ts.rx_packets += rx['packets']
        ts.rx_errors += rx['errors']
        ts.rx_dropped += rx['dropped']
        ts.rx_overrun += rx['over_errors']
        ts.rx_mcast += rx['multicast']
        ts.tx_bytes += tx['bytes']
        ts.tx_packets += tx['packets']
        ts.tx_errors += tx['errors']
        ts.tx_dropped += tx['dropped']
        ts.tx_carrier += tx['carrier_errors']
        ts.tx_collsns += tx['collisions']
        ts_lock.release()

    for i, id in enumerate(ids):
        remote = rmap[id]

        command = f'ip netns exec ns-{id} ip -j -statistics link show dev {interface}'
        tid = get_thread_id()
        exec(tid, remote, command, ignore_error=False, onResultCallBack=collectResults)

    wait_for_completion()

    return ts

def main():
    parser = argparse.ArgumentParser(description='Measure mean traffic speed.')
    parser.add_argument('--remotes', help='Measure across remotes described in the provided JSON file.')
    parser.add_argument('--interface', help='Interface to measure traffic on.')
    parser.add_argument('--duration', type=int, help='Measurement duration [ms].')

    args = parser.parse_args()

    if args.remotes:
        if not os.path.isfile(args.remotes):
            eprint(f'File not found: {args.remotes}')
            stop_all_terminals()
            exit(1)

        with open(args.remotes) as file:
            args.remotes = [Remote.from_json(obj) for obj in json.load(file)]
    else:
        args.remotes = default_remotes

    # need root for local setup
    for remote in args.remotes:
        if remote.address is None:
            if os.geteuid() != 0:
                eprint('Need to run as root.')
                exit(1)

    rmap = get_remote_mapping(args.remotes)
    if args.duration:
        ds = args.duration / 1000
        ts_beg = traffic(args.remotes, interface=args.interface, rmap=rmap)
        time.sleep(ds)
        ts_end = traffic(args.remotes, interface=args.interface, rmap=rmap)
        ts = ts_end - ts_beg
        n = ds * len(rmap)
        print(f'rx: {format_size(ts.rx_bytes / n)}/s, {ts.rx_packets / n:.2f} packets/s, {ts.rx_dropped / n:.2f} dropped/s (avg. per node)')
        print(f'tx: {format_size(ts.tx_bytes / n)}/s, {ts.tx_packets / n:.2f} packets/s, {ts.tx_dropped / n:.2f} dropped/s (avg. per node)')
    else:
        ts = traffic(args.remotes, interface=args.interface, rmap=rmap)
        print(f'rx: {format_size(ts.rx_bytes)} / {ts.rx_packets} packets / {ts.rx_dropped} dropped')
        print(f'tx: {format_size(ts.tx_bytes)} / {ts.tx_packets} packets / {ts.tx_dropped} dropped')

    stop_all_terminals()

if __name__ == "__main__":
    main()
