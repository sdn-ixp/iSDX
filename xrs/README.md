# xrs - SDX RS

This module is in charge of relaying BGP updates and announcements between the `exaBGP` 
and the `pctrlr` module respectively. It receives BGP updates from the `exaBGP` module and
forwards them to the `pctrlr`. It also receives announcements from the `pctrlr` which
it forwards to the `exaBGP` module.

## Run xrs

```bash
$ git checkout xrs
$ cd ~/sdx-ryu/xrs/
$ sudo python route_server.py <example-name> (e.g sudo python route_server.py simple)
```
