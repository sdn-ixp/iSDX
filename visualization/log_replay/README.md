# LogReplay

```bash
$ python ~/iSDX/visualization/log_replay/replay.py <path to config> <path to flow directory> <path to ports directory> <number of records> <time step>
```

* the time step determines how often (in seconds) an update published. you cannot go below 1 second.

* in lines 251 to 254 all the redis parameters can be configured

* a redis server needs to be running for the script to properly work

## Example

```bash
$ python ~/iSDX/visualization/log_replay/replay.py /home/vagrant/iSDX/visualization/test-ms.cfg /home/vagrant/iSDX/visualization/lts-data/flows /home/vagrant/iSDX/visualization/lts-data/ports 84 1
```
