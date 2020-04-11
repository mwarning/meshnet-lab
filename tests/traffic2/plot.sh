#!/bin/sh

../tools/csv_merge.py traffic2-batman-adv-lattice4.csv traffic2-batman-adv-lattice4_new.csv --span 10 --columns-range 'rx_node_bs'

gnuplot -e "
	set title \"Traffic for batman-adv on lattice4\n1. Start daemons, 2. Wait 300s, 3. Measure for 60s with 300 pings (10 times for value range)\";	\
	set grid;																			\
	set term png;																		\
	set terminal png size 1280,960;														\
	set output 'traffic2-batman-adv-lattice4.png';									\
	set key spacing 3 font 'Helvetica, 18';												\
	set xlabel '# number of nodes';														\
	set ylabel 'ingress per node [KB/s]';												\
	set y2label 'packet arrival [%]';													\
	set termoption lw 3;																\
	set xtics 0, 100;																	\
	set y2tics 0, 10;																	\
	set ytics nomirror;																	\
	plot																				\
	'traffic2-batman-adv-lattice4_new.csv' using (column('node_count')):(column('rx_bs') / 1000 / column('node_count')):(column('rx_node_bs_range') / 2.0) with errorbars title '' axis x1y1,	\
	'traffic2-batman-adv-lattice4_new.csv' using (column('node_count')):(column('rx_bs') / 1000 / column('node_count')) with linespoints title 'ingress per node [KB/s]' axis x1y1,					\
	'traffic2-batman-adv-lattice4_new.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'pings arrived [%]' axis x1y2;	\
"
