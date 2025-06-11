#!/bin/sh

address="$1"
id="$2"

if ! test -e /sys/class/net/bat0; then
  echo "start batman-adv on ${address} in ${id}"

  ip link set "uplink" down
  ip link set "uplink" up
  ip -4 addr flush dev "uplink"
  ip -6 addr flush dev "uplink"

  # batman-adv is not running
  #modprobe batman-adv # make sure it is loaded
  batctl meshif "bat0" interface add "uplink"
  ip link set "bat0" up
else
  echo "batman-adv already runs on ${address} in ${id}"
fi
