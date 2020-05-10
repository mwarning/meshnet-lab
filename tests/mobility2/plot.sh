#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Mobility1 Test.\n50 randomly placed nodes in a 1x1km square. Move in random directions of 50-400m in 50m increments. Wait and measure ping arrival over 60s in 10s intervals each time.\n100MBit/s - 1ms latency links.\" noenhanced; \
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}mobility2_arrival_stats.png'; \
	array protocols = ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'yggdrasil']; \
	array colors = ['dark-violet', 'skyblue', 'dark-yellow', 'dark-green', 'dark-red', 'coral', 'green', 'purple']; \
	array SUM[|protocols|]; \
	do for [i=1:|protocols|] { \
		file = 'mobility2-'.protocols[i].'.csv'; \
		stats file using (column('packets_arrived_pc')) nooutput; \
		SUM[i] = STATS_sum / STATS_records; \
	}; \
	set ylabel 'median packet arrival [%]'; \
	set style fill solid; \
  	set boxwidth 0.5; \
	set yrange [0:];
	plot SUM using 2:xtic(protocols[column(0)+1]) with boxes linetype rgb (colors[column(0)+1]); \
"

exit 0

gnuplot -e "
	set title \"Mobility1 Test.\n50 randomly placed nodes in a 1x1km square. Move in random directions of 50-400m in 50m increments. Wait and measure ping arrival over 60s in 10s intervals each time.\n100MBit/s - 1ms latency links.\" noenhanced; \
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}mobility2_traffic_stats.png'; \
	array protocols = ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'yggdrasil']; \
	array colors = ['dark-violet', 'skyblue', 'dark-yellow', 'dark-green', 'dark-red', 'coral', 'green', 'purple']; \
	array SUM[|protocols|]; \
	do for [i=1:|protocols|] { \
		file = 'mobility2-'.protocols[i].'.csv'; \
		stats file using (column('tx_bytes')) nooutput; \
		bytes = STATS_sum; \
		stats file using (column('time_ms')) nooutput; \
		duration_ms = STATS_sum; \
		SUM[i] = (bytes / 1000) / duration_ms; \
	}; \
	set ylabel 'tx [KB/s]'; \
	set style fill solid; \
  	set boxwidth 0.5; \
	set yrange [0:];
	plot SUM using 2:xtic(protocols[column(0)+1]) with boxes linetype rgb (colors[column(0)+1]); \
"

exit 0

gnuplot -e "
	set title \"Mobility1 Test.\n50 randomly placed nodes in a 1x1km square. Move in random directions of 50-400m in 50m increments. Wait and measure over 60s in 10s intervals each time.\n100MBit/s - 1ms latency links.\" noenhanced; \
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}mobility2.png'; \
	set key spacing 2 font 'Helvetica, 18' top left; \
	set ylabel 'tx [KB/s]'; \
	set termoption lw 3; \
	plot \
	'${prefix}mobility2-babel.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'dark-violet' title 'babel [%]' axis x1y1, \
	'${prefix}mobility2-batman-adv.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'skyblue' title 'batman-adv [%]' axis x1y1, \
	'${prefix}mobility2-bmx6.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'dark-yellow' title 'bmx6 [%]' axis x1y1, \
	'${prefix}mobility2-bmx7.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'dark-green' title 'bmx7 [%]' axis x1y1, \
	'${prefix}mobility2-cjdns.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'dark-red' title 'cjdns [%]' axis x1y1, \
	'${prefix}mobility2-olsr1.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'coral' title 'olsr1 [%]' axis x1y1, \
	'${prefix}mobility2-olsr2.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'green' title 'olsr2 [%]' axis x1y1, \
	'${prefix}mobility2-yggdrasil.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'purple' title 'yggdrasil [%]' axis x1y1 \
	;\
"