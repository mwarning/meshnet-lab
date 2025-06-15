#!/bin/sh

address="$1"
id="$2"

if [ -n "$id" ]; then
  # called for each node
  kill -9 $(cat "/tmp/qaul-${id}.pid")
  rm -f "/tmp/qaul-${id}.pid"
else
  # called once per remote
  pkill -SIGKILL -x qauld
  rm -f /tmp/qaul-*.pid
fi

true
