#!/bin/sh

address="$1"
id="$2"

echo "start babel on ${address} in ${id}"

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

# babel needs the link local (fe80:*) and a regular IPv6 address
ip link set "uplink" down
ip link set "uplink" up
#ip a a $(addr4 "uplink")/32 dev "uplink"
ip a a $(addr6 "uplink")/64 dev "uplink"

babeld -D -I "/tmp/babel-${id}.pid" "uplink"
