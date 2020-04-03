# Test Data

A collection of test data for simulation. So far without link quality data.

Line data creation:
```
#!/bin/sh

i=0
while [ $i -lt 1000 ]; do
	i=$((i + 50))
	./topology.py --formatted line $i > line-$(printf "%04d" $i).json
done
```

Lattice data creation:
```
#!/bin/sh

i=1
while [ $i -lt 32 ]; do
	i=$((i + 1))
	./topology.py --formatted lattice4 $i $i > lattice4-$(printf "%04d" $((i * i))).json
done
```

Random tree data creation:
```
#!/bin/sh

i=0
while [ $i -lt 1000 ]; do
	i=$((i + 50))
	./topology.py --formatted rtree $i $((i / 5)) > rtree-$(printf "%04d" $i).json
done
```

Freifunk data creation: See Freifunk [convert scripts](original_freifunk_data/).
