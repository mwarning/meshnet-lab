# Benchmark2 Test

An extension of [benchmark1](../benchmark1) on more topologies (`rtree`, `grid4`, `grid8`). But this benchmark also aborts a test if the load average (from `uptime`) is too high. The load average is also logged. 

## Test

1. creat a square grid of nodes
2. wait 10 seconds
3. start babel/batman-adv/yggdrasil on each node
4. send pings between on random (<number of links>) pairs of node of at least two hops over 30 seconds
5. record arrived pings and shut down software and grid topology
6. continue at 1.

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot
