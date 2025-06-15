#!/bin/sh

address="$1"
id="$2"

if [ -n "$id" ]; then
  # called for each node
  kill -9 $(cat "/tmp/olsr1-${id}.pid")
  rm -f "/tmp/olsr1-${id}.pid"
else
  # called once per remote
  pkill -SIGKILL -x olsrd
  rm -f /tmp/olsr1-*.pid
fi

true
