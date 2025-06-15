#!/bin/sh

address="$1"
id="$2"

if ! test -f /tmp/olsr2-${id}.pid; then
  echo "start olsr2 on ${remote} in ${id}"

cat <<- EOF > "/tmp/olsr2-${id}.conf"
  [global]
  fork       yes
  lockfile   -
  pidfile    /tmp/olsr2-${id}.pid

  # restrict to IPv6
  [olsrv2]
  originator  -0.0.0.0/0
  originator  -::1/128
  originator  default_accept

  # restrict to IPv6
  [interface]
  bindto  -0.0.0.0/0
  bindto  -::1/128
  bindto  default_accept
EOF

  addr6() {
    local mac=$(cat "/sys/class/net/$1/address")
    IFS=':'; set $mac; unset IFS
    printf fdef:17a0:ffb1:300:$(printf %02x $((0x$1 ^ 2)))$2:${3}ff:fe$4:$5$6
  }

  ip -4 addr flush dev "uplink"
  ip -6 addr flush dev "uplink"
  ip link set "uplink" down
  ip link set "uplink" up
  ip a a $(addr6 "uplink")/128 dev "uplink"

  olsrd2 "uplink" --load /tmp/olsr2-${id}.conf
else
  echo "olsr2 already runs on ${address} in ${id}"
fi
