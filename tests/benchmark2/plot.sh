#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

for topology in "rtree" "grid4" "grid8"; do
	gnuplot -e "
		set title \"Benchmark to see how many nodes of a ${topology} network the host system can sustain.\"; \
		set terminal pngcairo size 1280,960; \
		set output '${prefix}benchmark2.png'; \
		set grid back lc rgb '#808080' lt 0 lw 1; \
		set border 3 back lc rgb '#808080' lt 1; \
		set key left center spacing 1 font 'sans, 18'; \
		set xlabel '# number of nodes'; \
		set ylabel 'ping arrival [%]'; \
		set y2label '60s load average [cpu]'; \
		set y2range [0:10];
		set yrange [0:100]; \
		set y2tics 0, 1; \
		set ytics nomirror; \
		set termoption lw 3; \
		plot \
		'${prefix}benchmark2-babel-${topology}.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-violet' title 'babel [%]' axis x1y1, \
		'${prefix}benchmark2-babel-${topology}.csv' using (column('node_count')):(column('load1')) with linespoints dashtype 2 linewidth 1.2 linecolor rgb 'dark-violet' title 'babel [cpu]' axis x1y2, \
		\
		'${prefix}benchmark2-batman-adv-${topology}.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'skyblue' title 'batman-adv [%]' axis x1y1, \
		'${prefix}benchmark2-batman-adv-${topology}.csv' using (column('node_count')):(column('load1')) with linespoints dashtype 2 linewidth 1.2 linecolor rgb 'skyblue' title 'batman-adv [cpu]' axis x1y2, \
		\
		'${prefix}benchmark2-yggdrasil-${topology}.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'purple' title 'yggdrasil [%]' axis x1y1, \
		'${prefix}benchmark2-yggdrasil-${topology}.csv' using (column('node_count')):(column('load1')) with linespoints dashtype 2 linewidth 1.2 linecolor rgb 'purple' title 'yggdrasil [cpu]' axis x1y2, \
		;
	"
done
