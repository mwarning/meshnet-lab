#!/bin/sh

# TASK: set your own mesh routing program here!
PROGRAM="/usr/bin/true"

pkill -SIGKILL -x "$(basename '${PROGRAM}')"

exit 0
