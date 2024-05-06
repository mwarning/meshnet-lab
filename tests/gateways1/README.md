# Gateways Test 1

Assume that there is a small count of gateways/sinks in the network that many nodes want to use.

## Test

1. for each topology of different sizes:
2. create network
3. wait 10 seconds
4. start Yggdrasil on each node
5. wait 30 seconds
6. send a ping from each node to a designated sink/gateway node over a period of 5 minutes
7. record ping statistics and traffic
8. continue at 1.

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test.
* `./plot.sh` will create graphs using gnuplot
