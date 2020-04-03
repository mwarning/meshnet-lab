#!/bin/sh

# exit on any error
set -ex

run_test() {
	local protocol="$1"
	local dataid="$2"
	local tsvfile="convergence-$protocol-$dataid.tsv"
	local seed=42

	for graphfile in ${dataid}*.json; do
		local name=$(basename "$graphfile" | rev | cut -d'-' -f2- | rev)
		local nodes=$(expr 0 + $(basename "$graphfile" | rev | cut -d'-' -f1 | rev | cut -d'.' -f 1))
		local duration=5
		local samples=100

		# clear (just in case)
		../../network.py clear

		# Setup the network structure of namespaces
		../../network.py 'change' none "$graphfile"

		# wait for network stacks etc. to set settle
		sleep 10

		offset=0
		while [ $offset -le 60 ]; do
			offset=$((offset + 2))
			# Start mesh program in every namespace
			../../tests.py --verbosity 'verbose' "$protocol" start

			sleep $offset

			echo -n "$name		$nodes		$offset		$samples		$duration		" >> $tsvfile
			../../tests.py --verbosity 'verbose' --out "$tsvfile" --seed "$seed" "$protocol" "test" --duration $duration --samples $samples

			# Stop batman-adv
			../../tests.py --verbosity 'verbose' "$protocol" stop
		done

		# Remove all namespaces
		../../network.py clear
	done
}


# Ask for sudo password
if [ $(id -u) -ne 0 ]; then
	echo "Need to 	be called as root or with sudo."
	exit 1
fi

# need to open more files (especially for convergence measurement processes)
ulimit -Sn 4096

# artificial data sets
for dataid in 'line' 'rtree' 'lattice4'; do
	for protocol in 'none' 'olsr2' 'batman-adv' 'yggdrasil' 'babel' 'bmx6' 'bmx7'; do
		run_test "$protocol" "$dataid"
	done
done

# freifunk data set
for protocol in 'none' 'olsr2' 'yggdrasil' 'bmx7' 'batman-adv' 'babel'; do
	run_test "$protocol" "freifunk"
done
