#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

../tools/csv_merge.py traffic2-batman-adv-lattice4.csv traffic2-batman-adv-lattice4_new.csv --span 10 --columns-range 'rx_bytes'

gnuplot -e "
	set title \"Traffic for batman-adv on lattice4\n1. Start daemons, 2. Wait 300s, 3. Measure for 60s with 300 pings (10 times for mean value and value range)\";	\
	set grid;																			\
	set term png;																		\
	set terminal png size 1280,960;														\
	set output '${prefix}traffic2-batman-adv-lattice4.png';									\
	set key spacing 3 font 'Helvetica, 18';												\
	set xlabel '# number of nodes';														\
	set ylabel 'rx per node [KB/s]';												\
	set y2label 'packet arrival [%]';													\
	set termoption lw 3;																\
	set xtics 0, 100;																	\
	set y2tics 0, 10;																	\
	set ytics nomirror;																	\
	plot																				\
	'${prefix}traffic2-batman-adv-lattice4_new.csv' using (column('node_count')):(((column('rx_bytes') / 1000) / (column('duration_ms') / 1000)) / column('node_count')):(((column('rx_bytes_range') / 1000) / (column('duration_ms') / 1000)) / 2) with errorbars title '' axis x1y1,	\
	'${prefix}traffic2-batman-adv-lattice4_new.csv' using (column('node_count')):(((column('rx_bytes') / 1000) / (column('duration_ms') / 1000)) / column('node_count')) with linespoints title 'rx per node [KB/s]' axis x1y1,					\
	'${prefix}traffic2-batman-adv-lattice4_new.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'pings arrived [%]' axis x1y2;	\
"
