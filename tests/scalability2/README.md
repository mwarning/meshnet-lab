# Scalability Test 2

Test the scalability of different routing protocols on line, grid and random tree topologies by measuring traffic.
One ping is send from each node towards a sink node (with the lowest id). A ping is send every 200ms.

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot
