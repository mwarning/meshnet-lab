#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

title='Mobility2 Test for 50 randomly placed nodes in a 1x1km square.\nMove in random directions of 50-400m in 50m increments.\nWait and measure ping arrival over 60s in 10s intervals each time.\n100MBit/s - 1ms latency links.'

# progress of packet arrival rate
gnuplot -e "
	set title \"$title\" noenhanced; \
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}mobility2_arrival_progress.png'; \
	set key spacing 2 font 'Helvetica, 18' top right; \
	set ylabel 'packet arrival [%]'; \
	set termoption lw 3; \
	plot \
	'${prefix}mobility2-babel.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'dark-violet' title 'babel [%]' axis x1y1, \
	'${prefix}mobility2-batman-adv.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'skyblue' title 'batman-adv [%]' axis x1y1, \
	'${prefix}mobility2-bmx6.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'dark-yellow' title 'bmx6 [%]' axis x1y1, \
	'${prefix}mobility2-bmx7.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'gold' title 'bmx7 [%]' axis x1y1, \
	'${prefix}mobility2-cjdns.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'dark-red' title 'cjdns [%]' axis x1y1, \
	'${prefix}mobility2-olsr1.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'coral' title 'olsr1 [%]' axis x1y1, \
	'${prefix}mobility2-olsr2.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'green' title 'olsr2 [%]' axis x1y1, \
	'${prefix}mobility2-ospf.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'dark-green' title 'ospf [%]' axis x1y1, \
	'${prefix}mobility2-yggdrasil.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'purple' title 'yggdrasil [%]' axis x1y1 \
	;\
"

# progress of tx bytes rate
gnuplot -e "
	set title \"$title\" noenhanced; \
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}mobility2_traffic_progress.png'; \
	set key spacing 2 font 'Helvetica, 18' top right; \
	set ylabel 'tx traffic per node [KB/s]'; \
	set termoption lw 3; \
	plot \
	'${prefix}mobility2-babel.csv' using 0:(((column('tx_bytes') / 1000) / (column('time_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'dark-violet' title 'babel [%]' axis x1y1, \
	'${prefix}mobility2-batman-adv.csv' using 0:(((column('tx_bytes') / 1000) / (column('time_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'skyblue' title 'batman-adv [%]' axis x1y1, \
	'${prefix}mobility2-bmx6.csv' using 0:(((column('tx_bytes') / 1000) / (column('time_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'dark-yellow' title 'bmx6 [%]' axis x1y1, \
	'${prefix}mobility2-bmx7.csv' using 0:(((column('tx_bytes') / 1000) / (column('time_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'gold' title 'bmx7 [%]' axis x1y1, \
	'${prefix}mobility2-cjdns.csv' using 0:(((column('tx_bytes') / 1000) / (column('time_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'dark-red' title 'cjdns [%]' axis x1y1, \
	'${prefix}mobility2-olsr1.csv' using 0:(((column('tx_bytes') / 1000) / (column('time_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'coral' title 'olsr1 [%]' axis x1y1, \
	'${prefix}mobility2-olsr2.csv' using 0:(((column('tx_bytes') / 1000) / (column('time_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'green' title 'olsr2 [%]' axis x1y1, \
	'${prefix}mobility2-ospf.csv' using 0:(((column('tx_bytes') / 1000) / (column('time_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'dark-green' title 'ospf [%]' axis x1y1, \
	'${prefix}mobility2-yggdrasil.csv' using 0:(((column('tx_bytes') / 1000) / (column('time_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'purple' title 'yggdrasil [%]' axis x1y1 \
	;\
"

# packet arrival stats
gnuplot -e "
	set grid; \
	set term png; \
	set terminal png size 1280,480; \
	set output '${prefix}mobility2_arrival_stats.png'; \
	array protocols = ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'ospf', 'yggdrasil']; \
	array SUM[|protocols|]; \
	do for [i=1:|protocols|] { \
		file = '${prefix}mobility2-'.protocols[i].'.csv'; \
		stats file using (column('packets_arrived_pc')) nooutput; \
		SUM[i] = STATS_sum / STATS_records; \
	}; \
	set nokey; \
	set ylabel 'median packet arrival [%]'; \
	set style fill solid; \
	set boxwidth 0.5; \
	set yrange [0:]; \
	set palette defined (0 'dark-violet', 1 'skyblue', 2 'dark-yellow', 3 'gold', 4 'dark-red', 5 'coral', 6 'green', 7 'dark-green', 8 'purple'); \
	set cbrange [0:8]; \
	unset colorbox; \
	plot SUM using 0:2:(column(0)):xticlabels(protocols[column(0)+1]) with boxes linecolor palette; \
"

# tx traffic stats
gnuplot -e "
	set grid; \
	set term png; \
	set terminal png size 1280,480; \
	set output '${prefix}mobility2_traffic_stats.png'; \
	array protocols = ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'ospf', 'yggdrasil']; \
	array SUM[|protocols|]; \
	do for [i=1:|protocols|] { \
		node_count = 50; \
		file = '${prefix}mobility2-'.protocols[i].'.csv'; \
		stats file using (column('tx_bytes')) nooutput; \
		tx_bytes_sum = STATS_sum; \
		stats file using (column('time_ms')) nooutput; \
		time_ms_sum = STATS_sum; \
		SUM[i] = ((tx_bytes_sum / 1000) / (time_ms_sum / 1000)) / node_count; \
	}; \
	set nokey; \
	set ylabel 'median tx traffic per node [KB/s]'; \
	set style fill solid; \
	set boxwidth 0.5; \
	set yrange [0:]; \
	set palette defined (0 'dark-violet', 1 'skyblue', 2 'dark-yellow', 3 'gold', 4 'dark-red', 5 'coral', 6 'green', 7 'dark-green', 8 'purple'); \
	set cbrange [0:8]; \
	unset colorbox; \
	plot SUM using 0:2:(column(0)):xticlabels(protocols[column(0)+1]) with boxes linecolor palette; \
"

# combine graphs
convert	\( "${prefix}mobility2_arrival_progress.png" "${prefix}mobility2_arrival_stats.png" -append \) \
		\( "${prefix}mobility2_traffic_progress.png" "${prefix}mobility2_traffic_stats.png" -append \) \
		+append "${prefix}mobility2.png"
