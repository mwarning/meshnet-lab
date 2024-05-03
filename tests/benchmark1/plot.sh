#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Benchmark to see how many nodes of a grid4 network the host system can sustain.\"; \
	set terminal pngcairo size 1280,960; \
	set output '${prefix}benchmark1.png'; \
	set grid back lc rgb '#808080' lt 0 lw 1; \
	set border 3 back lc rgb '#808080' lt 1; \
	set tics nomirror; \
	set key left center spacing 1 font 'sans, 18'; \
	set xlabel '# number of nodes'; \
	set ylabel 'ping arrival [%]'; \
	set termoption lw 3; \
	set xrange [0:1500]; \
	set xtics 0, 100; \
	set yrange [0:100]; \
	set ytics 0, 10; \
	plot \
	'${prefix}benchmark1-babel.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'babel', \
	'${prefix}benchmark1-batman-adv.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'batman-adv', \
	'${prefix}benchmark1-yggdrasil.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'yggdrasil', \
	;
"
