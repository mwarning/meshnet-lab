# 2024 Test Results

Test of different MANET routing protocols. The raw test data (CSV) is available here as well. [Revison](https://github.com/mwarning/meshnet-lab/commit/e52fbb62056f42ce4af63a851398f847553b1c80) was used for this test.

## Disclaimer

The results might not reflect real world performance. Possible pitfalls:

* CPU usage can affect the results
* not all aspects are compared yet (e.g. mobility, packet loss)
* edge case topologies and traffic behavior (e.g. 0% packet loss)
* configuration details

## Environment

Hardware

* Dedicated Server AR12-64 (https://ionos.de)
* 12 Core x 3.1 GHz (AMD Ryzen 9 Pro 3900)
* 64GB RAM
* 2 x 2000 GB Software RAID 1

Software

* Debian 11.7
* Linux B4475043 5.10.0-23-amd64 #1 SMP Debian 5.10.179-1 (2023-05-12) x86_64 GNU/Linux

Routing Software

* batman-adv (2023.2)
* Babel (1.13.1)
* BMX 6 (1.0)
* BMX 7 (7.1.1)
* OLSRd (0.9.8, 204a44adc7e98b826833b6fac2f7673735832427)
* OLSR2 (0.15.1, fb15d54d6a7a087cb0c5ec37c49804f6ce432396)
* CJDNS (20.6)
* Yggdrasil (0.5.2)

Notes

* Ignore test results that are outside the safe range of nodes/links counts!
* All Yggdrasil version were compiled using Go 1.22.1.
* RAM and storage were much more than needed.
* Links are configured to have 1ms latency and no packet loss.
* There is no packet interference as you would see with WiFi.

## Topologies

An overview of the tested topologies can be found [here](/data/README.md).

## Benchmark1 Test

A test to figure out how many nodes the host system can emulate without affecting the results too much.

![image](benchmark1/benchmark1.png)

1. creat a square grid of nodes
2. wait 10 seconds
3. start routing process on each node
4. send pings between on random (<number of links>) pairs of node of at least two hops over 30 seconds
5. record arrived pings and shut down software and grid topology
6. continue at 1.

Notes

- the data for the graph took ??? hours to generate

## Convergence1 Test

Test procedure

1. for each topology:
2. wait 10 seconds
3. start routing process on each node
4. wait 0-60 seconds (increase by 2 on each iteration)
5. send 200 pings between random pairs of nodes over a period of 2 seconds
6. record arrived pings and shut down software
7. continue at 3.

Notes

- the data for the graphs took ??? hours to generate

### Line Topology

![image](convergence1/convergence1-line.png)

### Tree Topology

![image](convergence1/convergence1-rtree.png)

### Grid Topology

![image](convergence1/convergence1-grid4.png)

## Mobility1 Test

![image](mobility1/mobility1-10-10.png)
![image](mobility1/mobility1-10-30.png)
![image](mobility1/mobility1-10-60.png)

![image](mobility1/mobility1-30-10.png)
![image](mobility1/mobility1-30-30.png)
![image](mobility1/mobility1-30-60.png)

Test procedure

0. for all combinations of <step_duration\> seconds in [10, 30] and <step_distance\> in [10, 30, 60] meters:
1. create 50 nodes on a 1km x 1km area
2. connect all nodes with increasing link length until 150 links are created
3. start routing process on each node
4. move nodes by \<step_distance\>m for each iteration
5. connect all nodes with increasing link length until 150 links are created
6. wait for \<step_duration\>s seconds
7. send 200 pings between random pairs of nodes over a period of 2 seconds
8. record arrived packets
9. continue at 4. for 30 times

Notes

- the data for the graphs took ??? hours to generate

## Mobility 2 Test

![image](mobility2/mobility2.png)

Test procedure

1. create 50 nodes on a 1km x 1km area
2. connect all nodes with increasing link length until 150 links are created
3. start routing process on each node and wait 30 seconds
4. for each \<step_distance\> in [50, 100, 150, 200, 250, 300, 350, 400] meters do 6 times:
5. move nodes by \<step_distance\> in a random direction
6. reconnect with increasing link length until 150 links are created
7. wait 15 seconds
8. send 200 pings between random pairs of nodes over a period of 2 seconds
9. record ping statistics and traffic
10. continue at 4.

Notes

- the data for the graph took ??? minutes to generate

## Gateways1 Test

Test procedure

1. for each topology of different sizes:
2. create network
3. wait 10 seconds
4. start routing process on each node
5. wait 30 seconds
6. send a ping from each node to a designated sink/gateway node over a period of 5 minutes 
7. record ping statistics and traffic
8. continue at 1.

Notes

- the data for the graphs took ??? hours to generate

### Line Topology

![image](gateways1/gateways1-line.png)

### Tree Topology

![image](gateways1/gateways1-rtree.png)

### Grid Topology

![image](gateways1/gateways1-grid4.png)

## Freifunk1 Test

[Freifunk](https://freifunk.net/) is a grassroots public and free mesh network community. The [topologies](/data/freifunk/README.md) are a mix of WiFi and Internet connections through servers. The topology has been extracted from the public map data.

![image](freifunk1/freifunk1.png)

Test procedure

1. for each Freifunk topology 
2. create network
3. wait 10 seconds
4. start routing process on each node
5. wait 5 minutes
6. send ping over \<node count\> random & unique paths over a period 5 minutes
7. record ping statistics and traffic
8. continue at 1.

Notes

- the data for the graph took ??? hours to generate

## Satellites1 Test

![image](satellites1/satellites1.png)

![image](/tests/satellites1/animation.gif)

Test procedure

1. create nodes for ground stations (Paris, Berlin, New York, Seoul, New Dehli, Rio de Janeiro)
2. create nodes for 3 orbits with 30 satellites each
3. select 20 random paths between ground stations
4. connect all nodes in reach (2000km)
    * ground stations connect to 2 satellites at most
    * satellites to at most 8 other satellites
5. move satellites and earth in 24 steps (2 hours of movement in reality)
6. send ping on each random path
7. record ping statistics and traffic
8. continue at 1.

Notes

- the data for the graph took ??? hours to generate

## Scalability1 Test

Test procedure

1. for each topology of various sizes
2. start routing process on each node
3. wait 60 seconds
4. send \<node_count\> pings between random and unique node pairs
    * over a duration of 5 minutes
    * at least two hops length
5. record ping statistics and traffic 
6. continue at 1.

Notes

- the data for the graphs took ??? hours to generate

### Line Topology

![image](scalability1/scalability1-line.png)

### Tree Toplogy

![image](scalability1/scalability1-rtree.png)

### Grid Topology

![image](scalability1/scalability1-grid4.png)

## Scalability2 Test

Test procedure

1. for each topology of various sizes
2. start routing process on each node
3. wait 60 seconds
4. send a ping from each node towards a sink node
    * \~200ms between each ping
5. record ping statistics and traffic 
6. continue at 1.

Notes

- the data for the graphs took ??? hours to generate

### Line Topology

![image](scalability2/scalability2-line.png)

### Tree Topology

![image](scalability2/scalability2-rtree.png)

### Grid Topology

![image](scalability2/scalability2-grid4.png)

## Scalability3 Test

Test procedure

1. for each topology of various sizes
2. start routing process on each node
3. wait 60 seconds
4. send a ping from a sink node towards each other nodes
    * \~200ms between each ping
5. record ping statistics and traffic 
6. continue at 1.

Notes

- the data for the graphs took ??? hours to generate

### Line Topology

![image](scalability3/scalability3-line.png)

### Tree Topology

![image](scalability3/scalability3-rtree.png)

### Grid Topology

![image](scalability3/scalability3-grid4.png)
