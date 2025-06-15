#!/bin/sh

address="$1"
id="$2"

if ! test -f /tmp/cjdns-${id}.pid; then
  echo "start cjdns on ${address} in ${id}"

  ip link set "uplink" down
  ip link set "uplink" up

  cjdroute --genconf > /tmp/cjdns-${id}.conf
  cjdroute > /dev/null 2> /dev/null < /tmp/cjdns-${id}.conf
  pgrep -n cjdroute > "/tmp/cjdns-${id}.pid"
else
  echo "cjdns already runs on ${address} in ${id}"
fi
