#!/bin/sh

address="$1"
id="$2"

echo "start bmx6 on ${address} in ${id}"

ip link set "uplink" down
ip link set "uplink" up´

bmx7 --runtimeDir "/tmp/bmx7_${id}" --nodeRsaKey 6 /keyPath="/tmp/bmx7_${id}/rsa.der" --descSqnPath "/tmp/bmx7_${id}/descSqn" dev=uplink
