#!/bin/sh

address="$1"
id="$2"

if [ -n "$id" ]; then
  # called for each node
  kill -9 $(cat "/tmp/olsr2-${id}.pid")
  rm -f "/tmp/olsr2-${id}.pid"
else
  # called once per remote
  pkill -SIGKILL -x olsrd2
  rm -f /tmp/olsr2-*.pid
fi

true
