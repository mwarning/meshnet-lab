#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

for id in 'line' 'rtree' 'grid4'; do
	gnuplot -e "
		set title \"Reachability on a $id of 50 nodes with 100MBit/s - 1ms latency links.\n200 random pings in 2 seconds for each test point.\"; \
		set grid; \
		set term png; \
		set terminal png size 1280,960; \
		set output '${prefix}convergence1-$id.png'; \
		set key spacing 2 font 'Helvetica, 18'center right; \
		set ylabel 'packets arrived [%]'; \
		set xlabel 'wait after start [sec]'; \
		set termoption lw 3; \
		set ytics 10; \
		plot \
		'${prefix}convergence1-babel-$id.csv' using (column('offset_ms') / 1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-violet' title 'babel', \
		'${prefix}convergence1-batman-adv-$id.csv' using (column('offset_ms') / 1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'skyblue' title 'batman-adv', \
		'${prefix}convergence1-bmx6-$id.csv' using (column('offset_ms') / 1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-yellow' title 'bmx6', \
		'${prefix}convergence1-bmx7-$id.csv' using (column('offset_ms') / 1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'gold' title 'bmx7', \
		'${prefix}convergence1-cjdns-$id.csv' using (column('offset_ms') / 1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-red' title 'cjdns', \
		'${prefix}convergence1-olsr1-$id.csv' using (column('offset_ms') / 1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'coral' title 'olsr1', \
		'${prefix}convergence1-olsr2-$id.csv' using (column('offset_ms') / 1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'green' title 'olsr2', \
		'${prefix}convergence1-ospf-$id.csv' using (column('offset_ms') / 1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'green' title 'ospf', \
		'${prefix}convergence1-yggdrasil-$id.csv' using (column('offset_ms') / 1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'purple' title 'yggdrasil' \
	; \
	"
done
