#!/usr/bin/env python3

import datetime
import argparse
import time
import sys
import os
import re

import shared
from shared import (
    eprint, create_process, exec, get_remote_mapping, millis,
    default_remotes, convert_to_neighbors, stop_all_terminals,
    format_size, Remote
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

    for id in ids:
        remote = rmap[id]
        stdout = exec(remote, f'ip netns exec ns-{id} ip -statistics link show dev {interface}', get_output=True)[0]
        lines = stdout.split('\n')
        link_toks = lines[1].split()
        rx_toks = lines[3].split()
        tx_toks = lines[5].split()
        ts.rx_bytes += int(rx_toks[0])
        ts.rx_packets += int(rx_toks[1])
        ts.rx_errors += int(rx_toks[2])
        ts.rx_dropped += int(rx_toks[3])
        ts.rx_overrun += int(rx_toks[4])
        ts.rx_mcast += int(rx_toks[5])
        ts.tx_bytes += int(tx_toks[0])
        ts.tx_packets += int(tx_toks[1])
        ts.tx_errors += int(tx_toks[2])
        ts.tx_dropped += int(tx_toks[3])
        ts.tx_carrier += int(tx_toks[4])
        ts.tx_collsns += int(tx_toks[5])

    return ts

def main():
    parser = argparse.ArgumentParser(description='Measure mean traffic.')
    parser.add_argument('--remotes', help='Distribute nodes and links on remotes described in the JSON file.')
    parser.add_argument('--interface', help='Interface to measure traffic on.')
    parser.add_argument('--duration', type=int, help='Measurement duration in seconds.')

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
        ds = args.duration
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
