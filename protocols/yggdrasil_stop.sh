#!/bin/sh

address="$1"
id="$2"

if [ -n "$id" ]; then
  # called for each node
  kill -9 $(cat "/tmp/yggdrasil-${id}.pid")
  rm -f /tmp/yggdrasil-${id}.*
else
  # called once per remote
  pkill -SIGKILL -x yggdrasil
  rm -f /tmp/yggdrasil-*
fi

true
