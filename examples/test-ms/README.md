# Test Setup - MultiSwitch

## Mininet with SDNIP or Mininext

### Mininet with SDNIP
```bash
$ cd ~/sdx-ryu/examples/test-ms/mininet/
$ sudo ./simple_sdx.py
```

### Mininext
```bash
$ cd ~/sdx-ryu/examples/test-ms/mininext(
$ sudo ./sdx_mininext.py
```

## Run xctrl

```bash
$ cd ~/sdx-ryu/xctrl/
$ ./xctrl.py ~/sdx-ryu/examples/test-ms/config/xctrl-gss.cfg
```

## Run RefMon

```bash
$ ryu-manager ~/sdx-ryu/flanc/refmon.py --refmon-config ~/sdx-ryu/examples/test-ms/config/refmon.cfg
```
