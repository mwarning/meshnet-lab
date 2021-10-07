#!/bin/sh

# TASK: set your own mesh routing program here!
PROGRAM="/usr/bin/true"

address="$1"
id="$2"

echo "start custom mesh on ${address} in ${id}"

ip link set "uplink" down
ip link set "uplink" up

prefix=$(basename "${PROGRAM}")
${PROGRAM} -p "$PROTOCOL" -d -i "uplink" -s /tmp/${prefix}-${id}.sock -l /tmp/${prefix}-${id}.log
