#!/bin/sh

if [ -n "$id" ]; then
  # called for each node
  kill -9 $(cat "/tmp/bmx7_${id}/pid") 2> /dev/null
  rm -rf /tmp/bmx7_${id}/
else
  # called once per remote
  pkill -SIGKILL -x bmx7 2> /dev/null
  rm -rf /tmp/bmx7_*
fi

true
