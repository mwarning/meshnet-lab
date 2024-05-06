# Mobility Test 1

Test nodes that move around randomly and form new connections.
Real live changes can be followed via the graph.json output.

## Test

0. for all combinations of <step_duration\> seconds in [10, 30] and <step_distance\> in [10, 30, 60] meters:
1. create 50 nodes on a 1km x 1km area
2. connect all nodes with increasing link length until 150 links are created
3. start Yggdrasil on each node
4. move nodes by \<step_distance\>m for each iteration
5. connect all nodes with increasing link length until 150 links are created
6. wait for \<step_duration\>s seconds
7. send 200 pings between random pairs of nodes over a period of 2 seconds
8. record arrived packets
9. continue at 4. for 30 times

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot

## Animate

* use `./animate.sh record` to record a series of screenshots of MeshGraphViewer
* use `./animate.sh process` to create a gif
