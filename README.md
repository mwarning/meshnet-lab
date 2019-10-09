# Mesh Network Builder

Create a mesh network defined in a JSON file. Uses Linux network namespaces and bridges on linux.
The mesh routing program ([batman-adv](https://www.open-mesh.org/projects/open-mesh/wiki), [yggdrasil](https://github.com/yggdrasil-network) or [babel](https://www.irif.fr/~jch/software/babel/)) will see only network interface `uplink` to receive and send packets.
Packets send will be received on all connected instances via their own `uplink` interface.

Tools needed: pyhon, ip, bridge

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
(from `data.json`)

Run `sudo mesh-network.py batman-adv data.json` to create a mesh network with batman-adv running.

JSON keys:
- `source`, `target`: Mandatory. Name for the nodes on each side of a link.
- `source_tc`, `target_tc`: Optional. Will be appended to `tc qdisc add dev <ifname> root ` command to influence traffic on outgoing traffic of a links interface. (TODO: verify that this actually works)

Useful commands:

- List all namespaces: `ip netns list`
- Remove all namespaces: `ip -all netns delete`
- Inspect batman-adv state: `ip netns exec "ns-a" batctl o`

## Internal Working

This is what the script does:

1. Create a network namespace `switch` for all the virtual links between nodes.
    1. disable IPv6 since no IPv6 network logic is needed here
2. For every node (`<name>`)
    1. create a network namespace (`ns-<name>`)
    2. create a bridge in namepace `switch` (`br-<name>`) with arp and multicast disabled
    3. create a pair of connected interfaces (`downlink-<name>` and `<uplink>`) in namespace `switch`
        1. put `downlink-<name>` into bridge `br-<name>`
        2. move `<uplink>` into the namespace of the node
3. For every link
    1. create a pair of connected interfaces (`<veth-<from>-<to>` and `<veth-<to>-<from>`) in namespace `switch`
    2. put each interface into the bridge of the nodes bridge
    3. enable isolation on both interfaces so they speak only to the `downlink-<name>` interface of the bridge

## TODO

Create a topology generator and tests.

## Related Projects

- [mlc](https://github.com/axn/mlc) (for bmx routing daemon, very complex)
- [network-lab](https://github.com/sudomesh/network-lab) (mesh networks with network namespace, very simple)
- [yggdrasil netns](https://github.com/yggdrasil-network/yggdrasil-go/blob/master/misc/run-schannel-netns) (for yggdrasil only, simple)
