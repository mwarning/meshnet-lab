#!/bin/sh

address="$1"
id="$2"

if ! test -d "/tmp/bmx7_${id}"; then
    echo "start bmx7 on ${address} in ${id}"

    ip link set "uplink" down
    ip link set "uplink" up

    bmx7 --runtimeDir "/tmp/bmx7_${id}" --nodeRsaKey 6 /keyPath="/tmp/bmx7_${id}/rsa.der" --descSqnPath "/tmp/bmx7_${id}/descSqn" dev=uplink
else
    echo "bmx7 already runs on ${address} in ${id}"
fi
