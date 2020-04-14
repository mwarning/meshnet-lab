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
		local csvfile="${prefix}convergence1-$protocol-$name.csv"
		local duration=5
		local samples=100

		echo "$(date): start $protocol on $(basename \"$graphfile\")"

		# file empty or does not exists => write header name
		if [ ! -s "$csvfile" ]; then
			echo 'offset_sec	' >> $csvfile
		fi

		# clear (just in case)
		../../network.py clear

		# Setup the network structure of namespaces
		../../network.py --ignore-tc 'change' none "$graphfile"

		# wait for network stacks etc. to set settle
		sleep 10

		offset=0
		while [ $offset -le 60 ]; do
			offset=$((offset + 2))
			../../tests.py --verbosity 'verbose' --csv-delimiter '	' --csv-out "$csvfile" --seed "$seed" 'none' "test" --duration $duration --wait $offset --samples $samples
		done

		# Remove all namespaces
		../../network.py clear
	done
}


# Ask for sudo password
if [ $(id -u) -ne 0 ]; then
	echo "Need to be called as root or with sudo."
	exit 1
fi

# need to open more files (especially for convergence measurement processes)
ulimit -Sn 4096

# artificial data sets
for files in 'line/line-0100' 'rtree/rtree-0100' 'grid4/grid4-0100'; do
	for protocol in 'olsr2' 'batman-adv' 'yggdrasil' 'babel' 'bmx6' 'bmx7' 'cjdns'; do
		run_test "$protocol" "../../data/$files"
	done
done
