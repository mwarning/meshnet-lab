#!/usr/bin/env python3

import random
import datetime
import argparse
import subprocess
import math
import time
import sys
import os
import re


def eprint(s):
    sys.stderr.write(s + '\n')

# get time in milliseconds
def millis():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

# get system load from uptime command
# average of the last 1, 5 and 15 minutes
def get_load_average():
    p = subprocess.Popen(['uptime'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out, err) = p.communicate()
    t = out.decode().split('load average:')[1].split(',')
    return (float(t[0]), float(t[1]), float(t[2]))

# get random node pairs (not unique, not path to self)
def get_random_pairs(items, npairs):
    pairs = []

    if len(items) < 2 and npairs > 0:
        eprint('Not enough nodes to get any pairs!')
        exit(1)

    while len(pairs) < npairs:
        e1 = random.choice(items)
        e2 = random.choice(items)
        if e1 == e2:
            continue

        pairs.append((e1, e2))

    return pairs

# get IPv6 address, use fe80:: address as fallback
# TODO: return IPv6 address of the broadest scope in general
def get_ipv6_address(nsname, interface):
    lladdr = None
    # print only IPv6 addresses
    output = os.popen('ip netns exec "{}" ip -6 addr list dev {}'.format(nsname, interface)).read()
    for line in output.split('\n'):
        if 'inet6 ' in line:
            addr = line.split()[1].split('/')[0]
            if addr.startswith('fe80'):
                lladdr = addr
            else:
                return addr

    return lladdr

class PingResult:
    transmitted = 0
    received = 0
    rtt_min = 0.0
    rtt_max = 0.0
    rtt_avg = 0.0

    def __init__(self, transmitted = 0, received = 0, rtt_min = 0.0, rtt_max = 0.0, rtt_avg = 0.0):
        self.transmitted = transmitted
        self.received = received
        self.rtt_min = rtt_min
        self.rtt_max = rtt_max
        self.rtt_avg = rtt_avg

numbers_re = re.compile('[^0-9.]+')

def parse_ping(output):
    ret = PingResult()
    for line in output.split('\n'):
        if 'packets transmitted' in line:
            toks = numbers_re.split(line)
            ret.transmitted = int(toks[0])
            ret.received = int(toks[1])
        if line.startswith('rtt min/avg/max/mdev'):
            toks = numbers_re.split(line)
            ret.rtt_min = float(toks[1])
            ret.rtt_avg = float(toks[2])
            ret.rtt_max = float(toks[3])
            #ret.rtt_mdev = float(toks[4])

    return ret

'''
Add a CSV header if the target file is empty or
extend existing header (for added data outside of this script)
'''
def add_csv_header(file, header):
    pos = file.tell()

    if pos == 0:
        # empty file => add header
        file.write(header)

    if pos > 0 and pos < len(header):
        # non-empty files but cannot be our header => assume existing header and extend it
        file.seek(0)
        content = file.read()
        if content.count('\n') == 1:
            file.seek(0)
            file.truncate()
            lines = content.split('\n')
            file.write(lines[0] + header)
            file.write(lines[1])

'''
1. traffic statistics
2. ping path_count times over test_duration_ms
3. wait until test_duration_ms is over
4. traffic statistics
5. print/write data
'''
def run_test(protocol, nsnames, interface, path_count = 10, test_duration_ms = 1000, wait_ms = 0, outfile = None):
    ping_deadline=1
    ping_count=1
    processes = []

    pairs = list(get_random_pairs(nsnames, path_count))
    ts_beg = get_traffic_statistics(nsnames)

    if wait_ms > 0:
        time.sleep(wait_ms / 1000.0)
        if args.verbosity != 'quiet':
            print('Wait for {} for pings to start.'.format(format_duration(wait_ms)))

    start_ms = millis()
    started = 0
    while started < len(pairs):
        # number of expected tests to have been run
        started_expected = math.ceil(((millis() - start_ms) / test_duration_ms) * len(pairs))
        if started_expected > started:
            for _ in range(0, started_expected - started):
                (nssource, nstarget) = pairs.pop()
                nstarget_addr = get_ipv6_address(nstarget, interface)

                if args.verbosity == 'verbose':
                    print('[{:06}] Ping {} => {} ({} / {})'.format(millis() - start_ms, nssource, nstarget, nstarget_addr, interface))

                command = ['ip', 'netns', 'exec', nssource ,'ping', '-c', str(ping_count), '-w', str(ping_deadline), '-D', nstarget_addr]
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                processes.append(process)
                started += 1
        else:
            # sleep a small amount
            time.sleep(test_duration_ms / len(pairs) / 1000.0 / 10.0)

    stop1_ms = millis()

    # wait until test_duration_ms is over
    if (stop1_ms - start_ms) < test_duration_ms:
        time.sleep((test_duration_ms - (stop1_ms - start_ms)) / 1000.0)

    stop2_ms = millis()

    ts_end = get_traffic_statistics(nsnames)

    result_packets_send = 0
    result_packets_received = 0
    result_rtt_avg = 0.0

    # wait/collect for results from pings (prolongs testing up to 1 second!)
    for process in processes:
        process.wait()
        (output, err) = process.communicate()
        result = parse_ping(output.decode())

        result_packets_send += ping_count
        result_packets_received += result.received
        result_rtt_avg += result.rtt_avg

    result_rtt_avg_ms = 0.0 if result_packets_received == 0 else (result_rtt_avg / result_packets_received)
    result_duration_ms = stop1_ms - start_ms
    result_filler_ms = stop2_ms - stop1_ms

    result_rx_bytes = ts_end.rx_bytes - ts_beg.rx_bytes
    result_rx_packets = ts_end.rx_packets - ts_beg.rx_packets
    result_rx_errors = ts_end.rx_errors - ts_beg.rx_errors
    result_rx_dropped = ts_end.rx_dropped - ts_beg.rx_dropped
    result_rx_overrun = ts_end.rx_overrun - ts_beg.rx_overrun
    result_rx_mcast = ts_end.rx_mcast - ts_beg.rx_mcast

    result_tx_bytes = ts_end.tx_bytes - ts_beg.tx_bytes
    result_tx_packets = ts_end.tx_packets - ts_beg.tx_packets
    result_tx_errors = ts_end.tx_errors - ts_beg.tx_errors
    result_tx_dropped = ts_end.tx_dropped - ts_beg.tx_dropped
    result_tx_carrier = ts_end.tx_carrier - ts_beg.tx_carrier
    result_tx_collsns = ts_end.tx_collsns - ts_beg.tx_collsns

    lavg = get_load_average()

    if outfile is not None:
        header = (
            'load_avg1 '
            'load_avg5 '
            'load_avg15 '
            'node_count '
            'packets_send '
            'packets_received '
            'wait_ms '
            'duration_ms '
            'rtt_avg_ms '
            'rx_bytes '
            'rx_packets '
            'rx_errors '
            'rx_dropped '
            'rx_overrun '
            'rx_mcast '
            'tx_bytes '
            'tx_packets '
            'tx_errors '
            'tx_dropped '
            'tx_carrier '
            'tx_collsns\n'
        )

        # add csv header if not present
        add_csv_header(outfile, header.replace(' ', args.csv_delimiter))

        outfile.write('{:0.2f} {:0.2f} {:0.2f} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}\n'.format(
            lavg[0],
            lavg[1],
            lavg[2],
            len(nsnames),
            result_packets_send,
            result_packets_received,
            int(wait_ms),
            int(result_duration_ms + result_filler_ms),
            int(result_rtt_avg_ms),
            result_rx_bytes,
            result_rx_packets,
            result_rx_errors,
            result_rx_dropped,
            result_rx_overrun,
            result_rx_mcast,
            result_tx_bytes,
            result_tx_packets,
            result_tx_errors,
            result_tx_dropped,
            result_tx_carrier,
            result_tx_collsns
        ).replace(' ', args.csv_delimiter))

    if args.verbosity != 'quiet':
        print('{}: send: {}, received: {}, load: {}/{}/{}, arrived: {}%, measurement span: {}ms + {}ms, tx: {}/s/node, rx: {}/s/node'.format(
            protocol,
            result_packets_send,
            result_packets_received,
            lavg[0], lavg[1], lavg[2],
            '-' if (result_packets_send == 0) else '{:0.2f}'.format(100.0 * (result_packets_received / result_packets_send)),
            result_duration_ms,
            result_filler_ms,
            '-' if (len(nsnames) == 0) else format_bytes(1000.0 * result_tx_bytes / result_duration_ms / len(nsnames)),
            '-' if (len(nsnames) == 0) else format_bytes(1000.0 * result_tx_bytes / result_duration_ms / len(nsnames))
        ))

class TrafficStatisticSummary:
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

    def print(self):
        print('received {} ({} bytes, {} packets), send: {} ({} bytes, {} packets)'.format(
            format_bytes(self.rx_bytes), self.rx_bytes, self.rx_packets,
            format_bytes(self.tx_bytes), self.tx_bytes, self.tx_packets
        ))

def format_bytes(size):
    power = 1000
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T', 5: 'E'}
    while size > power:
        size /= power
        n += 1
    return '{:.2f} {}B'.format(size, power_labels[n])

def format_duration(time_ms):
    d, remainder = divmod(time_ms, 24 * 60 * 60 * 1000)
    h, remainder = divmod(remainder, 60 * 60 * 1000)
    m, remainder = divmod(remainder, 60 * 1000)
    s, remainder = divmod(remainder, 1000)
    ms = remainder

    if d > 0:
        if h > 0:
            return "{}.{}d".format(int(d), int(h))
        return "{}d".format(int(d))
    elif h > 0:
        if m > 0:
            return "{}.{}h".format(int(h), int(m))
        return "{}h".format(int(h))
    elif m > 0:
        if s > 0:
            return "{}.{}m".format(int(m), int(s))
        return "{}m".format(int(m))
    elif s > 0:
        if ms > 0:
            return "{}.{}s".format(int(s), int(ms))
        return "{}s".format(int(s))
    else:
        return "{}ms".format(int(ms))

def get_traffic_statistics(nsnames):
    # fetch uplink statistics
    ret = TrafficStatisticSummary()

    for nsname in nsnames:
        command = ['ip', 'netns', 'exec', nsname , 'ip', '-statistics', 'link', 'show', 'dev', 'uplink']
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (output, err) = process.communicate()
        lines = output.decode().split('\n')
        link_toks = lines[1].split()
        rx_toks = lines[3].split()
        tx_toks = lines[5].split()
        ret.rx_bytes += int(rx_toks[0])
        ret.rx_packets += int(rx_toks[1])
        ret.rx_errors += int(rx_toks[2])
        ret.rx_dropped += int(rx_toks[3])
        ret.rx_overrun += int(rx_toks[4])
        ret.rx_mcast += int(rx_toks[5])
        ret.tx_bytes += int(tx_toks[0])
        ret.tx_packets += int(tx_toks[1])
        ret.tx_errors += int(tx_toks[2])
        ret.tx_dropped += int(tx_toks[3])
        ret.tx_carrier += int(tx_toks[4])
        ret.tx_collsns += int(tx_toks[5])

    return ret

parser = argparse.ArgumentParser()
parser.add_argument('protocol',
    choices=['none', 'babel', 'batman-adv', 'olsr1', 'olsr2', 'bmx6', 'bmx7', 'yggdrasil', 'cjdns'],
    help='Routing protocol to set up.')
parser.add_argument('--verbosity',
    choices=['verbose', 'normal', 'quiet'],
    default='normal',
    help='Set verbosity.')
parser.add_argument('--seed',
    type=int,
    help='Seed the random generator.')
parser.add_argument('--csv-out',
    help='Write CSV formatted data to file.')
parser.add_argument('--csv-delimiter',
    default='\t',
    help='Delimiter for CSV output columns. Default: tab character')
parser.add_argument('--duration',
    type=int,
    default=1,
    help='Duration in seconds for this test.')
parser.add_argument('--samples',
    type=int,
    default=10,
    help='Number of random paths to test (not unique, no destination to self).')
parser.add_argument('--wait',
    type=int,
    default=0,
    help='Seconds to wait after the begin of the traffic measurement before pings are send.')

args = parser.parse_args()

if os.popen('id -u').read().strip() != '0':
    eprint('Need to run as root.')
    exit(1)

random.seed(args.seed)

# network interface to send packets to/from
uplink_interface = 'uplink'

outfile = None
if args.csv_out is not None:
    outfile = open(args.csv_out, 'a+')

# batman-adv uses its own interface as entry point to the mesh
if args.protocol == 'batman-adv':
    uplink_interface = 'bat0'
elif args.protocol == 'yggdrasil':
    uplink_interface = 'tun0'
elif args.protocol == 'cjdns':
    uplink_interface = 'tun0'

# all ns-* network namespaces
nsnames = [x for x in os.popen('ip netns list').read().split() if x.startswith('ns-')]
run_test(args.protocol, nsnames, uplink_interface, args.samples, args.duration * 1000, args.wait * 1000, outfile)
