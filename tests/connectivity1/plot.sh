#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

# merge rows
for nodes in 10 20 30 40 50 ; do
	./csv_merge.py ${prefix}connectivity1-${nodes}.csv ${prefix}connectivity1-${nodes}_merged.csv --span 100
done

gnuplot -e "
	set title \"Connectivity of nodes on a 1x1 km square with a fixed range.\nMedian of 100 values for each point.\"; \
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}connectivity1.png'; \
	set key spacing 2 font 'Helvetica, 18' center right; \
	set xlabel 'Connection range [m]'; \
	set ylabel 'connectivity [%]'; \
	set xtics 50; \
	set ytics 10; \
	set termoption lw 3; \
	plot \
	'${prefix}connectivity1-10_merged.csv' using (1000 * column('max_range')):(column('connectivity_per')) with linespoints linetype rgb 'violet' title '10 nodes', \
	'${prefix}connectivity1-20_merged.csv' using (1000 * column('max_range')):(column('connectivity_per')) with linespoints linetype rgb 'orange' title '20 nodes', \
	'${prefix}connectivity1-30_merged.csv' using (1000 * column('max_range')):(column('connectivity_per')) with linespoints linetype rgb 'brown' title '30 nodes', \
	'${prefix}connectivity1-40_merged.csv' using (1000 * column('max_range')):(column('connectivity_per')) with linespoints linetype rgb 'dark-green' title '40 nodes', \
	'${prefix}connectivity1-50_merged.csv' using (1000 * column('max_range')):(column('connectivity_per')) with linespoints linetype rgb 'dark-blue' title '50 nodes', \
	;\
"
