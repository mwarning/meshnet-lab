#!/bin/sh

address="$1"
id="$2"

if ! test -d "/tmp/bmx6_${id}"; then
    echo "start bmx6 on ${address} in ${id}"

    ip -4 addr flush dev "uplink"
    ip -6 addr flush dev "uplink"

    ip link set "uplink" down
    ip link set "uplink" up

    bmx6 --runtimeDir "/tmp/bmx6_${id}" dev=uplink
else
    echo "bmx6 already runs on ${address} in ${id}"
fi
