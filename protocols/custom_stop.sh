#!/bin/sh

address="$1"
id="$2"

# TASK: set your own mesh routing program here!
PROGRAM="/usr/bin/true"

if [ -n "$id" ]; then
  # called for each node
  kill -9 $(cat "/tmp/custom-${id}.pid")
  rm /tmp/custom-${id}.*
else
  # called once per remote
  pkill -SIGKILL -x $(basename "$PROGRAM")
  rm -f /tmp/custom-*
fi

true
