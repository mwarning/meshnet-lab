#!/bin/sh

address="$1"
id="$2"

echo "start qaul on ${address} in ${id}"

addr4() {
  local mac=$(cat "/sys/class/net/$1/address")
  IFS=':'; set $mac; unset IFS
  [ "$6" = "ff" -o "$6" = "00" ] && set $1 $2 $3 $4 $5 "01"
  printf "10.%d.%d.%d" 0x$4 0x$5 0x$6
}

ip link set "uplink" down
ip link set "uplink" up
ip a a $(addr4 "uplink")/8 dev "uplink"

DIR="/tmp/qaul-${id}"
rm -rf "$DIR"
mkdir "$DIR"
cd "$DIR"

nohup qauld --name="test-${id}" > /dev/null 2> /dev/null < /dev/null &
