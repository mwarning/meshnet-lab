#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Reachability between 6 ground stations and 3 orbits of 30 satellites.\nAt 2x real time.\"; \
	set terminal pngcairo size 1280,960; \
	set output '${prefix}satellites1.png'; \
	set grid back lc rgb '#808080' lt 0 lw 1; \
	set border 3 back lc rgb '#808080' lt 1; \
	set tics nomirror; \
	set key spacing 2 font 'sans, 18'center right; \
	set ylabel 'packets arrived [%]'; \
	set yrange [0:105]; \
	set xlabel 'real_time [sec]'; \
	set termoption lw 3; \
	plot \
	'${prefix}satellites1-yggdrasil-0.3.16.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'skyblue' title 'yggdrasil-0.3.16', \
	'${prefix}satellites1-yggdrasil-0.4.7.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-yellow' title 'yggdrasil-0.4.7', \
	'${prefix}satellites1-yggdrasil-0.5.5.csv' using (column('real_time_sec')/1000):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'gold' title 'yggdrasil-0.5.5' \
; \
"
