# Test Data

A collection of test data for simulation. So far without link quality data.

Line data creation:
```
i=0
while [ $i -lt 100 ]; do
	i=$((i + 5))
	./topology.py "line" $i > line-$(printf "%03d" $i).json
done
```

Lattice data creation:
```
i=2
while [ $i -lt 41 ]; do
	./topology.py "lattice4" $i $i > lattice4-$(printf "%03d" $i).json
	i=$((i + 3))
done
```

Freifunk data creation: See Freifunk [convert scripts](original_freifunk_data/).
