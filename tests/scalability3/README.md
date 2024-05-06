# Scalability Test 3

Test the scalability of different routing protocols on line, grid and random tree topologies by measuring traffic.
One ping is send from a sink node (with the lowest id) towards each other node. A ping is send every 200ms.

## Test

1. for each topology of various sizes
2. start Yggdrasil on each node
3. wait 60 seconds
4. send a ping from a sink node towards each other nodes
    * \~200ms between each ping
5. record ping statistics and traffic
6. continue at 1.

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot
