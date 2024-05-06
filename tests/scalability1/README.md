# Scalability Test 1

Test the scalability of different routing protocols on line, grid and random tree topologies.
Every topology is only set up once to minimize run time, since the test can run a long time as a whole.

The amount of pings between random node pair is always the number of nodes. For a good routing protocol, the traffic per node should stay almost constant.

## Test

1. for each topology of various sizes
2. start Yggdrasil on each node
3. wait 60 seconds
4. send \<node_count\> pings between random and unique node pairs
    * over a duration of 5 minutes
    * at least two hops length
5. record ping statistics and traffic
6. continue at 1.

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot
