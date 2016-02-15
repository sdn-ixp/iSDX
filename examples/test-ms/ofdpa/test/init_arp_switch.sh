#!/bin/bash

sudo ovs-vsctl del-br arp-switch 2> /dev/null
sudo ip link del arp-ifc type veth peer name arp-ifc-ovs 2> /dev/null

sudo ovs-vsctl add-br arp-switch
sudo ovs-vsctl set-fail-mode arp-switch secure
sudo ovs-vsctl set bridge arp-switch protocols=OpenFlow13
sudo ovs-vsctl set-controller arp-switch tcp:127.0.0.1:6633
sudo ovs-vsctl set bridge arp-switch other-config:datapath-id=0000000000000004

# connect switch to physical switch
sudo ovs-vsctl add-port arp-switch eth3
sudo ovs-ofctl -O OpenFlow13 mod-port arp-switch 1 up

# create a switch port
# (could just use 'arp-switch', but would rather not deal with negative port #)
sudo ip link add arp-ifc type veth peer name arp-ifc-ovs
sudo ifconfig arp-ifc 172.0.255.253
sudo ifconfig arp-ifc hw ether 08:00:27:89:33:ff
sudo ovs-vsctl add-port arp-switch arp-ifc-ovs
sudo ovs-ofctl -O OpenFlow13 mod-port arp-switch 2 up
