# FLANC - Reference Monitor

The reference monitor (refmon.py) is a ryu module and requires [Ryu](http://osrg.github.io/ryu/) to be installed.

__Install Ryu__

If you haven't already done so, install git and python-pip:
```bash
$ sudo apt-get install -y git python-pip
```

Run setup/ryu-setup.sh
```bash
$ sh setup/ryu-setup.sh
```

This will install ryu along with dependencies, and also extend the supported flags with the provided ryu-flags.py.

## Run RefMon

```bash
$ ryu-manager ~/iSDX/flanc/refmon.py --refmon-config <path of config file>
```

To log all received flow mods to a file just run it like this:

```bash
$ ryu-manager ~/iSDX/flanc/refmon.py --refmon-config <path of config file> --refmon-flowmodlog <path of log file>
```

# FLANC - Reference Monitor Log Replay

## Run RefMon

After logging all the flow mods, the flow mods can be replayed using LogClient.

```bash
$ ryu-manager ~/iSDX/flanc/refmon.py --refmon-config <path of config file>
```

```bash
$ ./log_client.py localhost 5555 sdx <path of input file>
```
