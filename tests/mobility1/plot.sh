#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Mobility1 test of 20 nodes.\nEach test ~10 seconds after nodes moved randomly.\"; \
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}mobility1.png'; \
	set key spacing 1 font 'Helvetica, 12'; \
	set xlabel 'time [sec]'; \
	set ylabel 'packet arrival [%]'; \
	set yrange [-2:102]; \
	set termoption lw 3; \
	plot \
	'${prefix}mobility1-babel.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('packets_send'))) with linespoints title 'babel [%]' axis x1y1, \
	'${prefix}mobility1-batman-adv.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('packets_send'))) with linespoints title 'batman-adv [%]' axis x1y1, \
	'${prefix}mobility1-bmx6.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('packets_send'))) with linespoints title 'bmx6 [%]' axis x1y1, \
	'${prefix}mobility1-bmx7.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('packets_send'))) with linespoints title 'bmx7 [%]' axis x1y1, \
	'${prefix}mobility1-cjdns.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('packets_send'))) with linespoints title 'cjdns [%]' axis x1y1, \
	'${prefix}mobility1-olsr1.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('packets_send'))) with linespoints title 'olsr1 [%]' axis x1y1, \
	'${prefix}mobility1-olsr2.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('packets_send'))) with linespoints title 'olsr2 [%]' axis x1y1, \
	'${prefix}mobility1-yggdrasil.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('packets_send'))) with linespoints title 'yggdrasil [%]' axis x1y1 \
	;\
"
