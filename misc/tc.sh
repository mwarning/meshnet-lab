#!/usr/bin/sh

# A script to use a link command to change link properties. The variables
# in the link command are enclosed with curly braces and are take from the
# link objects in the graph.json file.
# E.g. ./network.py --verbosity verbose --link-command './misc/tc.sh "{direction}" "{action}" "{ifname}" "{latency_ms}" "{loss_pc}" "{bandwidth_mbit}"' apply graph.json

direction="$1"
action="$2"
ifname="$3"
latency_ms="${4:-1}"
loss_pc="${5:-0}"
bandwidth_mbit="${6:-10}"

if [ "$direction" = "source" ]; then
  case "$action" in
    "create")
      tc qdisc add dev ${ifname} root handle 1: netem delay ${latency_ms}ms loss ${loss_pc}%
      tc qdisc add dev ${ifname} parent 1: handle 2: tbf rate ${bandwidth_mbit}mbit burst 32kbit latency ${latency_ms}ms
      ;;
    "update")
      tc qdisc change dev ${ifname} root handle 1: netem delay ${latency_ms}ms loss ${loss_pc}%
      tc qdisc change dev ${ifname} parent 1: handle 2: tbf rate ${bandwidth_mbit}mbit burst 32kbit latency ${latency_ms}ms
      ;;
    "remove")
      tc qdisc del dev ${ifname} root
      ;;
  esac
fi
