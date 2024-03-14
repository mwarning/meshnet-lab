#!/bin/sh

# to distinguish multiple runs (if needed)
prefix="$1"

for step_duration in 10 30; do
	for step_distance in 10 30 60; do
		gnuplot -e "
			set title \"Mobility1 test of 50 nodes. Start inside 1x1km square.\nStep duration is ${step_duration} seconds. Step width is 0-${step_distance}m. 100MBit/s - 1ms latency links.\" noenhanced; \
			set terminal pngcairo size 1280,960; \
			set output '${prefix}mobility1-${step_duration}-${step_distance}_arrival_progress.png'; \
			set grid back lc rgb '#808080' lt 0 lw 1; \
			set border 3 back lc rgb '#808080' lt 1; \
			set tics nomirror; \
			set key spacing 2 font 'sans, 18' center right; \
			set xlabel '${step_duration}s steps [-]'; \
			set ylabel 'packet arrival [%]'; \
			set yrange [0:100]; \
			set termoption lw 3; \
			plot \
			'${prefix}mobility1-${step_duration}-${step_distance}-yggdrasil-0.3.16.csv' using 0:(100 * (column('packets_received') / column('packets_send'))) with linespoints linetype rgb 'dark-red' title 'yggdrasil-0.3.16 [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-yggdrasil-0.4.7.csv' using 0:(100 * (column('packets_received') / column('packets_send'))) with linespoints linetype rgb 'coral' title 'yggdrasil-0.4.7 [%]' axis x1y1, \
			'${prefix}mobility1-${step_duration}-${step_distance}-yggdrasil-0.5.5.csv' using 0:(100 * (column('packets_received') / column('packets_send'))) with linespoints linetype rgb 'green' title 'yggdrasil-0.5.5 [%]' axis x1y1 \
			;\
		"

		# packet arrival stats
		gnuplot -e "
			set terminal pngcairo size 1280,480; \
			set output '${prefix}mobility1-${step_duration}-${step_distance}_arrival_stats.png'; \
			set grid back lc rgb '#808080' lt 0 lw 1; \
			set border 3 back lc rgb '#808080' lt 1; \
			set tics nomirror; \
			array protocols = ['yggdrasil-0.3.16', 'yggdrasil-0.4.7', 'yggdrasil-0.5.5']; \
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
