#!/bin/sh

batctl meshif "bat0" interface del "uplink"

# destroys every bridge attached to node...
#modprobe -r batman-adv
