#!/bin/sh

address="$1"
id="$2"

batctl meshif "bat0" interface destroy 2> /dev/null
true
