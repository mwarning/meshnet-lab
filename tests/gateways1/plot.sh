#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

for id in 'line' 'grid4' 'rtree'; do
	gnuplot -e "
		set title \"Traffic by routing protocol on $id dataset with 100MBit/s - 1ms latency links.\n1. Start daemons, 2. Wait 300s, 3. Measure for 300s with <node_count> random pings to a gateway\" noenhanced; \
		set grid; \
		set terminal pngcairo size 1280,960; \
		set output '${prefix}gateways1-$id.png'; \
		set key left top spacing 1 font 'sans, 12'; \
		set xlabel '# number of nodes'; \
		set ylabel 'tx per node [KB/s]'; \
		set y2label 'packet arrival [%]'; \
		set y2tics 0, 20; \
		set y2range [0:100]; \
		set ytics nomirror; \
		set termoption lw 3; \
		plot \
		'${prefix}gateways1-babel-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'dark-violet' title 'babel [KB/s/node]' axis x1y1, \
		'${prefix}gateways1-babel-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints dashtype 2 linewidth 1.5 linecolor rgb 'dark-violet' title 'babel [%]' axis x1y2, \
		\
		'${prefix}gateways1-batman-adv-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'skyblue' title 'batman-adv [KB/s/node]' axis x1y1, \
		'${prefix}gateways1-batman-adv-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints dashtype 2 linewidth 1.5 linecolor rgb 'skyblue' title 'batman-adv [%]' axis x1y2, \
		\
		'${prefix}gateways1-bmx6-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'dark-yellow' title 'bmx6 [KB/s/node]' axis x1y1, \
		'${prefix}gateways1-bmx6-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints dashtype 2 linewidth 1.5 linecolor rgb 'dark-yellow' title 'bmx6 [%]' axis x1y2, \
		\
		'${prefix}gateways1-bmx7-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'gold' title 'bmx7 [KB/s/node]' axis x1y1, \
		'${prefix}gateways1-bmx7-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints dashtype 2 linewidth 1.5 linecolor rgb 'gold' title 'bmx7 [%]' axis x1y2, \
		\
		'${prefix}gateways1-cjdns-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'dark-red' title 'cjdns [KB/s/node]' axis x1y1, \
		'${prefix}gateways1-cjdns-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints dashtype 2 linewidth 1.5 linecolor rgb 'dark-red' title 'cjdns [%]' axis x1y2, \
		\
		'${prefix}gateways1-olsr1-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'coral' title 'olsr1 [KB/s/node]' axis x1y1, \
		'${prefix}gateways1-olsr1-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints dashtype 2 linewidth 1.5 linecolor rgb 'coral' title 'olsr1 [%]' axis x1y2, \
		\
		'${prefix}gateways1-olsr2-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'green' title 'olsr2 [KB/s/node]' axis x1y1, \
		'${prefix}gateways1-olsr2-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints dashtype 2 linewidth 1.5 linecolor rgb 'green' title 'olsr2 [%]' axis x1y2, \
		\
		'${prefix}gateways1-yggdrasil-$id.csv' using (column('node_count')):(((column('tx_bytes') / 1000) / (column('traffic_ms') / 1000)) / column('node_count')) with linespoints linetype rgb 'purple' title 'yggdrasil [KB/s/node]' axis x1y1, \
		'${prefix}gateways1-yggdrasil-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with linespoints dashtype 2 linewidth 1.5 linecolor rgb 'purple' title 'yggdrasil [%]' axis x1y2, \
		;\
	"
done
