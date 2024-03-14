#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Traffic for freifunk network topologies\"; \
	set terminal pngcairo size 1280,960; \
	set output '${prefix}freifunk1_traffic_stats.png'; \
	set grid back lc rgb '#808080' lt 0 lw 1; \
	set border 3 back lc rgb '#808080' lt 1; \
	set tics nomirror; \
	set key spacing 3 font 'sans, 18'; \
	set style data histogram; \
	set style histogram cluster gap 3; \
	set style fill solid border -1; \
	set ylabel 'tx per node [KB/s]'; \
	set yrange [0:]; \
	set termoption lw 3; \
	plot \
	'${prefix}freifunk1-yggdrasil-0.3.16.csv' using (((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')):xtic(1) with histogram linetype rgb 'dark-violet' title 'yggdrasil-0.3.16', \
	'${prefix}freifunk1-yggdrasil-0.4.7.csv' using (((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')):xtic(1) with histogram linetype rgb 'skyblue' title 'yggdrasil-0.4.7', \
	'${prefix}freifunk1-yggdrasil-0.5.5.csv' using (((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')):xtic(1) with histogram linetype rgb 'dark-yellow' title 'yggdrasil-0.5.5'; \
"

gnuplot -e "
	set title \"Packet arrival for freifunk network topologies\"; \
	set terminal pngcairo size 1280,960; \
	set output '${prefix}freifunk1_arrival_stats.png'; \
	set grid back lc rgb '#808080' lt 0 lw 1; \
	set border 3 back lc rgb '#808080' lt 1; \
	set tics nomirror; \
	set nokey; \
	set style data histogram; \
	set style histogram cluster gap 3; \
	set style fill solid border -1; \
	set ylabel 'packet arrival [%]'; \
	set yrange [0:100]; \
	set termoption lw 3; \
	plot \
	'${prefix}freifunk1-yggdrasil-0.3.16.csv' using (100 * (column('packets_received') / column('packets_send'))):xtic(1) with histogram linetype rgb 'dark-violet' title 'yggdrasil-0.3.16', \
	'${prefix}freifunk1-yggdrasil-0.4.7.csv' using (100 * (column('packets_received') / column('packets_send'))):xtic(1) with histogram linetype rgb 'skyblue' title 'yggdrasil-0.4.7', \
	'${prefix}freifunk1-yggdrasil-0.5.5.csv' using (100 * (column('packets_received') / column('packets_send'))):xtic(1) with histogram linetype rgb 'dark-yellow' title 'yggdrasil-0.5.5'; \
"

# combine graphs
convert	\( "${prefix}freifunk1_arrival_stats.png" "${prefix}freifunk1_traffic_stats.png" +append \) \
		+append "${prefix}freifunk1.png"
