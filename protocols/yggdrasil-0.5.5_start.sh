#!/bin/sh

address="$1"
id="$2"

echo "start yggdrasil-0.5.5 on ${address} in ${id}"

ip link set "uplink" down
ip link set "uplink" up

# yggdrasil uses a tun0 interface, uplink only needs an fe80:* address

echo "AdminListen: none" > "/tmp/yggdrasil-0.5.5-${id}.conf"
nohup yggdrasil-0.5.5 -useconffile "/tmp/yggdrasil-0.5.5-${id}.conf" > /dev/null 2>&1 < /dev/null &
