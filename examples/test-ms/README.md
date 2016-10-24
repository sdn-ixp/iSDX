
# Example: MultiSwitch

## Topology

![Experimental Setup]
(https://docs.google.com/drawings/d/1aO6wxbl6jv7nfOHl8kKbb7I3vJYeWRar4Yv_6uYGeSE/pub?w=808&h=579)

The setup consists of 3 participants (participating ASes) A, B and C. These participants have the following routers:

`Router A1, Router B1, Router C1, and Router C2`

These routers are running the zebra and bgpd daemons, part of the `Quagga` routing engine. We've used the `MiniNext` emulation tool to create this topology. In this example we have three switches representing SDX switch: (1) Main Switch, (2) Outbound Switch, and (3) Inbound Switch. 

## Configuring the Setup

The experiment needs two types of configurations: the control plane (SDX controller), and the data plane (Mininet topology). 

* **Control Plane Configurations**

The control plane configuration involves defining participant's policies, configuring `bgp.conf` for SDX's route server (based on ExaBGP), configuring 'sdx_global.cfg' to provide each participant's information to the SDX controller. 

In this example, participant `A` has outbound policies defined in `/examples/test-ms/policies/participant_1.py`. Participant `C` has inbound policies as defined in `/examples/test-ms/policies/participant_3.py`. Participant `B` has no policy.


* **Data Plane Configurations**

In our experimental setup, we need edge routers running a routing engine to exchange BGP paths. 
For our example, the MiniNext script is described in `/examples/test-ms/mininext/sdx_mininext.py`.

The SDX route server (which is based on ExaBGP) runs in the root namespace. We created an interface in the root namespace itself and connected it with the SDX switch. 

## Running the setup
The test-ms scenario has been wrapped in a launch.sh shell script.

### Log Server
```bash
$ cd ~
$ ./iSDX/launch.sh test-ms 1
```

This performs the following tasks:

```bash
$ cd ~/iSDX
$ sh pctrl/clean.sh
$ rm -f SDXLog.log
$ python logServer.py SDXLog.log
```

### Mininet
```bash
$ cd ~
$ ./iSDX/launch.sh test-ms 2
```

This performs the following tasks:

```bash
$ cd ~
$ sudo python iSDX/examples/test-mt/mininet/simple_sdx.py
```

### Run everything else
```bash
$ cd ~
$ ./iSDX/launch.sh [--stats] test-ms 3
```

This will start the following parts (and if `--stats` is specificed, it will also start the gauge.py Ryu app):

#### RefMon (Fabric Manager)
```bash
$ cd ~/iSDX/flanc
$ ryu-manager refmon.py --refmon-config ~/iSDX/examples/test-ms/config/sdx_global.cfg &
$ sleep 1
```

The RefMon module is based on Ryu. It listens for forwarding table modification instructions from the participant controllers and the IXP controller and installs the changes in the switch fabric. It abstracts the details of the underlying switch hardware and OpenFlow messages from the participants and the IXP controllers and also ensures isolation between the participants.

#### xctrl (IXP Controller)
```bash
$ cd ~/iSDX/xctrl
$ python xctrl.py ~/iSDX/examples/test-ms/config/sdx_global.cfg
```

The IXP controller initializes the sdx fabric and installs all static default forwarding rules. It also handles ARP queries and replies in the fabric and ensures that these messages are forwarded to the respective participants’ controllers via ARP relay.

#### arpproxy (ARP Relay)
```bash
$ cd ~/iSDX/arproxy
$ sudo python arproxy.py test-ms &
$ sleep 1
```

This module receives ARP requests from the IXP fabric and it relays them to the corresponding participant's controller. It also receives ARP replies from the participant controllers which it relays to the IXP fabric. 

#### xrs (BGP Relay)
```bash
$ cd ~/iSDX/xrs
$ sudo python route_server.py test-ms &
$ sleep 1
```

The BGP relay is based on ExaBGP and is similar to a BGP route server in terms of establishing peering sessions with the border routers. Unlike a route server, it does not perform any route selection. Instead, it multiplexes all BGP routes to the participant controllers.

#### pctrl (Participant SDN Controller)
```bash
$ cd ~/iSDX/pctrl
$ sudo python participant_controller.py test-ms 1 &
$ sudo python participant_controller.py test-ms 2 &
$ sudo python participant_controller.py test-ms 3 &
$ sleep 1
```

Each participant SDN controller computes a compressed set of forwarding table entries, which are installed into the inbound and outbound switches via the fabric manager, and continuously updates the entries in response to the changes in SDN policies and BGP updates. The participant controller receives BGP updates from the BGP relay. It processes the incoming BGP updates by selecting the best route and updating the RIBs. The participant controller also generates BGP announcements destined to the border routers of this participant, which are sent to the routers via the BGP relay.

#### ExaBGP
```bash
$ cd ~/iSDX
$ exabgp examples/test-ms/config/bgp.conf
```

It is part of the `xrs` module itself and it handles the BGP sessions with all the border routers of the SDX participants.

## Testing the setup

Check if the route server has correctly advertised the routes  

    mininext> a1 route -n  
    Kernel IP routing table  
    Destination     Gateway         Genmask         Flags Metric Ref    Use Iface  
    140.0.0.0       172.0.1.3       255.255.255.0   UG    0      0        0 a1-eth0  
    150.0.0.0       172.0.1.4       255.255.255.0   UG    0      0        0 a1-eth0  
    172.0.0.0       0.0.0.0         255.255.0.0     U     0      0        0 a1-eth0  

### Test 1

Outbound policy of a1: match(tcp_port=80) >> fwd(b1)

```bash
mininext> h1_b1 iperf -s -B 140.0.0.1 -p 80 &  
mininext> h1_a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 80 -t 2
```

### Test 2

Outbound policy of a1: match(tcp_port=4321) >> fwd(c)
and Inbound policy of c: match(tcp_port=4321) >> fwd(c1)

```bash
mininext> h1_c1 iperf -s -B 140.0.0.1 -p 4321 &
mininext> h1_a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4321 -t 2  
```

### Test 3 

Outbound policy of a1: match(tcp_port=4322) >> fwd(c)
and Inbound policy of c: match(tcp_port=4322) >> fwd(c2)

```bash
mininext> h1_c2 iperf -s -B 140.0.0.1 -p 4322 &  
mininext> h1_a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4322 -t 2  
```

Successful `iperf` connections should look like this:  

    mininext> h1_c2 iperf -s -B 140.0.0.1 -p 4322 &  
    mininext> h1_a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4322 -t 2  
    ------------------------------------------------------------  
    Client connecting to 140.0.0.1, TCP port 4322  
    Binding to local address 100.0.0.1  
    TCP window size: 85.3 KByte (default)  
    ------------------------------------------------------------  
    [  3] local 100.0.0.1 port 4322 connected with 140.0.0.1 port 4322  
    [ ID] Interval       Transfer     Bandwidth  
    [  3]  0.0- 2.0 sec  1.53 GBytes  6.59 Gbits/sec  

In case the `iperf` connection is not successful, you should see the message, `connect failed: Connection refused.`
Notice that here each iperf tests one of the participants' policies. The iperf has always the same destination ip, but reaches different hosts (b1, c1, c2) due to the more specific SDN policies.

## Cleanup
Run the `clean` script:
```bash
$ sh ~/iSDX/pctrl/clean.sh
```

### Note
Always check with ```route``` whether ```a1``` sees ```140.0.0.0/24``` and ```150.0.0.0/24```, ```b1```/```c1```/```c2``` see ```100.0.0.0/24``` and ```110.0.0.0/24```
