# Scalability Test 1

Test the scalability of different routing protocols on line, grid and random tree topologies.
Every topology is only set up once to minimize run time, since the test can run a long time as a whole.

The amount of pings between random node pair is always the number of nodes. For a good routing protocol, the traffic per node should stay almost constant.

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot
