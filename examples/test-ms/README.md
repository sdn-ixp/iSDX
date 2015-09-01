# Test Setup - MultiSwitch

## Mininext
```bash
$ cd ~/sdx-ryu/examples/test-ms/mininext
$ sudo ./sdx_mininext.py
```

## Run RefMon

```bash
$ ryu-manager ~/sdx-ryu/flanc/refmon.py --refmon-config ~/sdx-ryu/examples/test-ms/config/sdx_global.cfg
```

## Run xctrl

```bash
$ cd ~/sdx-ryu/xctrl/
$ ./xctrl.py ~/sdx-ryu/examples/test-ms/config/sdx_global.cfg
```

## Run arpproxy

```bash
$ cd ~/sdx-ryu/arproxy/
$ sudo python arproxy.py test-ms
```

## Run xrs

```bash
$ cd ~/sdx-ryu/xrs/
$ sudo python route_server.py test-ms
```

## Run pctrl

```bash
$ cd ~/sdx-ryu/pctrl/
$ sh run_pctrlr.sh
```

## Run ExaBGP

```bash
exabgp ~/sdx-ryu/examples/test-ms/config/bgp.conf
```

## Run iperf to test the policies

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
$ cd ~/sdx-ryu/pctrl/
$ sh clean.sh
```

### Note

Always check with ```route``` whether ```a1``` sees ```140.0.0.0/24``` and ```150.0.0.0/24```, ```b1```/```c1```/```c2``` see ```100.0.0.0/24``` and ```110.0.0.0/24```

## Different Setup (not yet tested)

### Mininet with SDNIP

```bash
$ cd ~/sdx-ryu/examples/test-ms/mininet/
$ sudo ./simple_sdx.py
```
