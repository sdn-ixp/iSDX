
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

### Test 1

Outbound policy of a1: match(tcp_port=80) >> fwd(b1)

```bash
mininext> b1 iperf -s -B 140.0.0.1 -p 80 &  
mininext> a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 80 -t 2
```

### Test 2

Outbound policy of a1: match(tcp_port=4321) >> fwd(c)
and Inbound policy of c: match(tcp_port=4321) >> fwd(c1)

```bash
mininext> c1 iperf -s -B 140.0.0.1 -p 4321 &
mininext> a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4321 -t 2  
```

### Test 3 

Outbound policy of a1: match(tcp_port=4322) >> fwd(c)
and Inbound policy of c: match(tcp_port=4322) >> fwd(c2)

```bash
mininext> c2 iperf -s -B 140.0.0.1 -p 4322 &  
mininext> a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4322 -t 2  
```

## Cleanup
In the `pctrl` directory, run the `clean` script. 
```bash
$ cd ~/iSDX/pctrl/
$ sh clean.sh
```

### Note

Always check with ```route``` whether ```a1``` sees ```140.0.0.0/24``` and ```150.0.0.0/24```, ```b1```/```c1```/```c2``` see ```100.0.0.0/24``` and ```110.0.0.0/24```
