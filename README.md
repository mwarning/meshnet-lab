# Mesh Network Lab

Create connected Linux network namespaces each with a single `uplink` interface.
A packet send on an interface will be received on all uplinks in all connected namespaces as defined in the JSON file.

This project is meant for testing Mobile Ad Hoc Mesh routing protocols. Supported are [babel](https://www.irif.fr/~jch/software/babel/), [batman-adv](https://www.open-mesh.org/projects/open-mesh/wiki), [olsr](https://www.olsr.org) and [yggdrasil](https://github.com/yggdrasil-network).

Topology and link quality changes are supported.

graph.json:
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
(The format is somewhat compatible with the [netjson](http://netjson.org/) format)

JSON keys:

- `source`, `target`: Mandatory. Name of the network namespace. Maximum of 6 characters long.
- `source_tc`, `target_tc`: Optional. Will be appended to `tc qdisc add dev <ifname> root ` command to influence traffic on outgoing traffic of a links interface. (TODO: verify that this actually works)


Useful commands:

- `./network.py list`: List all network namespaces.
- `./network.py cleanup`: Remove all network namespaces.
- `./network.py <from-state> <to-state>`: Change the network from `<from-state>` to `<to-state>` via JSON files. `none` can be used as an alias for an empty network.
- `ip netns exec "ns-a" batctl o`: Inspect the state of batman-adv in namespace `ns-a`.

## Usage

```
# Remove all namespaces (just in case)
sudo ./network.py cleanup

# Create a 10x10 lattice and write it to a file called graph.json
sudo ./topology.py lattice4 10 graph.json

# Setup the network structure of namespaces
sudo ./network.py none graph.json

# Start batman-adv in every namespace
sudo ./tests.py batman-adv start

# Test convergence by sending a few pings on random paths
sudo ./tests.py batman-adv test_convergence

# Stop batman-adv
sudo ./tests.py batman-adv stop

# Remove all namespaces
sudo ./network.py cleanup
```

## Internal Working

Every node is represented by its own network namespace and a bridge in namespace `switch`. The node namespace and bridge in `switch` are connected by a veth peer pair `uplink` and `dl-<node>`.  The nodes are connected by connecting the bridges with veth pairs in the `switch` namespace.

All interfaces in the bridges (except the `dl-<node>`) are set to `isolated`. This makes data flow only to and from the non-isolated `dl-<node>` interface, but not between them.

All bridges have `ageing_time` and `forward_delay` set to 0 to make them behave link a hub. A packet from the uplink will be send to all connections, but not between them.

## TODO

- Do not require the present state to be given.
- Better topology generator (more features).

## Related Projects

- [mlc](https://github.com/axn/mlc) (for bmx routing daemon, very complex)
- [network-lab](https://github.com/sudomesh/network-lab) (mesh networks with network namespace, very simple)
- [yggdrasil netns](https://github.com/yggdrasil-network/yggdrasil-go/blob/master/misc/run-schannel-netns) (for yggdrasil only, simple)
