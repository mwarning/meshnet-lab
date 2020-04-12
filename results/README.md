# Test Results

## Environments

Server:

* Debian 10.3 (Linux Kernel 4.19.0-8-amd64)
* 2 x Intel Xeon X5687 (2 * 4 Cores, 3.86 GHz) with 32GB RAM.

Laptop:

* Void Linux (Linux 5.4.27_1 SMP PREEMPT x86_64)
* Intel i7-6500U (2 Cores, 2.50 GHz) with 8GB RAM.

Routing Software:

* yggdrasil (0.3.14)
* batman-adv/batctl (2020.0)
* babel (1.8.3-1)
* olsr2 (v0.15.1-96-g8397c64e)
* bmx6 (v1.0 / 12.05.2018 / d8869ec69797)
* bmx7 (v7.1.1 / 21.07.2019 / 91d6651ccb5a)
* cjdns (v20.5)

## Results

### Convergence1 Test

Line:

![image](server_convergence1-line.png)

![image](laptop_convergence1-line.png)

Lattice4:

![image](server_convergence1-lattice4.png)

![image](laptop_convergence1-lattice4.png)

RTree:

![image](server_convergence1-rtree.png)

![image](laptop_convergence1-rtree.png)

### Traffic1 Test

Line:

![image](traffic1-line_server.png)

![image](traffic1-line_laptop.png)

Lattice4:

![image](traffic1-lattice4_server.png)

![image](laptop_traffic1-lattice4.png)
(laptop; [babel](laptop_traffic1-babel-lattice4.csv), [bmx6](laptop_traffic1-bmx6-lattice4.csv), [cjdns](laptop_traffic1-cjdns-lattice4.csv), [olsr2](laptop_traffic1-olsr2-lattice4.csv), [batman-adv](laptop_traffic1-batman-adv-lattice4.csv), [bmx7](laptop_traffic1-bmx7-lattice4.csv), [yggdrasil](laptop_traffic1-yggdrasil-lattice4.csv))

Note that the packet arrival rates are usually pretty bad. This cause has still to be determined.

RTree:

![image](traffic1-rtree_server.png)

![image](traffic1-rtree_laptop.png)

### Traffic2 Test

Only for batman-adv, but with error bars:

Laptop:

![image](laptop_traffic2-batman-adv-lattice4.png)
([batman-adv](laptop_traffic2-batman-adv-lattice4.csv))

The dropping packet arrival rate after 100 nodes might indicate that the system has come to its limits.

Server:

![image](server_traffic2-batman-adv-lattice4.png)
