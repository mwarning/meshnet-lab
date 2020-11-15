#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

for step_duration in 10 30; do
	for step_distance in 10 30 60; do
		gnuplot -e "
			set title \"Mobility1 test of 50 nodes. Start inside 1x1km square.\nStep duration is ${step_duration} seconds. Step width is 0-${step_distance}m. 100MBit/s - 1ms latency links.\" noenhanced; \
			set grid; \
			set term png; \
			set terminal png size 1280,960; \
			set output '${prefix}mobility1-${step_duration}-${step_distance}_arrival_progress.png'; \
			set key spacing 2 font 'Helvetica, 18' center right; \
			set xlabel '${step_duration}s steps [-]'; \
			set ylabel 'packet arrival [%]'; \
			set yrange [0:100]; \
			set termoption lw 3; \
			plot \
			'${prefix}mobility1-${step_duration}-${step_distance}-babel.csv' using 0:(100 * (column('packets_received') / column('packets_send'))) with linespoints linetype rgb 'dark-violet' title 'babel [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-batman-adv.csv' using 0:(100 * (column('packets_received') / column('packets_send'))) with linespoints linetype rgb 'skyblue' title 'batman-adv [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-bmx6.csv' using 0:(100 * (column('packets_received') / column('packets_send'))) with linespoints linetype rgb 'dark-yellow' title 'bmx6 [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-bmx7.csv' using 0:(100 * (column('packets_received') / column('packets_send'))) with linespoints linetype rgb 'gold' title 'bmx7 [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-cjdns.csv' using 0:(100 * (column('packets_received') / column('packets_send'))) with linespoints linetype rgb 'dark-red' title 'cjdns [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-olsr1.csv' using 0:(100 * (column('packets_received') / column('packets_send'))) with linespoints linetype rgb 'coral' title 'olsr1 [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-olsr2.csv' using 0:(100 * (column('packets_received') / column('packets_send'))) with linespoints linetype rgb 'green' title 'olsr2 [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-ospf.csv' using 0:(100 * (column('packets_received') / column('packets_send'))) with linespoints linetype rgb 'dark-green' title 'ospf [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-yggdrasil.csv' using 0:(100 * (column('packets_received') / column('packets_send'))) with linespoints linetype rgb 'purple' title 'yggdrasil [%]' axis x1y1 \
			;\
		"

		# packet arrival stats
		gnuplot -e "
			set grid; \
			set term png; \
			set terminal png size 1280,480; \
			set output '${prefix}mobility1-${step_duration}-${step_distance}_arrival_stats.png'; \
			array protocols = ['babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'ospf', 'yggdrasil']; \
			array SUM[|protocols|]; \
			do for [i=1:|protocols|] { \
				file = '${prefix}mobility1-${step_duration}-${step_distance}-'.protocols[i].'.csv'; \
				stats file using (column('packets_send')) nooutput; \
				packets_send_sum = STATS_sum; \
				stats file using (column('packets_received')) nooutput; \
				packets_received_sum = STATS_sum; \
				SUM[i] = 100 * (packets_received_sum / packets_send_sum); \
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

		# combine graphs
		convert	"${prefix}mobility1-${step_duration}-${step_distance}_arrival_progress.png" "${prefix}mobility1-${step_duration}-${step_distance}_arrival_stats.png" \
				-append "${prefix}mobility1-${step_duration}-${step_distance}.png"
	done
done
