#!/bin/sh

address="$1"
id="$2"

if test "/tmp/yggdrasil-${id}.pid"; then
  echo "start yggdrasil on ${address} in ${id}"

  ip link set "uplink" down
  ip link set "uplink" up

  # yggdrasil uses a tun0 interface, uplink only needs an fe80:* address

  echo "AdminListen: none" > "/tmp/yggdrasil-${id}.conf"
  nohup yggdrasil -useconffile "/tmp/yggdrasil-${id}.conf" > /tmp/yggdrasil-${id}.log 2>&1 < /dev/null &
  echo $! > "/tmp/yggdrasil-${id}.pid"

  # wait only the tunnel is set up
  while ! ip a list dev tun0 | grep -q "inet6 2"; do
    sleep 1
  done
else
  echo "yggdrasil already runs on ${address} in ${id}"
fi
