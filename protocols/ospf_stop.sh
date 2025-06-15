#!/bin/sh

address="$1"
id="$2"

if [ -n "$id" ]; then
  # called for each node
  kill -9 $(cat "/tmp/bird-ospf-${id}.pid")
  rm -f /tmp/bird-ospf-${id}.*
else
  # called once per remote
  pkill -SIGKILL -x bird
  rm -f /tmp/bird-ospf-*
fi

true
