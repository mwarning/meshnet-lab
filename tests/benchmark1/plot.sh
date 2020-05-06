#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Benchmark to see how many nodes of a grid4 network the host system can sustain.\"; \
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}benchmark1.png'; \
	set key spacing 3 font 'Helvetica, 18'; \
	set xlabel '# number of nodes'; \
	set ylabel 'tx per node [KB/s]'; \
	set y2label 'ping arrival [%]'; \
	set termoption lw 3; \
	set xtics 0, 50; \
	set xrange [0:1050]; \
	set y2tics 0, 10; \
	set y2range [0:100]; \
	set ytics nomirror; \
	plot \
	'${prefix}benchmark1-babel.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'babel' axis x1y2, \
	'${prefix}benchmark1-batman-adv.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'batman-adv' axis x1y2, \
	'${prefix}benchmark1-yggdrasil.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'yggdrasil' axis x1y2 \
	;
"
