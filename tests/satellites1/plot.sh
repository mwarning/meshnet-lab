#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Reachability between 6 ground stations and 3 orbits of 30 satellites.\nAt 2x real time.\"; \
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}satellites1.png'; \
	set key spacing 2 font 'Helvetica, 18'center right; \
	set ylabel 'packets arrived [%]'; \
	set yrange [0:105]; \
	set xlabel 'real_time [sec]'; \
	set termoption lw 3; \
	plot \
	'${prefix}satellites1-batman-adv.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'skyblue' title 'batman-adv', \
	'${prefix}satellites1-bmx6.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-yellow' title 'bmx6', \
	'${prefix}satellites1-bmx7.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'gold' title 'bmx7', \
	'${prefix}satellites1-cjdns.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-red' title 'cjdns', \
	'${prefix}satellites1-olsr1.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'coral' title 'olsr1', \
	'${prefix}satellites1-olsr2.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'green' title 'olsr2', \
	'${prefix}satellites1-yggdrasil.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'purple' title 'yggdrasil' \
; \
"
