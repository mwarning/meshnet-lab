# Mobility Test 2

Test nodes move around randomly and form new connections.

## Test

1. create 50 nodes on a 1km x 1km area
2. connect all nodes with increasing link length until 150 links are created
3. start Yggdrasil on each node and wait 30 seconds
4. for each \<step_distance\> in [50, 100, 150, 200, 250, 300, 350, 400] meters do 6 times:
5. move nodes by \<step_distance\> in a random direction
6. reconnect with increasing link length until 150 links are created
7. wait 15 seconds
8. send 200 pings between random pairs of nodes over a period of 2 seconds
9. record ping statistics and traffic
10. continue at 4.

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot
