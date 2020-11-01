#!/bin/sh

address="$1"
id="$2"

echo "start cjdns on ${address} in ${id}"

ip link set "uplink" down
ip link set "uplink" up

cjdroute --genconf > /tmp/cjdns-${id}.conf
nohup cjdroute > /dev/null 2> /dev/null < /tmp/cjdns-${id}.conf &
