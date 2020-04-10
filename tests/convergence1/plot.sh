#!/bin/sh

for id in 'line' 'rtree' 'lattice4'; do
	gnuplot -e "
		set title \"Reachability on a $id of 100 nodes.\nLinks without packet loss, 100 random pings over 5-6 seconds\";	\
		set grid;												\
		set term png;											\
		set terminal png size 1280,960;							\
		set output 'convergence-$id.png';					\
		set key spacing 3 font 'Helvetica, 18';					\
		set ylabel 'packets arrived [%]';						\
		set xlabel 'wait after start [sec]';					\
		set termoption lw 3;									\
		set yrange [-5:105];									\
		plot													\
		'convergence-batman-adv-$id.csv' using (column('offset_sec')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'batman-adv',	\
		'convergence-babel-$id.csv' using (column('offset_sec')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'babel',			\
		'convergence-yggdrasil-$id.csv' (column('offset_sec')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'yggdrasil',	\
		'convergence-olsr2-$id.csv' using (column('offset_sec')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'olsr2',			\
		'convergence-bmx6-$id.csv' using (column('offset_sec')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'bmx6',				\
		'convergence-bmx7-$id.csv' using (column('offset_sec')):(100 * column('packets_received') / column('packets_send')) with linespoints title 'bmx7';				\
	"
done
