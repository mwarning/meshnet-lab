#!/bin/sh

address="$1"
id="$2"

echo "start ospf on ${address} in ${id}"

# The route id can be any 32bit identifier
# as integer or as IPv4 address.
router_id=$(shuf -i 0-4294967296 -n 1)

cat <<- EOF > "/tmp/bird-ospf-${id}.conf"
  router id ${router_id};
  protocol kernel {
    scan time 10;
    import all;
    export all;
  }

  protocol ospf v3 {
    area 0 { interface "uplink" {}; };
    import all;
    export all;
  }

  protocol device {
    scan time 60;
  }
EOF

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

#ip a a $(addr4 "uplink")/32 dev "uplink"
#bird -P "/tmp/bird-ospf-${id}.pid" -s "/tmp/bird-ospf-${id}.ctl" -c "/tmp/bird-ospf-${id}.conf"

# ospf needs the fe80:* address (link local)
# and a regular IPv6 address (/128 or other)
ip a a $(addr6 "uplink")/128 dev "uplink"
bird -d -i "/tmp/bird-ospf-${id}.pid" -z "/tmp/bird-ospf-${id}.ctl" -f "/tmp/bird-ospf-${id}.conf"
