#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

./csv_merge.py ${prefix}traffic1-batman-adv-grid4.csv ${prefix}traffic1-batman-adv-grid4_new.csv --span 10 --columns-range 'tx_bytes'

gnuplot -e "
	set title \"Traffic for batman-adv on grid4 with 100MBit/s - 1ms latency links.\n1. Start daemons, 2. Wait 300s, 3. Measure for 60s with 300 pings (10 times for mean value and value range)\";	\
	set grid;																			\
	set term png;																		\
	set terminal png size 1280,960;														\
	set output '${prefix}traffic1-batman-adv-grid4.png';									\
	set key spacing 3 font 'Helvetica, 18';												\
	set xlabel '# number of nodes';														\
	set ylabel 'tx per node [KB/s]';												\
	set y2label 'ping arrival [%]';													\
	set termoption lw 3;																\
	set xtics 0, 50;																	\
	set xrange [0:1050]; \
	set y2tics 0, 10;																	\
	set y2range [0:100]; \
	set ytics nomirror;																	\
	plot																				\
	'${prefix}traffic1-batman-adv-grid4_new.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('duration_ms') / 1000)) / column('node_count')):((((column('tx_bytes_range') / 1000) / (column('duration_ms') / 1000)) / column('node_count')) / 2) with errorbars notitle axis x1y1,	\
	'${prefix}traffic1-batman-adv-grid4_new.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('duration_ms') / 1000)) / column('node_count')) with linespoints title 'tx per node [KB/s]' axis x1y1,					\
	'${prefix}traffic1-batman-adv-grid4_new.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'pings arrived [%]' axis x1y2;	\
"
