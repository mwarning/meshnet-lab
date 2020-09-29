#!/bin/sh

batctl meshif "bat0" interface del "uplink" 2> /dev/null
true

# destroys every bridge attached to node...
#modprobe -r batman-adv