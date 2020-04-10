#!/bin/sh

# exit on any error
set -ex

# to distinguish multiple runs (if needed)
prefix="$1"

run_test() {
	local protocol="$1"
	local files="$2"
	local seed=42

	for graphfile in ${files}-*.json; do
		local name=$(basename "$graphfile" | rev | cut -d'-' -f2- | rev)
		local links=$(../tools/json_count.py "$graphfile" 'count-links')
		local csvfile="${prefix}traffic-$protocol-$name.csv"
		local duration_sec=60

		echo "$(date): start $protocol on $(basename \"$graphfile\")"

		# clear (just in case)
		../../network.py clear

		# Setup the network structure of namespaces
		../../network.py --ignore-tc 'change' none "$graphfile"

		# wait for network stacks etc. to set settle
		sleep 10

		# 10 runs
		for _ in 0 1 2 3 4 5 6 7 8 9; do
			# Start mesh program in every namespace
			../../tests.py --verbosity 'verbose' "$protocol" start

			# Run the ping test
			../../tests.py --verbosity 'verbose' --csv-delimiter '	' --csv-out "$csvfile" --seed "$seed" "$protocol" "test" --duration $duration_sec --wait 60 --samples $links

			# Stop batman-adv
			../../tests.py --verbosity 'verbose' "$protocol" stop
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

# need to open more files (especially for traffic measurement processes)
ulimit -Sn 4096

# just in case
sysctl -w net.ipv6.neigh.default.gc_thresh1=$((8 * 128))
sysctl -w net.ipv6.neigh.default.gc_thresh2=$((8 * 512))
sysctl -w net.ipv6.neigh.default.gc_thresh3=$((8 * 1024))


run_test 'batman-adv' '../../data/lattice4/lattice4'
