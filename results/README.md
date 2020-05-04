# Test Results

The results might not yet reflect real performance yet. Possible pitfalls:

* CPU usage can affect the results
* not all aspects are compared yet (e.g. mobility, packet loss)
* edge case topologies and traffic behavior (e.g. 0% packet loss)
* wrong configuration

Laptop for convergence1 and mobility1 tests:

* Void Linux (Linux 5.4.27_1 SMP PREEMPT x86_64)
* Intel i7-6500U (2 Cores, 2.50 GHz) with 8GB RAM

Server for scalability1 test:

* Debian 10.3 (Linux Kernel 4.19.0-8-amd64)
* 2 x Intel Xeon X5687 (2 * 4 Cores, 3.86 GHz) with 32GB RAM

Routing Software:

* yggdrasil (0.3.14)
* batman-adv/batctl (2020.0)
* babel (1.8.3-1)
* olsr1 (0.9.8), IPv4 tested!
* olsr2 (v0.15.1-96-g8397c64e)
* bmx6 (v1.0 / 12.05.2018 / d8869ec69797)
* bmx7 (v7.1.1 / 21.07.2019 / 91d6651ccb5a)
* cjdns (v20.5)
* `none` only works for one hop destinations. It serves as baseline.

## Topologies

An overview of the tested topologies can be found [here](../data/README.md).

## Convergence1 Test

![image](laptop/convergence1/1_convergence1-line.png)
![image](laptop/convergence1/1_convergence1-rtree.png)
![image](laptop/convergence1/1_convergence1-grid4.png)

Notes:

- the line topology is the biggest challenge here
- the timing intervals are visible
- batman-adv can not reach 100% on a line, since the maximum hop count is 32
- cjdns struggles a bit, at about 30 seconds there seem to be a reconfiguration
- yggdrasil has the best start performance, but a more irratic routing behaviour on a line topology
- bmx7 does not route any packets except if it goes to a direct neighbor, the reasons are unknown
- these three graphs take about 8 hours to generate

## Mobility1 Test

![image](laptop/mobility1/1_mobility1-10-0.01.png)
![image](laptop/mobility1/1_mobility1-10-0.03.png)
![image](laptop/mobility1/1_mobility1-10-0.06.png)

![image](laptop/mobility1/1_mobility1-30-0.01.png)
![image](laptop/mobility1/1_mobility1-30-0.03.png)
![image](laptop/mobility1/1_mobility1-30-0.06.png)

Notes:

- some pings cannot reach the destination, so 100% is only based on the actual possible limit
- the higher a line, the better
- bmx7 is at the baseline, because in this test it does not do routing
- yggdrasil uses a dedicated tun0 interface, as such, in can perform below the one hop baseline

## Scalability1 Test

![image](server/scalability1/1_scalability1-grid4.png)
![image](server/scalability1/1_scalability1-line.png)
![image](server/scalability1/1_scalability1-rtree.png)

Notes:

- a low packet arrival rate makes the corresponding traffic result data meaningless (e.g. the complete line data :/)
- some routing protocols cause a huge amount of traffic on certain topologies with no latency:
  - yggdrasil on a line
  - batman-adv on rtree and grid4
- batman-adv has a low hop limit
- grid4 and line topologies (even more so with no traffic/latency limitations) are pathological
- these three graphs took 55 hours to generate
