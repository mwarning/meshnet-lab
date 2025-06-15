#!/bin/sh

address="$1"
id="$2"

if [ -n "$id" ]; then
  # called for each node
  kill -9 $(cat "/tmp/cjdns-${id}.pid")
  rm -f /tmp/cjdns-${id}.*
else
  # called once per remote
  pkill -SIGKILL -x cjdroute
  rm -f /tmp/cjdns-*
fi

true
