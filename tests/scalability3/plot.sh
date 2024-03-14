#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

for id in 'line' 'grid4' 'grid8' 'rtree'; do
	gnuplot -e "
		set title \"Traffic by routing protocol on $id dataset with 100MBit/s - 1ms latency links.\n1. Start daemons, 2. Wait 300s, 3. Send one ping from a sink node towards each other node.\" noenhanced; \
		set terminal pngcairo size 1280,960; \
		set output '${prefix}scalability3-$id.png'; \
		set grid back lc rgb '#808080' lt 0 lw 1; \
		set border 3 back lc rgb '#808080' lt 1; \
		set key spacing 1 font 'sans, 12'; \
		set xlabel '# number of nodes'; \
		set ylabel 'tx per node [KB/s]'; \
		set y2label 'packet arrival [%]'; \
		set y2range [0:105];
		set key right top; \
		set y2tics 0, 10; \
		set ytics nomirror; \
		set termoption lw 3; \
		plot \
		'${prefix}scalability3-yggdrasil-0.3.16-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'dark-violet' title 'yggdrasil-0.3.16 [KB/s/node]' axis x1y1, \
		'${prefix}scalability3-yggdrasil-0.3.16-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints dashtype 2 linewidth 1.2 linecolor rgb 'dark-violet' title 'yggdrasil-0.3.16 [%]' axis x1y2, \
		\
		'${prefix}scalability3-yggdrasil-0.4.7-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'skyblue' title 'yggdrasil-0.4.7 [KB/s/node]' axis x1y1, \
		'${prefix}scalability3-yggdrasil-0.4.7-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints dashtype 2 linewidth 1.2 linecolor rgb 'skyblue' title 'yggdrasil-0.4.7 [%]' axis x1y2, \
		\
		'${prefix}scalability3-yggdrasil-0.5.5-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'dark-yellow' title 'yggdrasil-0.5.5 [KB/s/node]' axis x1y1, \
		'${prefix}scalability3-yggdrasil-0.5.5-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints dashtype 2 linewidth 1.2 linecolor rgb 'dark-yellow' title 'yggdrasil-0.5.5 [%]' axis x1y2, \
		;\
	"
done
