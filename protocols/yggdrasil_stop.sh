#!/bin/sh

pkill -SIGKILL -x yggdrasil
rm -f /tmp/yggdrasil-*.conf
true
