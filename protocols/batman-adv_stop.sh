#!/bin/sh

address="$1"
id="$2"

if [ -n "$id" ]; then
  # called for each node
  batctl meshif "bat0" interface del "uplink" 2> /dev/null
else
  # called once per remote
  for ns in $(ip netns list); do
    ip netns exec "$ns" batctl meshif "bat0" interface del "uplink" 2> /dev/null
  done
fi

true

# destroys every bridge attached to node... bug?
#modprobe -r batman-adv