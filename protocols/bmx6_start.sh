#!/bin/sh

address="$1"
id="$2"

echo "start bmx6 on ${address} in ${id}"

addr4() {
  local mac=$(cat "/sys/class/net/$1/address")
  IFS=':'; set $mac; unset IFS
  [ "$6" = "ff" -o "$6" = "00" ] && set $1 $2 $3 $4 $5 "01"
  printf "10.%d.%d.%d" 0x$4 0x$5 0x$6
}

addr6() {
  local mac=$(cat "/sys/class/net/$1/address")
  IFS=':'; set $mac; unset IFS
  printf fdef:17a0:ffb1:300:$(printf %02x $((0x$1 ^ 2)))$2:${3}ff:fe$4:$5$6
}

ip link set "uplink" down
ip link set "uplink" up
ip -4 addr flush dev "uplink"
ip -6 addr flush dev "uplink"

ip a a $(addr4 "uplink")/32 dev "uplink"
# Only the link local fe80:* address is needed

bmx6 --runtimeDir "/tmp/bmx6_${id}" dev=uplink
