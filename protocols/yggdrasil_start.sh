#!/bin/sh

address="$1"
id="$2"

echo "start yggdrasil on ${address} in ${id}"

ip link set "uplink" down
ip link set "uplink" up

# yggdrasil uses a tun0 interface, uplink only needs an fe80:* address

printf "AdminListen: none" > "/tmp/yggdrasil-${id}.conf"
nohup yggdrasil -useconffile "/tmp/yggdrasil-${id}.conf" > /dev/null 2> /dev/null < /dev/null &
