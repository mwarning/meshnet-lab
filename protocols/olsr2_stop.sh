#!/bin/sh

pkill -SIGKILL -x olsrd2
rm -f /tmp/olsrd2-*.conf
true
