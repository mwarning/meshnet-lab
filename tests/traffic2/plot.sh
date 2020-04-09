#!/bin/sh

../tools/variance.py traffic-batman-adv-lattice4.tsv traffic-batman-adv-lattice4_sd.tsv --span 10 --column 'ingress_avg_node_kbs'

gnuplot -e "
	set title \"Traffic for batman-adv on lattice4\n1. Start daemons, 2. Wait 300s, 3. Measure for 60s with 300 pings (10 times)\";	\
	set grid;																			\
	set term png;																		\
	set terminal png size 1280,960;														\
	set output 'traffic-batman-adv-lattice4_sd.png';									\
	set key spacing 3 font 'Helvetica, 18';												\
	set ylabel 'kB/s per node (ingress)';												\
	set xlabel '# number of nodes';														\
	set termoption lw 3;																\
	plot																				\
	'traffic-batman-adv-lattice4_sd.tsv' using (column('node_count')):(column('ingress_avg_node_kbs')):(column('ingress_avg_node_kbs_sd') / 2.0) with errorbars title '',	\
	'traffic-batman-adv-lattice4_sd.tsv' using (column('node_count')):(column('ingress_avg_node_kbs')) with linespoints title 'batman-adv';	\
"
