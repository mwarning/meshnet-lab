#!/usr/bin/env python3

import csv


'''
Calculate the traffic increase per 100 nodes. Needed for presentation.
'''

def kbs(tx_bytes, traffic_ms, node_count):
    return (float(tx_bytes) / 1000) / (float(traffic_ms) / 1000) / float(node_count)

print('KB/s increase per 100 nodes:')

for protocol in ['batman-adv', 'babel', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'yggdrasil']:
    with open(f'1_scalability1-{protocol}-rtree.csv') as csvfile:
        spamreader = csv.reader(csvfile, delimiter='\t')
        rows = list(spamreader)
        header = rows[0]
        tx_bytes_idx = header.index('tx_bytes')
        traffic_ms_idx = header.index('traffic_ms')
        node_count_idx = header.index('node_count')

        first = rows[1]
        last = None
        for row in rows[1:]:
            if float(row[node_count_idx]) > 300:
                last = row
                break

        first_value = kbs(first[tx_bytes_idx], first[traffic_ms_idx], first[node_count_idx])
        last_value = kbs(last[tx_bytes_idx], last[traffic_ms_idx], last[node_count_idx])

        #print(f'{first_value} {last_value}')

        m = 100.0 * (last_value - first_value) / (float(last[node_count_idx]) - float(first[node_count_idx]))
        print(f'{protocol} {m:.2f} KB/s')
