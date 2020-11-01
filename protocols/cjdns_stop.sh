#!/bin/sh

pkill -SIGKILL -x cjdroute
rm -f /tmp/cjdns-*.conf

true
