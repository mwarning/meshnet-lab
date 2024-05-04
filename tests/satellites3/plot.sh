#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Reachability between 6 ground stations and 3 orbits of 30 satellites.\nAt 2x real time with packet loss of 0-10%.\"; \
	set terminal pngcairo size 1280,960; \
	set output '${prefix}satellites3.png'; \
	set grid back lc rgb '#808080' lt 0 lw 1; \
	set border 3 back lc rgb '#808080' lt 1; \
	set tics nomirror; \
	set key spacing 2 font 'sans, 18'center right; \
	set ylabel 'packets arrived [%]'; \
	set yrange [0:105]; \
	set xlabel 'real_time [sec]'; \
	set termoption lw 3; \
	plot \
	'${prefix}satellites3-batman-adv.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'skyblue' title 'batman-adv', \
	'${prefix}satellites3-bmx6.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-yellow' title 'bmx6', \
	'${prefix}satellites3-bmx7.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'gold' title 'bmx7', \
	'${prefix}satellites3-cjdns.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-red' title 'cjdns', \
	'${prefix}satellites3-olsr1.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'coral' title 'olsr1', \
	'${prefix}satellites3-olsr2.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'green' title 'olsr2', \
	'${prefix}satellites3-yggdrasil.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'purple' title 'yggdrasil' \
; \
"
