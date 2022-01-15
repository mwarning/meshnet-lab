# Test Results

The results might not yet reflect real performance yet. Possible pitfalls:

* CPU usage can affect the results
* not all aspects are compared yet (e.g. mobility, packet loss)
* edge case topologies and traffic behavior (e.g. 0% packet loss)
* wrong configuration

Laptop for convergence1 and mobility1 tests:

* Void Linux (Linux 5.4.27_1 SMP PREEMPT x86_64)
* Intel i7-6500U (2 Cores, 2.50 GHz) with 8GB RAM
* From late 2015

Server for scalability1 test:

* Debian 10.3 (Linux Kernel 4.19.0-8-amd64)
* 2 x Intel Xeon X5687 (2 * 4 Cores, 3.86 GHz) with 32GB RAM
* From late 2011

Routing Software:

* yggdrasil (0.3.14)
* batman-adv/batctl (2020.0)
* babel (1.8.3-1)
* olsr1 (0.9.8), IPv4 tested!
* olsr2 (v0.15.1-96-g8397c64e)
* bmx6 (v1.0 / 12.05.2018 / d8869ec69797)
* bmx7 (v7.1.1 / 21.07.2019 / 91d6651ccb5a)
* cjdns (v20.5)

Note:
* I was not able to get bmx7 working in the test setup. As such, please ignore any bmx7 results for now!
* The test code might have been changed, use a matching meshnet-lab source code revision for result recreation.

## Topologies

An overview of the tested topologies can be found [here](../data/README.md).


## Benchmark1 Test

A test to figure out how many nodes the host system can emulate.

![image](laptop/benchmark1/1_benchmark1.png)
![image](server/benchmark1/1_benchmark1.png)

Notes:

- max. 120 nodes for the laptop
- max. 250 nodes for the server
- the host can probably support more nodes if the topology has less links

## Convergence1 Test

![image](laptop/convergence1/1_convergence1-line.png)
![image](laptop/convergence1/1_convergence1-rtree.png)
![image](laptop/convergence1/1_convergence1-grid4.png)

Notes:

- the line topology is the biggest challenge here
- the timing intervals are visible
- batman-adv can not reach 100% on a line, since the maximum hop count is 32
- cjdns struggles a bit, at about 30 seconds there seem to be a reconfiguration
- yggdrasil has the best start performance
- these three graphs take about 8 hours to generate

## Mobility1 Test

![image](laptop/mobility1/1_mobility1-10-10.png)
![image](laptop/mobility1/1_mobility1-10-30.png)
![image](laptop/mobility1/1_mobility1-10-60.png)

![image](laptop/mobility1/1_mobility1-30-10.png)
![image](laptop/mobility1/1_mobility1-30-30.png)
![image](laptop/mobility1/1_mobility1-30-60.png)

![image](laptop/mobility1/1_mobility1-10.gif) ![image](laptop/mobility1/1_mobility1-30.gif) ![image](laptop/mobility1/1_mobility1-60.gif)

Notes:

- Test setup:
  1. 50 nodes are distributed on a 1km x 1km square
  2. 150 nearest links are established
  3. after 10/30 seconds, 200 pings are send from a random source node to random destination node (over 2s)
  4. all nodes now move 0-10/30/60m in a random direction
  5. continue at step 2
- the higher a line, the better
- bmx7 is at the baseline, because in this test, it does no routing
- the data for each graph took 1 hour to generate

## Mobility 2 Test

![image](laptop/mobility2/1_mobility2.png)

- Test setup:
  1. 50 nodes are distributed on a 1km x 1km square
  2. for distances of 50m to 400m in steps of 50m do six times:
      1. move nodes in random directions of current distance
      2. 150 nearest links are established
      3. wait 10 seconds
      4. 200 pings are send from a random source node to random destination node (over 2s)
- the data took 1.5 hours to generate

## Scalability1 Test

![image](server/scalability1/1_scalability1-grid4.png)
![image](server/scalability1/1_scalability1-line.png)
![image](server/scalability1/1_scalability1-rtree.png)

Notes:

- under optimal routing strategies, the traffic per node should decline, since the number of pings are constant in this test but the number of nodes increases
- a low packet arrival rate makes the corresponding traffic result data meaningless (e.g. the complete line data :/)
- this test is low traffic by design and tries to measure overhead only
- a few edge cases seem to be revealed
- batman-adv has a maximum hop limit of 32
- the data for each graph took 18 hours to generate

## Connectivity1 Test

This is a pure numerical test related to the percolation theory. Nodes are distributed randomly in an area and given increasing range. The connectivity (% of possible connections) is measured.

![image](laptop/connectivity1/connectivity1.png)
![image](laptop/connectivity1/connectivity1_sd.png)

Notes:

- based on Gilbert's random disk model
- the connectivity rises exponentionally
- the standard deviation decreases very quickly near 100%
- further reading: [Insights From Percolation Theory](https://inthemesh.com/archive/from-mocha-to-mesh-insights-from-percolation-theory/)
- rough threshold radius approximation: 2 * sqrt(overall_area / (PI * node_count))
