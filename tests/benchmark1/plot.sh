#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Benchmark to see how many nodes of a grid4 network the host system can sustain.\"; \
	set grid; \
	set term png; \
	set terminal png size 800,600; \
	set output '${prefix}benchmark1.png'; \
	set key spacing 1 font 'Helvetica, 18'; \
	set xlabel '# number of nodes'; \
	set ylabel 'ping arrival [%]'; \
	set termoption lw 3; \
	set xrange [0:500]; \
	set xtics 0, 50; \
	set yrange [0:100]; \
	set ytics 0, 10; \
	plot \
	'${prefix}benchmark1-babel.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'babel', \
	'${prefix}benchmark1-batman-adv.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'batman-adv', \
	'${prefix}benchmark1-yggdrasil.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'yggdrasil', \
	;
"
