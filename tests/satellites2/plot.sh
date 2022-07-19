#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Reachability and traffix between 6 ground stations and 3 orbits of 30 satellites.\nA span of 2 hours is simulated at different speedups.\"; \
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}satellites2.png'; \
	set key spacing 2 font 'Helvetica, 18'center right; \
	set ylabel 'packets arrived [%]'; \
	set yrange [0:105]; \
	set xlabel 'speedup'; \
	set y2label 'tx [kB/s]'; \
	set autoscale y2; \
	set ytics nomirror; \
	set y2tics; \
	set termoption lw 3; \
	plot \
	'${prefix}satellites2-batman-adv.csv' using (column('speedup')):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'skyblue' title 'batman-adv' axis x1y1, \
	'${prefix}satellites2-batman-adv.csv' using (column('speedup')):(column('tx_bytes') / 1000) with points linetype rgb 'skyblue' title 'batman-adv traffic' axis x1y2, \
	'${prefix}satellites2-bmx6.csv' using (column('speedup')):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'dark-yellow' title 'bmx6' axis x1y1, \
	'${prefix}satellites2-bmx6.csv' using (column('speedup')):(column('tx_bytes') / 1000) with points linetype rgb 'dark-yellow' title 'bmx6 traffic' axis x1y2, \
	'${prefix}satellites2-bmx7.csv' using (column('speedup')):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'gold' title 'bmx7' axis x1y1, \
	'${prefix}satellites2-bmx7.csv' using (column('speedup')):(column('tx_bytes') / 1000) with points linetype rgb 'gold' title 'bmx7 traffic' axis x1y2, \
	'${prefix}satellites2-olsr1.csv' using (column('speedup')):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'coral' title 'olsr1' axis x1y1, \
	'${prefix}satellites2-olsr1.csv' using (column('speedup')):(column('tx_bytes') / 1000) with points linetype rgb 'coral' title 'olsr1 traffic' axis x1y2, \
	'${prefix}satellites2-olsr2.csv' using (column('speedup')):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'green' title 'olsr2' axis x1y1, \
	'${prefix}satellites2-olsr2.csv' using (column('speedup')):(column('tx_bytes') / 1000) with points linetype rgb 'green' title 'olsr2 traffic' axis x1y2, \
	'${prefix}satellites2-yggdrasil.csv' using (column('speedup')):(100 * column('packets_received') / column('packets_send')) with linespoints linetype rgb 'purple' title 'yggdrasil' axis x1y1, \
	'${prefix}satellites2-yggdrasil.csv' using (column('speedup')):(column('tx_bytes') / 1000) with points linetype rgb 'purple' title 'yggdrasil traffic' axis x1y2 \
; \
"
