#!/bin/sh

for id in 'line' 'rtree' 'lattice4'; do
	gnuplot -e "
		set title \"Traffic by routing protocol on $id\n1. Start daemons, 2. Wait 300s, 3. Measure for 60s with 300 pings\";	\
		set grid;																			\
		set term png;																		\
		set terminal png size 1280,960;														\
		set output 'traffic-$id.png';														\
		set key spacing 3 font 'Helvetica, 18';												\
		set ylabel 'kB/s per node (egress)';												\
		set xlabel '# number of nodes';														\
		set termoption lw 3;																\
		plot																				\
		'traffic-none-$id.tsv' using (column('node_count')):(column('ingress_avg_node_kbs')) with linespoints title 'none',					\
		'traffic-batman-adv-$id.tsv' using (column('node_count')):(column('ingress_avg_node_kbs')) with linespoints title 'batman-adv',		\
		'traffic-babel-$id.tsv' using (column('node_count')):(column('ingress_avg_node_kbs')) with linespoints title 'babel',				\
		'traffic-yggdrasil-$id.tsv' using (column('node_count')):(column('ingress_avg_node_kbs')) with linespoints title 'yggdrasil',		\
		'traffic-olsr2-$id.tsv' using (column('node_count')):(column('ingress_avg_node_kbs')) with linespoints title 'olsr2',				\
		'traffic-bmx6-$id.tsv' using (column('node_count')):(column('ingress_avg_node_kbs')) with linespoints title 'bmx6',					\
		'traffic-bmx7-$id.tsv' using (column('node_count')):(column('ingress_avg_node_kbs')) with linespoints title 'bmx7';					\
	"
done
