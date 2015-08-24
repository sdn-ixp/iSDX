# arproxy - ARP Proxy

This controller is in charge of pushing all the flow rules to the SDX fabric that are necessary to get the SDX running.

## Run arproxy

```bash
$ git checkout xrs
$ cd ~/sdx-ryu/arproxy/
$ python arproxy.py
```

A sample config file (arproxy.cfg) is provided.
Note: This module requires root permission to sniff all incoming packets on the `eth0` interface.  
