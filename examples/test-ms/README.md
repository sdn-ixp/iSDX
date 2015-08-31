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
$ sudo python participant_controller.py test-ms 1
$ sudo python participant_controller.py test-ms 2
$ sudo python participant_controller.py test-ms 3
```

## Run ExaBGP
exabgp ~/sdx-ryu/examples/test-ms/config/bgp.conf

### Mininet with SDNIP

```bash
$ cd ~/sdx-ryu/examples/test-ms/mininet/
$ sudo ./simple_sdx.py
```
