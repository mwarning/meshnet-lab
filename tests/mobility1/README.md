# Mobility Test 1

Test nodes that move around randomly and form new connections.
Real live changes can be followed via the graph.json output.

1. 50 nodes are distributed on a 1km x 1km square
2. 150 nearest links are established
3. after 10/30 seconds, 200 pings are send from a random source node to random destination node
4. all nodes now move 0-10/30/60m in a random direction
5. continue at step 2

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot

## Animate

* use `./animate.sh record` to record a series of screenshots of MeshGraphViewer
* use `./animate.sh process` to create a gif
