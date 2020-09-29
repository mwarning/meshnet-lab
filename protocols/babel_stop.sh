#!/bin/sh

pkill -SIGKILL -x babeld
rm -f /tmp/babel-*.pid
true
