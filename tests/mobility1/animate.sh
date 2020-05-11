#!/bin/sh

set -e

if [ "$1" = 'record' ]; then
	sleep 3
	echo 'start'
	# all step durations should result in the same animation
	for step_duration in 10 30; do
		for step_distance in 10 30 60; do
			for file in graph-${step_duration}-${step_distance}-*.json; do
				[ -e "$file" ] || ( echo "File not found: $file"; exit 1; )
				echo "record $file"
				cp $file graph.json
				sleep 1
				# save screenshot
				import -window root $(basename "${file%.*}").png
			done
		done
	done
fi

if [ "$1" = 'process' ]; then
	offset_left_px=1160
	offset_top_px=290

	for step_duration in 10 30; do
		for step_distance in 10 30 60; do
			i=0
			for file in graph-${step_duration}-${step_distance}-*.png; do
				[ -e "$file" ] || ( echo "File not found: $file"; exit 1; )
				echo "process $file"

				i=$((i + 1))
				# crop (<width>x<height>+<left>+<top>)
				convert "$file" -crop "600x600+${offset_left_px}+${offset_top_px}" +repage "processed_${file}"
				# tag
				convert -pointsize 20 -fill black -draw "text 440,580 \"${step_distance}m steps / $(printf '%.03d' $i)\"\"" "processed_${file}" "processed_${file}"
			done
			echo "create mobility1-${step_distance}.gif"
			# make gif
			convert -dispose previous -delay 100 -loop 0 "processed_graph-${step_duration}-${step_distance}-*.png" "mobility1-${step_distance}.gif"
			# cleanup
			rm processed_graph-*.png
		done
	done
fi
