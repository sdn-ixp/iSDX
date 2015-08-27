# pctrl - Participants' SDX Controller

This module is in charge of running an `event handler` for each SDX participant. This `event handler`
receives network events from `xrs` module (BGP updates), `arproxy` module (ARP requests), and participants's
control interface (high-level policy changes). It processes incoming network events to generate new
BGP announcements and data plane updates. It sends the BGP announcements to the `xrs` module and
dp updates to the `flanc` module. 

## Run arproxy

```bash
$ git checkout xrs
$ cd ~/sdx-ryu/pctrl/
$ sudo python participant_controller.py <example-name> <participant id> (e.g sudo python route_server.py simple 1)
```
