# Routing Protocols

This is a collection of start and stop scripts for several routing protocols. The start scripts are executed in very instance. The stop script kill all instances at once so far (TODO). Feel free to modifiy them and add new scripts.
Use `./software.py start <protocol>` to call `protocols/<protocol>_start.sh` on each virtual node (network namespace).

All of the following protocols are proactive protocols. They are also written in the C programming language - unless stated otherwise.

## B.A.T.M.A.N.-adv.

- [website](https://www.open-mesh.org/projects/open-mesh/wiki)
- distance vector
- rewrite/successor of batmand
- routes layer 2 packets (bat0 interface can be bridged)
- Linux kernel module

## Babel

- [website](https://www.irif.fr/~jch/software/babel/)
- distance vector
- Videos
  - [Babel Doesn't Care](https://www.youtube.com/watch?v=1zMDLVln3XM)
  - [Evolution of the Babel Routing Protocol](https://www.youtube.com/watch?v=Mflw4BuksHQ)

## BMX 6

- [website](https://github.com/bmx-routing/bmx6)
- distance vector
- fork of batmand

## BMX 7

- [Website](https://github.com/bmx-routing/bmx7)
- distance vector

## CJDNS

- [CJDNS](https://github.com/cjdelisle/cjdns)
- distance vector

## OLSR 1

- [website](https://github.com/OLSR/olsrd)
- distance vector

## OLSR 2

- [website](https://github.com/OLSR/OONF)
- distance vector
- rewrite of OLSR 1 as a framework

## Yggdrasil

- [website](https://yggdrasil-network.github.io/)
- [routing core](https://github.com/matrix-org/pinecone)
- distance vector
- spanning tree
- inspired by CJDNS
- written in Go
- Videos
  - [Growing Pinecones for P2P Matrix](https://fosdem.org/2022/schedule/event/matrix_p2p_pinecone/)
  - [Pinecones and Dendrites - P2P Matrix Progress](https://archive.fosdem.org/2021/schedule/event/matrix_pinecones/)
