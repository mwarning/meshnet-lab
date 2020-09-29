#!/bin/sh

pkill -SIGKILL -x bird
rm -f /tmp/bird-ospf-*.conf

pkill -SIGKILL -x bird6
rm -f /tmp/bird6-ospf-*.conf

true
