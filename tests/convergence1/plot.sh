#!/bin/sh

for dataid in 'line' 'rtree' 'lattice4'; do
	gnuplot -e "
		set title \"Reachability on a $dataid of 100 nodes\nno packet loss, 100 pings over 5-6 seconds\";	\
		set grid;												\
		set term png;											\
		set terminal png size 1280,960;							\
		set output 'convergence-$dataid.png';					\
		set key spacing 3 font 'Helvetica, 18';					\
		set ylabel '% of packets arrived';						\
		set xlabel 'seconds after start';						\
		set termoption lw 3;									\
		set yrange [0:110];										\
		plot													\
		'convergence-none-$dataid.tsv' using 3:(100*\$7/\$6) with linespoints title 'none',				\
		'convergence-batman-adv-$dataid.tsv' using 3:(100*\$7/\$6) with linespoints title 'batman-adv',	\
		'convergence-babel-$dataid.tsv' using 3:(100*\$7/\$6) with linespoints title 'babel',			\
		'convergence-yggdrasil-$dataid.tsv' using 3:(100*\$7/\$6) with linespoints title 'yggdrasil',	\
		'convergence-olsr2-$dataid.tsv' using 3:(100*\$7/\$6) with linespoints title 'olsr2',			\
		'convergence-bmx6-$dataid.tsv' using 3:(100*\$7/\$6) with linespoints title 'bmx6',				\
		'convergence-bmx7-$dataid.tsv' using 3:(100*\$7/\$6) with linespoints title 'bmx7';				\
	"
done
