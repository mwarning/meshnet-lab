#!/bin/sh

# exit on any error
set -ex

# to distinguish multiple runs (if needed)
prefix="$1"

run_test() {
	local protocol="$1"
	local files="$2"
	local seed=42

	for graphfile in ${files}*.json; do
		local name=$(basename "$graphfile" | rev | cut -d'-' -f2- | rev)
		local links=$(../tools/json_count.py "$graphfile" 'count-links')
		local csvfile="${prefix}traffic1-$protocol-$name.csv"
		local duration_sec=60
		local wait_sec=30

		echo "$(date): start $protocol on $(basename \"$graphfile\")"

		# clear (just in case)
		../../network.py clear

		# Setup the network structure of namespaces
		../../network.py --ignore-tc 'change' none "$graphfile"

		# Wait for network stacks etc. to set settle
		sleep 10

		# Start software
		../../software.py --verbosity 'verbose' start "$protocol"

		# Run test
		../../tests.py --verbosity 'verbose' "$protocol" --csv-delimiter '	' --csv-out "$csvfile" --seed "$seed" --duration $duration_sec --wait $wait_sec --samples $links

		# Stop software
		../../software.py --verbosity 'verbose' stop "$protocol"

		# Remove all namespaces
		../../network.py clear
	done
}

# Ask for sudo password
if [ $(id -u) -ne 0 ]; then
	echo "Need to be called as root or with sudo."
	exit 1
fi

# need to open more files (especially for traffic measurement processes)
ulimit -Sn 4096

# artificial data sets
for files in '../../data/line/' '../../data/grid4/' '../../data/rtree/'; do
	for protocol in 'olsr2' 'batman-adv' 'yggdrasil' 'babel' 'bmx6' 'bmx7' 'cjdns'; do
		run_test "$protocol" "$files"
	done
done

# freifunk data set
for protocol in 'olsr2' 'batman-adv' 'yggdrasil' 'babel' 'bmx6' 'bmx7' 'cjdns'; do
	run_test "$protocol" "../../data/freifunk/freifunk"
done
