# Mobility Test 1

Test reaction of different routing protocols on 20 nodes that move around and form new connection.
Real live changes can be followed via the graph.json output.

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot

## Animate

* use `./animate record` to record a series of screenshots of MeshGraphViewer
* use `./animate process` to create a gif
