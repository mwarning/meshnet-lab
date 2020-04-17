# Mesh Network Lab

Emulate a mesh network of hundreds of nodes on a computer. The network is realized using Linux network namespaces that are connected via virtual Ethernet interfaces. The network is defined in a JSON file.

Each namespace can run its own routing progam and sees a single `uplink` interface. A packet send on that interface will be received on the uplinks of all connected namespaces.

This project is meant for testing Mobile Ad Hoc Mesh routing protocols. Supported are [Babel](https://www.irif.fr/~jch/software/babel/), [B.A.T.M.A.N.-adv](https://www.open-mesh.org/projects/open-mesh/wiki), [OLSR1](https://github.com/OLSR/olsrd), [OLSR2](https://github.com/OLSR/OONF), [BMX6](https://github.com/bmx-routing/bmx6), [BMX7](https://github.com/bmx-routing/bmx7), [Yggdrasil](https://github.com/yggdrasil-network) and [CJDNS](https://github.com/cjdelisle/cjdns). Preliminary [test results](results/) are available.

Example JSON file:
```
{
  "links": [
    {
      "source": "a",
      "target": "b",
      "source_tc": "netem delay 10ms 20ms distribution normal",
      "target_tc": "netem loss 0.1"
    },
    {
      "source": "b",
      "target": "c",
      "source_tc": "tbf rate 100mbit burst 8192 latency 1ms",
      "target_tc": "tbf rate 100mbit burst 8192 latency 1ms"
    }
  ]
}
```

JSON keys:

- `source`, `target`: Mandatory. Name of the network namespace. Maximum of 6 characters long.
- `source_tc`, `target_tc`: Optional. It will be appended to the `tc qdisc add dev <veth-interface> root` command and affects outgoing traffic on interface pairs connecting the bridges. (TODO: verify that this actually works)

## Usage

Most commands need root. So we assume all commands are execute as root:

```
# Create a 10x10 grid and write it to a file called graph.json
./topology.py grid4 10 10 > graph.json

# Create Network
./network.py change none graph.json

# Start Software
./tests.py start batman-adv

# Run Tests
./tests.py batman-adv

# Stop Software
./tests.py stop batman-adv

# Remove Network
./network.py change graph.json none
```

As an alternative, you can stop all protocols using `./software.py clear` and remove all namespaces using `./network.py clear`.

## Internal Working

Every node is represented by its own network namespace (`ns-*`) and a namespace called `switch` that contains all the cabling. The node namespace and bridge in `switch` are connected by a veth peer pair `uplink` and `dl-<node>`.

All interfaces in the bridges (except the `dl-<node>`) are set to `isolated`. This makes data flow only to and from the non-isolated `dl-<node>` interface, but not between them.

All bridges have `ageing_time` and `forward_delay` set to 0 to make them behave link a hub. A packet from the uplink will be send to all connections, but not between them.

![Visual Example](misc/network_mapping.png)

- Applications can be started in ns1, ns2, ns3 and see only their interface called `uplink`
- bridges have properties `stp_state`, `ageing_time` and `forward_delay` set to 0
- ve-* interfaces have property `isolated` set to `on`

## Routing Protocol Notes

- BATMAN-adv:
  - needs batctl installed for tests
  - the current metric limits the maximum hop count to 32 ([source](https://lists.open-mesh.org/pipermail/b.a.t.m.a.n/2020-April/019212.html))
  - `kworker/u32:1+bat_events` becomes quickly a single threaded bottleneck
    - change `create_singlethread_workqueue()` to `create_workqueue()` in `net/batman-adv/main.c` ([source](https://lists.open-mesh.org/pipermail/b.a.t.m.a.n/2020-April/019214.html))
  - OGM paket TTL is 50 ([source](https://git.open-mesh.org/batman-adv.git/blob/refs/heads/master:/net/batman-adv/main.h#l26))
  - tested with batman-adv 2019.4
- OLSR2 complains when the Linux kernel is not compiled with CONFIG_IPV6_MULTIPLE_TABLES enabled
  - but it still seems to work without
  - tested with olsr2 0.15.1
- OLSR1 has buggy/broken IPv6 support, we use IPv4 instead
  - tested with olsr1 0.9.8
- Babel has a maximum metric of 2^16 - 1, a single wired hop has a default metric of 96, a wireless hop with no packet loss has a metric of 256. That allows a maximum hop count of around 683 hops. ([source](https://alioth-lists.debian.net/pipermail/babel-users/2020-April/003688.html))
  - `default rxcost 16` in the configuration file should help
- Yggdrasil needs the most resources (CPU/RAM) of the routing protocol programs supported here
  - encrypts traffic
- CJDNS security can be disabled. Compile for speed using `NSA_APPROVED=true Seccomp_NO=1 NO_TEST=1 NO_NEON=1 CFLAGS="-O0" ./do`.

## Related Projects

- [MeshGraphViewer](https://github.com/mwarning/MeshGraphViewer) can show the topology JSON files in a browser using d3.js.
- [mininet](http://mininet.org/) (uses VirtualBox images and OpenFlow, every link ends in an interface, otherwise very similar)
- [mlc](https://github.com/axn/mlc) (uses LXC Containers, supports BMX7 and Babel, very complex)
- [network-lab](https://github.com/sudomesh/network-lab) (mesh networks with network namespace, simple)
- [yggdrasil netns](https://github.com/yggdrasil-network/yggdrasil-go/blob/master/misc/run-schannel-netns) (for yggdrasil only, very simple)
- [Running Babel/OLSR/BMX7 inside kubernetes](https://media.freifunk.net/v/multipathtcp-with-un-meshed-networks-and-running-babel-olsr-bmx7-inside-kubernetes-and-containers)
- Freifunk Berlin [firmware test](https://github.com/freifunk-berlin/firmware/wiki/Local-testing) (uses docker containers)
