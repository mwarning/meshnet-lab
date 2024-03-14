#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

for id in 'line' 'rtree' 'grid4'; do
	gnuplot -e "
		set title \"Reachability on a $id of 50 nodes with 100MBit/s - 1ms latency links.\n200 random pings in 2 seconds for each test point.\"; \
		set terminal pngcairo size 1280,960; \
		set output '${prefix}convergence1-$id.png'; \
		set grid back lc rgb '#808080' lt 0 lw 1; \
		set border 3 back lc rgb '#808080' lt 1; \
		set tics nomirror; \
		set key spacing 2 font 'sans, 18'center right; \
		set ylabel 'packets arrived [%]'; \
		set xlabel 'wait after start [sec]'; \
		set termoption lw 3; \
		set ytics 10; \
		plot \
		'${prefix}convergence1-yggdrasil-0.3.16-$id.csv' using (column('offset_ms') / 1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-violet' title 'yggdrasil-0.3.16', \
		'${prefix}convergence1-yggdrasil-0.4.7-$id.csv' using (column('offset_ms') / 1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-yellow' title 'yggdrasil-0.4.7', \
		'${prefix}convergence1-yggdrasil-0.5.5-$id.csv' using (column('offset_ms') / 1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'skyblue' title 'yggdrasil-0.5.5' \
	; \
	"
done
