#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

for step_duration in 10 30; do
	for step_distance in 0.01 0.03 0.06; do
		gnuplot -e "
			set title \"Mobility1 test of 50 nodes. Start inside 1x1 square.\nStep duration is ${step_duration} seconds. Step width is 0-${step_distance}. LAN cable connections. 200 pings were send.\" noenhanced; \
			set grid; \
			set term png; \
			set terminal png size 1280,960; \
			set output '${prefix}mobility1-${step_duration}-${step_distance}.png'; \
			set key spacing 2 font 'Helvetica, 18' center right; \
			set xlabel 'time [sec]'; \
			set ylabel 'packet arrival [%]'; \
			set yrange [-2:102]; \
			set termoption lw 3; \
			plot \
			'${prefix}mobility1-${step_duration}-${step_distance}-babel.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('valid_path_count'))) with linespoints linetype rgb 'dark-violet' title 'babel [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-batman-adv.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('valid_path_count'))) with linespoints linetype rgb 'skyblue' title 'batman-adv [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-bmx6.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('valid_path_count'))) with linespoints linetype rgb 'dark-yellow' title 'bmx6 [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-bmx7.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('valid_path_count'))) with linespoints linetype rgb 'dark-green' title 'bmx7 [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-cjdns.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('valid_path_count'))) with linespoints linetype rgb 'dark-red' title 'cjdns [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-none.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('valid_path_count'))) with linespoints linetype rgb 'black' title 'none [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-olsr1.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('valid_path_count'))) with linespoints linetype rgb 'coral' title 'olsr1 [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-olsr2.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('valid_path_count'))) with linespoints linetype rgb 'green' title 'olsr2 [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-yggdrasil.csv' using (column('time_ms') / 1000):(100 * (column('packets_received') / column('valid_path_count'))) with linespoints linetype rgb 'purple' title 'yggdrasil [%]' axis x1y1 \
			;\
		"
	done
done
