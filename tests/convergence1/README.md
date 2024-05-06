# Convergence Test 1

Test the convergence of different routing protocols on three topologies (line, grid and a random tree) of 100 nodes each.

## Test

1. for each topology:
2. wait 10 seconds
3. start Yggdrasil on each node
4. wait 0-60 seconds (increase by 2 on each iteration)
5. send 200 pings between random pairs of nodes over a period of 2 seconds
6. record arrived pings and shut down software
7. continue at 3.

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot
