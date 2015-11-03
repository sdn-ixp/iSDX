
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


### Mininext
```bash
$ cd ~/iSDX/examples/test-ms/mininext
$ sudo ./sdx_mininext.py
```

### Run RefMon

```bash
$ ryu-manager ~/iSDX/flanc/refmon.py --refmon-config ~/iSDX/examples/test-ms/config/sdx_global.cfg
```

### Run xctrl

```bash
$ cd ~/iSDX/xctrl/
$ ./xctrl.py ~/iSDX/examples/test-ms/config/sdx_global.cfg
```

### Run arpproxy

```bash
$ cd ~/iSDX/arproxy/
$ sudo python arproxy.py test-ms
```

### Run xrs

```bash
$ cd ~/iSDX/xrs/
$ sudo python route_server.py test-ms
```

### Run pctrl

```bash
$ cd ~/iSDX/pctrl/
$ sh run_pctrlr.sh
```

### Run ExaBGP

```bash
exabgp ~/iSDX/examples/test-ms/config/bgp.conf
```

## Testing the setup

Check if the route server has correctly advertised the routes  

    mininext> a1 route -n  
    Kernel IP routing table  
    Destination     Gateway         Genmask         Flags Metric Ref    Use Iface  
    140.0.0.0       172.0.1.3       255.255.255.0   UG    0      0        0 a1-eth0  
    150.0.0.0       172.0.1.4       255.255.255.0   UG    0      0        0 a1-eth0  
    172.0.0.0       0.0.0.0         255.255.0.0     U     0      0        0 a1-eth0  

Testing the Policies

The participants have specified the following policies:  

_Participant A - outbound:_

    match(dstport=80) >> fwd(B) + match(dstport=4321/4322) >> fwd(C)

_Participant C - inbound:_

    match(dstport = 4321) >>  fwd(C1) + match(dstport=4322) >> fwd(C2)

Starting the  `iperf` servers:  

    mininext> b1 iperf -s -B 140.0.0.1 -p 80 &  
    mininext> c1 iperf -s -B 140.0.0.1 -p 4321 &  
    mininext> c2 iperf -s -B 140.0.0.1 -p 4322 &  

Starting the  `iperf` clients:  

    mininext> a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 80 -t 2  
    mininext> a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4321 -t 2  
    mininext> a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4322 -t 2  

Successful `iperf` connections should look like this:  

    mininext> c2 iperf -s -B 140.0.0.1 -p 4322 &  
    mininext> a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4322 -t 2  
    ------------------------------------------------------------  
    Client connecting to 140.0.0.1, TCP port 4322  
    Binding to local address 100.0.0.1  
    TCP window size: 85.3 KByte (default)  
    ------------------------------------------------------------  
    [  3] local 100.0.0.1 port 4322 connected with 140.0.0.1 port 4322  
    [ ID] Interval       Transfer     Bandwidth  
    [  3]  0.0- 2.0 sec  1.53 GBytes  6.59 Gbits/sec  

In case the `iperf` connection is not successful, you should see the message, `connect failed: Connection refused.`

## Cleanup
In the `pctrl` directory, run the `clean` script. 
```bash
$ cd ~/iSDX/pctrl/
$ sh clean.sh
```

### Note
Always check with ```route``` whether ```a1``` sees ```140.0.0.0/24``` and ```150.0.0.0/24```, ```b1```/```c1```/```c2``` see ```100.0.0.0/24``` and ```110.0.0.0/24```
