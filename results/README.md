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

![image](convergence1-line_server.png)
(server, [csv data](convergence1-line_server.csv))

![image](convergence1-line_laptop.png)
(laptop, [csv data](convergence1-line_laptop.csv))

Lattice4:

![image](convergence1-lattice4_server.png)
(server, [csv data](convergence1-lattice4_server.csv))

![image](convergence1-lattice4_laptop.png)
(laptop, [csv data](convergence1-lattice4_laptop.csv))

RTree:

![image](convergence1-rtree_server.png)
(laptop, [csv data](convergence1-rtree_server.csv))

![image](convergence1-rtree_laptop.png)
(laptop, [csv data](convergence1-rtree_laptop.csv))

### Traffic1 Test

Line:

![image](traffic1-line_server.png)
(server, [csv data](traffic1-line_server.csv))

![image](traffic1-line_laptop.png)
(laptop, [csv data](traffic1-line_laptop.csv))

Lattice4:

![image](traffic1-lattice4_server.png)
(server, [csv data](traffic1-lattice4_server.csv))

![image](traffic1-lattice4_laptop.png)
(laptop, [csv data](traffic1-lattice4_laptop.csv))

RTree:

![image](traffic1-rtree_server.png)
(laptop, [csv data](traffic1-rtree_server.csv))

![image](traffic1-rtree_laptop.png)
(laptop, [csv data](traffic1-rtree_laptop.csv))


### Traffic2 Test

Only for batman-adv, but with error bars:

Laptop:

![image](traffic2-batman-adv-lattice4_laptop.png)
([csv data](traffic2-batman-adv-lattice4_laptop.csv))

Server:

![image](traffic2-batman-adv-lattice4_server.png)
([csv data](traffic2-batman-adv-lattice4_server.csv))
