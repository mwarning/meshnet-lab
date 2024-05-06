# Freifunk Test 1

Replicate topologies from the Freifunk data set with cable and WiFi connections.

## Test

1. for each Freifunk topology
2. create network
3. wait 10 seconds
4. start Yggdrasil on each node
5. wait 5 minutes
6. send ping over \<node count\> random & unique paths over a period 5 minutes
7. record ping statistics and traffic
8. continue at 1.

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot
