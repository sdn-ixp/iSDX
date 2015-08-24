# FLANC - Reference Monitor

The reference monitor (refmon.py) is a ryu module and requires [Ryu](http://osrg.github.io/ryu/) to be installed.

__Install Ryu__

Clone Ryu  

    $ cd ~  
    $ git clone git://github.com/osrg/ryu.git  

Before installing it, replace flags.py with the provided file

    $ cp ~/sdx-ryu/flanc/flags.py ~/ryu/ryu/flags.py
    $ cd ~/ryu
    $ sudo python ./setup.py install

## Run RefMon

```bash
$ ryu-manager ~/sdx-ryu/flanc/refmon.py --refmon-config <path of config file>
```

There are two sample config files provided:

* refmon_ms.cfg - a config file for an SDX using Supersets and Multiple-Switches

* refmon_mt.cfg - a config file for an SDX using Supersets and Multiple-Tables
