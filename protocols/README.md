# Routing Protocols

This is a collection of start and stop scripts for several routing protocols. The start scripts are executed in very instance. The stop script kill all instances at once so far (TODO). Feel free to modifiy them and add new scripts.
Use `./software.py start <protocol>` to call `protocols/<protocol>_start.sh` on each virtual node (network namespace).

All of the following protocols are proactive protocols. They are also written in the C programming language - unless stated otherwise.

## B.A.T.M.A.N.-adv.

- [website](https://www.open-mesh.org/projects/open-mesh/wiki)
- distance vector
- successor of batmand
  - batmand is a layer 3, user space daemon
- routes layer 2 packets (bat0 interface can be bridged)
- Linux kernel module
- used by most Freifunk communities

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
- rewrite of BMX 6 with trusted nodes / authentication mechanism

## CJDNS

- [CJDNS](https://github.com/cjdelisle/cjdns)
- distance vector
- source routing
- used primarily as overlay over the Internet

## OLSRd

- [website](https://github.com/OLSR/olsrd)
- link state

## OLSR2

- [website](https://github.com/OLSR/OONF)
- link state
- rewrite of OLSR 1 as a framework

## Yggdrasil

- [website](https://yggdrasil-network.github.io/)
- research project, geared towards P2P Matrix, written in Go
- [Ironwood](https://github.com/Arceliar/ironwood) routing library for Yggdrasil 0.4.x
- [Pinecone](https://github.com/matrix-org/pinecone) is very similar to Ironwood, meant for P2P Matrix (some [documentation](https://github.com/matrix-org/pinecone/wiki))
- runs as overlay over Internet with manual peering
  - >5000 nodes
- general algorithm (0.3.x/0.4.x/0.5.x)
  - distance vector
  - spanning tree
  - end to end encryption (node identifiers are derive from crypto keys)
- Videos
  - [Growing Pinecones for P2P Matrix](https://fosdem.org/2022/schedule/event/matrix_p2p_pinecone/)
  - [Pinecones and Dendrites - P2P Matrix Progress](https://archive.fosdem.org/2021/schedule/event/matrix_pinecones/)
- each minor version so far is a different (incompatible) routing protocol
- the research network transitions to each new iteration of the protocol

### Yggdrasil 0.3.x

[Yggdrasil blog](https://yggdrasil-network.github.io/2018/12/12/announcing-v0-3.html)

- spanning tree
- switch to new DHT (Chord) from Kademlia

### Yggdrasil 0.4.x

[Yggdrasil blog](https://yggdrasil-network.github.io/2021/06/19/preparing-for-v0-4.html)

- spanning tree
- source routing
- uses new linear DHT design (SNEK)

### Yggdrasil 0.5.x

[Yggdrasil blog](https://yggdrasil-network.github.io/2023/10/22/upcoming-v05-release.html)

- spanning tree
- greedy routing (instead of source routing)
- leave nodes send bloom filters towards root

## Qaul

[Qaul](https://github.com/qaul)

- a meshenger that uses a gossip protocol
- provides core functionality as a daemon
- does not provide a network tunnel
- for ping tests, a wrapper needs to be used
