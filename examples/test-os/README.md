# Test Setup - One Switch One Table

## Running the setup
The test-os scenario has been wrapped in a launch.sh shell script.

### Log Server
```bash
$ cd ~
$ ./iSDX/launch.sh test-os 1
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
$ ./iSDX/launch.sh test-os 2
```

This performs the following tasks:

```bash
$ cd ~
$ sudo python iSDX/examples/test-os/mininet/simple_sdx.py
```

### Run everything else
```bash
$ cd ~
$ ./iSDX/launch.sh test-os 3
```

This will start the following parts:

#### RefMon (Fabric Manager)
```bash
$ cd ~/iSDX/flanc
$ ryu-manager refmon.py --refmon-config ~/iSDX/examples/test-os/config/sdx_global.cfg &
$ sleep 1
```

The RefMon module is based on Ryu. It listens for forwarding table modification instructions from the participant controllers and the IXP controller and installs the changes in the switch fabric. It abstracts the details of the underlying switch hardware and OpenFlow messages from the participants and the IXP controllers and also ensures isolation between the participants.

#### xctrl (IXP Controller)
```bash
$ cd ~/iSDX/xctrl
$ python xctrl.py ~/iSDX/examples/test-os/config/sdx_global.cfg
```

The IXP controller initializes the sdx fabric and installs all static default forwarding rules. It also handles ARP queries and replies in the fabric and ensures that these messages are forwarded to the respective participants’ controllers via ARP relay.

#### arpproxy (ARP Relay)
```bash
$ cd ~/iSDX/arproxy
$ sudo python arproxy.py test-os &
$ sleep 1
```

This module receives ARP requests from the IXP fabric and it relays them to the corresponding participant's controller. It also receives ARP replies from the participant controllers which it relays to the IXP fabric. 

#### xrs (BGP Relay)
```bash
$ cd ~/iSDX/xrs
$ sudo python route_server.py test-os &
$ sleep 1
```

The BGP relay is based on ExaBGP and is similar to a BGP route server in terms of establishing peering sessions with the border routers. Unlike a route server, it does not perform any route selection. Instead, it multiplexes all BGP routes to the participant controllers.

#### pctrl (Participant SDN Controller)
```bash
$ cd ~/iSDX/pctrl
$ sudo python participant_controller.py test-os 1 &
$ sudo python participant_controller.py test-os 2 &
$ sudo python participant_controller.py test-os 3 &
$ sleep 1
```

Each participant SDN controller computes a compressed set of forwarding table entries, which are installed into the inbound and outbound switches via the fabric manager, and continuously updates the entries in response to the changes in SDN policies and BGP updates. The participant controller receives BGP updates from the BGP relay. It processes the incoming BGP updates by selecting the best route and updating the RIBs. The participant controller also generates BGP announcements destined to the border routers of this participant, which are sent to the routers via the BGP relay.

#### ExaBGP
```bash
$ cd ~/iSDX
$ exabgp examples/test-os/config/bgp.conf
```

It is part of the `xrs` module itself and it handles the BGP sessions with all the border routers of the SDX participants.

## Testing the setup

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

## Cleanup
Run the `clean` script:
```bash
$ sh ~/iSDX/pctrl/clean.sh
```

### Note
Always check with ```route``` whether ```a1``` sees ```140.0.0.0/24``` and ```150.0.0.0/24```, ```b1```/```c1```/```c2``` see ```100.0.0.0/24``` and ```110.0.0.0/24```
