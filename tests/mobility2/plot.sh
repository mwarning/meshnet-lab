#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

title='Mobility2 Test for 50 randomly placed nodes in a 1x1km square.\nMove in random directions of 50-400m in 50m increments.\nWait and measure ping arrival over 60s in 10s intervals each time.\n100MBit/s - 1ms latency links.'

# progress of packet arrival rate
gnuplot -e "
	set title \"$title\" noenhanced; \
	set terminal pngcairo size 1280,960; \
	set output '${prefix}mobility2_arrival_progress.png'; \
	set grid back lc rgb '#808080' lt 0 lw 1; \
	set border 3 back lc rgb '#808080' lt 1; \
	set tics nomirror; \
	set key spacing 2 font 'sans, 18' top right; \
	set ylabel 'packet arrival [%]'; \
	set termoption lw 3; \
	plot \
	'${prefix}mobility2-yggdrasil-0.3.16.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'dark-violet' title 'yggdrasil-0.3.16 [%]' axis x1y1, \
	'${prefix}mobility2-yggdrasil-0.4.7.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'skyblue' title 'yggdrasil-0.4.7 [%]' axis x1y1, \
	'${prefix}mobility2-yggdrasil-0.5.5.csv' using 0:(column('packets_arrived_pc')) with linespoints linetype rgb 'dark-yellow' title 'yggdrasil-0.5.5 [%]' axis x1y1 \
	;\
"

# progress of tx bytes rate
gnuplot -e "
	set title \"$title\" noenhanced; \
	set terminal pngcairo size 1280,960; \
	set output '${prefix}mobility2_traffic_progress.png'; \
	set grid back lc rgb '#808080' lt 0 lw 1; \
	set border 3 back lc rgb '#808080' lt 1; \
	set tics nomirror; \
	set key spacing 2 font 'sans, 18' top right; \
	set ylabel 'tx traffic per node [KB/s]'; \
	set termoption lw 3; \
	plot \
	'${prefix}mobility2-yggdrasil-0.3.16.csv' using 0:(((column('tx_bytes') / 1000) / (column('time_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'dark-violet' title 'yggdrasil-0.3.16 [%]' axis x1y1, \
	'${prefix}mobility2-yggdrasil-0.4.7.csv' using 0:(((column('tx_bytes') / 1000) / (column('time_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'skyblue' title 'yggdrasil-0.4.7 [%]' axis x1y1, \
	'${prefix}mobility2-yggdrasil-0.5.5.csv' using 0:(((column('tx_bytes') / 1000) / (column('time_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'dark-yellow' title 'yggdrasil-0.5.5 [%]' axis x1y1 \
	;\
"

# packet arrival stats
gnuplot -e "
	set terminal pngcairo size 1280,480; \
	set output '${prefix}mobility2_arrival_stats.png'; \
	set grid back lc rgb '#808080' lt 0 lw 1; \
	set border 3 back lc rgb '#808080' lt 1; \
	set tics nomirror; \
	array protocols = ['yggdrasil-0.3.16', 'yggdrasil-0.4.7', 'yggdrasil-0.5.5']; \
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
	set terminal pngcairo size 1280,480; \
	set output '${prefix}mobility2_traffic_stats.png'; \
	set grid back lc rgb '#808080' lt 0 lw 1; \
	set border 3 back lc rgb '#808080' lt 1; \
	set tics nomirror; \
	array protocols = ['yggdrasil-0.3.16', 'yggdrasil-0.4.7', 'yggdrasil-0.5.5']; \
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
