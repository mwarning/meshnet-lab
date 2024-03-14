#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Reachability and traffic between 6 ground stations and 3 orbits of 30 satellites.\nA span of 2 hours is simulated at different speedups.\"; \
	set terminal pngcairo size 1280,960; \
	set output '${prefix}satellites2.png'; \
	set grid back lc rgb '#808080' lt 0 lw 1; \
	set border 3 back lc rgb '#808080' lt 1; \
	set tics nomirror; \
	set key spacing 2 font 'sans, 18'center right; \
	set ylabel 'packets arrived [%]'; \
	set yrange [0:105]; \
	set xlabel 'speedup'; \
	set y2label 'tx [kB/s]'; \
	set autoscale y2; \
	set ytics nomirror; \
	set y2tics; \
	set termoption lw 3; \
	plot \
	'${prefix}satellites2-yggdrasil-0.3.16.csv' using (column('speedup')):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'skyblue' title 'yggdrasil-0.3.16' axis x1y1, \
	'${prefix}satellites2-yggdrasil-0.4.7.csv' using (column('speedup')):(column('tx_bytes') / 1000) with points linetype rgb 'skyblue' title 'yggdrasil-0.4.7 traffic' axis x1y2, \
	'${prefix}satellites2-yggdrasil-0.5.5.csv' using (column('speedup')):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-yellow' title 'yggdrasil-0.5.5' axis x1y1 \
; \
"
