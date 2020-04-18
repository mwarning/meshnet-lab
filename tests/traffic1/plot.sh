#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

for id in 'line' 'rtree' 'grid4'; do
	gnuplot -e "
		set title \"Traffic by routing protocol on $id\n1. Start daemons, 2. Wait 300s, 3. Measure for 60s with 300 pings\";	\
		set grid;																			\
		set term png;																		\
		set terminal png size 1280,960;														\
		set output '${prefix}traffic1-$id.png';														\
		set key spacing 1 font 'Helvetica, 12';												\
		set xlabel '# number of nodes';														\
		set ylabel 'tx per node [KB/s]';													\
		set y2label 'packet arrival [%]';													\
		set y2tics 0, 10;																	\
		set ytics nomirror;																	\
		set termoption lw 3;																\
		plot																				\
		'${prefix}traffic1-batman-adv-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('duration_ms') / 1000)) / column('node_count')) with linespoints title 'batman-adv [KB/s/node]' axis x1y1, \
		'${prefix}traffic1-batman-adv-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'batman-adv [%]' axis x1y2, \
		\
		'${prefix}traffic1-babel-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('duration_ms') / 1000)) / column('node_count')) with linespoints title 'babel [KB/s/node]' axis x1y1, \
		'${prefix}traffic1-babel-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'babel [%]' axis x1y2, \
		\
		'${prefix}traffic1-yggdrasil-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('duration_ms') / 1000)) / column('node_count')) with linespoints title 'yggdrasil [KB/s/node]' axis x1y1, \
		'${prefix}traffic1-yggdrasil-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'yggdrasil [%]' axis x1y2, \
		\
		'${prefix}traffic1-olsr1-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('duration_ms') / 1000)) / column('node_count')) with linespoints title 'olsr1 [KB/s/node]' axis x1y1, \
		'${prefix}traffic1-olsr1-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'olsr1 [%]' axis x1y2, \
		\
		'${prefix}traffic1-olsr2-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('duration_ms') / 1000)) / column('node_count')) with linespoints title 'olsr2 [KB/s/node]' axis x1y1, \
		'${prefix}traffic1-olsr2-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'olsr2 [%]' axis x1y2, \
		\
		'${prefix}traffic1-bmx6-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('duration_ms') / 1000)) / column('node_count')) with linespoints title 'bmx6 [KB/s/node]' axis x1y1, \
		'${prefix}traffic1-bmx6-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'bmx6 [%]' axis x1y2, \
		\
		'${prefix}traffic1-bmx7-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('duration_ms') / 1000)) / column('node_count')) with linespoints title 'bmx7 [KB/s/node]' axis x1y1, \
		'${prefix}traffic1-bmx7-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'bmx7 [%]' axis x1y2,	\
		\
		'${prefix}traffic1-cjdns-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('duration_ms') / 1000)) / column('node_count')) with linespoints title 'cjdns [KB/s/node]' axis x1y1, \
		'${prefix}traffic1-cjdns-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'cjdns [%]' axis x1y2, \
		;\
	"
done
