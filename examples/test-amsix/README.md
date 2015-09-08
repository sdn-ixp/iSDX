# FLANC - Reference Monitor Logger

This script saves every flowmod with a timestamp to the specified file (e.g. test.log)

```bash
$ cd ~/sdx-parallel/flanc
$ ./reflog.py localhost 5555 sdx <path of log file>
```

# xbgp - ExaBGP Simulator

This module reads bgp updates from a bgp dump file and sends them in ExaBGP format to xrs

## Run xbgp

```bash
$ cd ~/sdx-parallel/xbgp
$ ./xbgp.py localhost 6000 xrs <path of bgp updates file>
```

