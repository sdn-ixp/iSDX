# Test Setup - MultiTable

## Running the setup


### Mininext
```bash
$ cd ~/iSDX/examples/test-mt/mininext
$ sudo ./sdx_mininext.py
```

### Run RefMon

```bash
$ ryu-manager ~/iSDX/flanc/refmon.py --refmon-config ~/iSDX/examples/test-mt/config/sdx_global.cfg
```

### Run xctrl

```bash
$ cd ~/iSDX/xctrl/
$ ./xctrl.py ~/iSDX/examples/test-mt/config/sdx_global.cfg
```

### Run arpproxy

```bash
$ cd ~/iSDX/arproxy/
$ sudo python arproxy.py test-mt
```

### Run xrs

```bash
$ cd ~/iSDX/xrs/
$ sudo python route_server.py test-mt
```

### Run pctrl

```bash
$ cd ~/iSDX/pctrl/
$ sh run_pctrlr.sh
```

### Run ExaBGP

```bash
exabgp ~/iSDX/examples/test-mt/config/bgp.conf
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
