#!/bin/sh

address="$1"
id="$2"

if [ -n "$id" ]; then
  # called for each node
  kill -9 $(cat "/tmp/bmx6_${id}/pid") 2> /dev/null
  rm -rf /tmp/bmx6_${id}/
else
  # called once per remote
  pkill -SIGKILL -x bmx6 2> /dev/null
  rm -rf /tmp/bmx6_*
fi

true
