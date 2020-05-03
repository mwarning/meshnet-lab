#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

gnuplot -e "
	set title \"Traffic for freifunk network topologies\";	\
	set grid; \
	set term png; \
	set terminal png size 1280,960; \
	set output '${prefix}traffic1-batman-adv-grid4.png'; \
	set key spacing 3 font 'Helvetica, 18'; \
	set style data histogram; \
	set style histogram cluster gap 1; \
	set style fill solid border -1; \
	set xlabel ''; \
	set ylabel 'tx per node [KB/s]'; \
	set termoption lw 3; \
	plot \
	'${prefix}traffic2-babel-freifunk.csv' using (column('tx_bytes') / 1000):xtic(1) with histogram linetype rgb 'dark-violet' title 'babel', \
	'${prefix}traffic2-babel-freifunk.csv' using 0:(1.2 * column('tx_bytes') / 1000):(sprintf('%d%%', (100 * column('packets_received') / column('packets_send')))) with labels linetype rgb 'dark-violet' notitle, \
	'${prefix}traffic2-batman-adv-freifunk.csv' using (column('tx_bytes') / 1000):xtic(1) with histogram linetype rgb 'skyblue' title 'batman-adv', \
	'${prefix}traffic2-bmx6-freifunk.csv' using (column('tx_bytes') / 1000):xtic(1) with histogram linetype rgb 'dark-yellow' title 'bmx6', \
	'${prefix}traffic2-bmx7-freifunk.csv' using (column('tx_bytes') / 1000):xtic(1) with histogram linetype rgb 'dark-green' title 'bmx7', \
	'${prefix}traffic2-cjdns-freifunk.csv' using (column('tx_bytes') / 1000):xtic(1) with histogram linetype rgb 'dark-red' title 'cjdns', \
	'${prefix}traffic2-olsr1-freifunk.csv' using (column('tx_bytes') / 1000):xtic(1) with histogram linetype rgb 'coral' title 'olsr1', \
	'${prefix}traffic2-olsr2-freifunk.csv' using (column('tx_bytes') / 1000):xtic(1) with histogram linetype rgb 'green' title 'olsr2', \
	'${prefix}traffic2-yggdrasil-freifunk.csv' using (column('tx_bytes') / 1000):xtic(1) with histogram linetype rgb 'purple' title 'yggdrasil'; \
"
