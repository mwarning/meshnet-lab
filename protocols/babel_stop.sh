#!/bin/sh

address="$1"
id="$2"

if [ -n "$id" ]; then
  # called for each node
  kill -9 $(cat "/tmp/babel-${id}.pid")
  rm -f "/tmp/babel-${id}.pid"
else
  # called once per remote
  pkill -SIGKILL -x babeld
  rm -f /tmp/babel-*.pid
fi

true
