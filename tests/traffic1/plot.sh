#!/bin/sh

for dataid in 'line' 'rtree' 'lattice4'; do
	gnuplot -e "
		set title \"Traffic by routing protocol over 60 seconds on $dataid\n300 seconds after setup up to 300 pings are performed in that time frame\";	\
		set grid;																			\
		set term png;																		\
		set terminal png size 1280,960;														\
		set output 'traffic-$dataid.png';													\
		set key spacing 3 font 'Helvetica, 18';												\
		set ylabel 'kB/s per node (egress)';												\
		set xlabel '# number of nodes';														\
		set termoption lw 3;																\
		plot																				\
		'traffic-none-$dataid.tsv' using 2:9 with linespoints title 'none',					\
		'traffic-batman-adv-$dataid.tsv' using 2:9 with linespoints title 'batman-adv',			\
		'traffic-babel-$dataid.tsv' using 2:9 with linespoints title 'babel',				\
		'traffic-yggdrasil-$dataid.tsv' using 2:9 with linespoints title 'yggdrasil',		\
		'traffic-olsr2-$dataid.tsv' using 2:9 with linespoints title 'olsr2',				\
		'traffic-bmx6-$dataid.tsv' using 2:9 with linespoints title 'bmx6',					\
		'traffic-bmx7-$dataid.tsv' using 2:9 with linespoints title 'bmx7';					\
	"
done
