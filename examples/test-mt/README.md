# Test Setup - MultiTable

## Mininet with SDNIP or Mininext

### Mininet with SDNIP
```bash
$ cd ~/sdx-ryu/examples/test-mt/mininet/
$ sudo ./simple_sdx.py
```

### Mininext
```bash
$ cd ~/sdx-ryu/examples/test-mt/mininext(
$ sudo ./sdx_mininext.py
```

## Run xctrl

```bash
$ cd ~/sdx-ryu/xctrl/
$ ./xctrl.py ~/sdx-ryu/examples/test-mt/config/sdx_global.cfg
```

## Run RefMon

```bash
$ ryu-manager ~/sdx-ryu/flanc/refmon.py --refmon-config ~/sdx-ryu/examples/test-mt/config/sdx_global.cfg
```
