
# Experiments to Evaluate SDX's Performance

## One time setup

### Step 1: Install MongoDB s/w
```bash
$ sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
$ echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.0.list
$ sudo apt-get update
$ sudo apt-get install -y mongodb-org
$ sudo service mongod start
```

### Step 2: Setup SDX-Parallel repo
- Clone the repo
```bash
$ git clone https://github.com/sdn-ixp/sdx-parallel.git
```
- Checkout the `testing` branch.

- Install dependencies:
```bash
$ sh ~/sdx-parallel/setup/sdx-setup.sh
```

### Step 3: Place RIB/Update files in appropriate directory.
#### RIB file
```bash
$ cd ~/sdx-parallel/examples/test-largeIX
$ cp <rib file> rib1.txt
```

#### BGP Update File
```bash
$ cd ~/sdx-parallel/xbgp/
$ cp <updates file> updates.txt
```

## Experiment 1:

##Goal: 
Evaluate the performance of `pctrl` for varying participant policies. We are changing the fraction of the total IXP participants for which we have SDN policies. 

### Step 1: Explore the experiment params
```bash
$ cd ~/sdx-parallel/pctrl/
$ vi change_fraction.sh
```
Experiment's params:
- ITERATIONS = 10 ---> Number of iterations.
- FRAC=(0.2 0.4 0.6,0.8, 1.0) ---> fraction of IXP participants for which each participant has forwarding actions.
- Mode = 0 ---> The mode for `xbgp.py` for this experiment where it will send first 5 minutes of BGP updates at normal rate.
- *Update* the `INSTALL_ROOT`, which is the path where `sdx-parallel` is installed. 

### Step 2: Run the experiment
```bash
$ . change_fraction.sh
```

### Step 3: Data Collection
After the expriment is complete. We will have all the log files in the directory: `~/sdx-parallel/pctrl/data/`. 

Zip all the these files for data analysis. 

## Experiment 2:

##Goal: 
Evaluate the performance of `pctrl` for varying rate at which BGP updates are sent. We are changing the rate at which BGP updates are sent to the `pctrl` and measuring how long does it takes to process each BGP update. 


### Step 1: Explore the experiment params
```bash
$ cd ~/sdx-parallel/pctrl/
$ vi change_update_rate.sh
```
Experiment's params:
- ITERATIONS = 5 ---> Number of iterations.
- FRAC = (0.1) ---> fraction of IXP participants for which each participant has forwarding actions.
- RATE = (20, 40, 60, 80, 100) ---> Rate at which BGP updates are sent to `pctrl`.
- Mode = 1 ---> The mode for `xbgp.py` for this experiment where it will send first 5 minutes of BGP updates at specified rate.
- *Update* the `INSTALL_ROOT`, which is the path where `sdx-parallel` is installed. 

### Step 2: Run the experiment
```bash
$ . change_update_rate.sh
```

### Step 3: Data Collection
After the expriment is complete. We will have all the log files in the directory: `~/sdx-parallel/pctrl/data/`. 

Zip all the these files for data analysis. 


## Debugging

### Generate configs/policies

```bash
$ cd  ~/sdx-parallel/examples/test-largeIX/
$ python generate_configs.py <frac>
```

Copy `asn_2_ip` and `asn_2_id` in pctrl directory
```bash
$  cp asn_2_* ~/sdx-parallel/pctrl
```

### Initialize RIBs for the participants
```bash
$ cd  ~/sdx-parallel/pctrl
$ python initialize_ribs.py 
```

### FLANC - Reference Monitor Logger

This script saves every flowmod with a timestamp to the specified file (e.g. test.log)

```bash
$ cd ~/sdx-parallel/flanc
$ ./reflog.py localhost 5555 sdx <path of log file>
```

#### Run xrs

```bash
$ cd ~/sdx-parallel/xrs
$ python route_server.py <name of example>
```

### Start the Pctrl
```bash
$ cd  ~/sdx-parallel/pctrl
$ python participant_controller.py test-largeIX <id> <output file name>
```

### xbgp - ExaBGP Simulator

This module reads bgp updates from a bgp dump file and sends them in ExaBGP format to xrs

#### Run xbgp

```bash
$ cd ~/sdx-parallel/xbgp
$ ./xbgp.py localhost 6000 xrs <path of bgp updates file> <rate=anything for mode 0> <mode=0> -d (for debugging)
```
