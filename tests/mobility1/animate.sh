#!/bin/sh

set -e

if [ "$1" = 'record' ]; then
	sleep 3
	echo 'start'
	# all step durations should result in the same animation
	for step_duration in 10 30; do
		for step_distance in 0.01 0.03 0.06; do
			for file in graph-${step_duration}-${step_distance}-*.json; do
				echo $file
				cp $file graph.json
				sleep 1
				# save screenshot
				import -window root $(basename "${file%.*}").png
			done
		done
	done
fi

offset_left=1120
offset_top=300
if [ "$1" = 'process' ]; then
	for step_duration in 10 30; do
		for step_distance in 0.01 0.03 0.06; do
			i=0
			for file in graph-${step_duration}-${step_distance}-*.png; do
				[ -e "$file" ] || ( echo "No files found: $file"; exit 1; )
				echo "process $file"

				i=$((i + 1))
				# crop (<width>x<height>+<left>+<top>)
				convert "$file" -crop "550x550+${offset_left}+${offset_top}" +repage "processed_${file}"
				# tag
				convert -pointsize 20 -fill black -draw "text 385,530 \"$step_distance steps / $(printf '%.03d' $i)\"\"" "processed_${file}" "processed_${file}"
			done
			echo "create mobility1-${step_distance}.gif"
			# make gif
			convert -dispose previous -delay 100 -loop 0 processed_graph-${step_duration}-${step_distance}-*.png "mobility1-${step_distance}.gif"
			# cleanup
			rm processed_graph-${step_duration}-${step_distance}-*.png
		done
	done
fi
