#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Traffic for freifunk network topologies\"; \
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}freifunk1_traffic_stats.png'; \
	set key spacing 3 font 'Helvetica, 18'; \
	set style data histogram; \
	set style histogram cluster gap 3; \
	set style fill solid border -1; \
	set ylabel 'tx per node [KB/s]'; \
	set termoption lw 3; \
	plot \
	'${prefix}freifunk1-babel.csv' using (((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')):xtic(1) with histogram linetype rgb 'dark-violet' title 'babel', \
	'${prefix}freifunk1-batman-adv.csv' using (((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')):xtic(1) with histogram linetype rgb 'skyblue' title 'batman-adv', \
	'${prefix}freifunk1-bmx6.csv' using (((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')):xtic(1) with histogram linetype rgb 'dark-yellow' title 'bmx6', \
	'${prefix}freifunk1-bmx7.csv' using (((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')):xtic(1) with histogram linetype rgb 'gold' title 'bmx7', \
	'${prefix}freifunk1-cjdns.csv' using (((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')):xtic(1) with histogram linetype rgb 'dark-red' title 'cjdns', \
	'${prefix}freifunk1-olsr1.csv' using (((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')):xtic(1) with histogram linetype rgb 'coral' title 'olsr1', \
	'${prefix}freifunk1-olsr2.csv' using (((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')):xtic(1) with histogram linetype rgb 'green' title 'olsr2', \
	'${prefix}freifunk1-ospf.csv' using (((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')):xtic(1) with histogram linetype rgb 'dark-green' title 'ospf', \
	'${prefix}freifunk1-yggdrasil.csv' using (((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')):xtic(1) with histogram linetype rgb 'purple' title 'yggdrasil'; \
"

gnuplot -e "
	set title \"Packet arrival for freifunk network topologies\"; \
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}freifunk1_arrival_stats.png'; \
	set key spacing 3 font 'Helvetica, 18'; \
	set style data histogram; \
	set style histogram cluster gap 3; \
	set style fill solid border -1; \
	set ylabel 'packet arrival [%]'; \
	set termoption lw 3; \
	plot \
	'${prefix}freifunk1-babel.csv' using (100 * (column('packets_received') / column('packets_send'))):xtic(1) with histogram linetype rgb 'dark-violet' title 'babel', \
	'${prefix}freifunk1-batman-adv.csv' using (100 * (column('packets_received') / column('packets_send'))):xtic(1) with histogram linetype rgb 'skyblue' title 'batman-adv', \
	'${prefix}freifunk1-bmx6.csv' using (100 * (column('packets_received') / column('packets_send'))):xtic(1) with histogram linetype rgb 'dark-yellow' title 'bmx6', \
	'${prefix}freifunk1-cjdns.csv' using (100 * (column('packets_received') / column('packets_send'))):xtic(1) with histogram linetype rgb 'dark-red' title 'cjdns', \
	'${prefix}freifunk1-olsr1.csv' using (100 * (column('packets_received') / column('packets_send'))):xtic(1) with histogram linetype rgb 'coral' title 'olsr1', \
	'${prefix}freifunk1-olsr2.csv' using (100 * (column('packets_received') / column('packets_send'))):xtic(1) with histogram linetype rgb 'green' title 'olsr2', \
	'${prefix}freifunk1-ospf.csv' using (100 * (column('packets_received') / column('packets_send'))):xtic(1) with histogram linetype rgb 'green' title 'ospf', \
	'${prefix}freifunk1-yggdrasil.csv' using (100 * (column('packets_received') / column('packets_send'))):xtic(1) with histogram linetype rgb 'purple' title 'yggdrasil'; \
"

# combine graphs
convert	\( "${prefix}freifunk1_traffic_stats.png" "${prefix}freifunk1_arrival_stats.png" -append \) \
		+append "${prefix}freifunk1.png"
