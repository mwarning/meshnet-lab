#!/bin/sh

for id in 'line' 'rtree' 'lattice4'; do
	gnuplot -e "
		set title \"Traffic by routing protocol on $id\n1. Start daemons, 2. Wait 300s, 3. Measure for 60s with 300 pings\";	\
		set grid;																			\
		set term png;																		\
		set terminal png size 1280,960;														\
		set output 'traffic-$id.png';														\
		set key spacing 1 font 'Helvetica, 12';												\
		set xlabel '# number of nodes';														\
		set ylabel 'ingress per node [KB/s]';												\
		set y2label 'packet arrival [%]';													\
		set y2tics 0, 10;																	\
		set ytics nomirror;																	\
		set termoption lw 3;																\
		plot																				\
		'traffic-batman-adv-$id.csv' using (column('node_count')):(column('rx_node_bs') / 1000) with linespoints title 'batman-adv [KB/s/node]' axis x1y1, \
		'traffic-batman-adv-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'batman-adv [%]' axis x1y2, \
		\
		'traffic-babel-$id.csv' using (column('node_count')):(column('rx_node_bs') / 1000) with linespoints title 'babel [KB/s/node]' axis x1y1, \
		'traffic-babel-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'babel [%]' axis x1y2, \
		\
		'traffic-yggdrasil-$id.csv' using (column('node_count')):(column('rx_node_bs') / 1000) with linespoints title 'yggdrasil [KB/s/node]' axis x1y1, \
		'traffic-yggdrasil-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'yggdrasil [%]' axis x1y2, \
		\
		'traffic-olsr2-$id.csv' using (column('node_count')):(column('rx_node_bs') / 1000) with linespoints title 'olsr2 [KB/s/node]' axis x1y1, \
		'traffic-olsr2-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'olsr2 [%]' axis x1y2, \
		\
		'traffic-bmx6-$id.csv' using (column('node_count')):(column('rx_node_bs') / 1000) with linespoints title 'bmx6 [KB/s/node]' axis x1y1, \
		'traffic-bmx6-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'bmx6 [%]' axis x1y2, \
		\
		'traffic-bmx7-$id.csv' using (column('node_count')):(column('rx_node_bs') / 1000) with linespoints title 'bmx7 [KB/s/node]' axis x1y1, \
		'traffic-bmx7-$id.csv' using (column('node_count')):(100 * column('packets_received') / column('packets_send')) with points title 'bmx7 [%]' axis x1y2,	\
		;\
	"
done
