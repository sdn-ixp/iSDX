# arproxy - ARP Proxy

This controller is in charge of pushing all the flow rules to the SDX fabric that are necessary to get the SDX running.

## Run arproxy

```bash
$ git checkout xrs
$ cd ~/iSDX/arproxy/
$ sudo python arproxy.py <example-name> (e.g sudo python arproxy.py simple)
```

Note: This module requires root permission to sniff all incoming packets on the `eth0` interface.  
