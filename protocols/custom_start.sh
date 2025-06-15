#!/bin/sh

# TASK: set your own mesh routing program here!
PROGRAM="/usr/bin/true"

address="$1"
id="$2"

if ! test -f "/tmp/custom-${id}.pid"; then
  echo "start custom on ${address} in ${id}"

  ip link set "uplink" down
  ip link set "uplink" up

  ${PROGRAM} -p "$PROTOCOL" -d -i "uplink" -s "/tmp/custom-${id}.sock" -l "/tmp/custom-${id}.log" --pidfile "/tmp/custom-${id}.pid"
else
    echo "custom already runs on ${address} in ${id}"
fi
