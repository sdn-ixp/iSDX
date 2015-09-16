# Experiment 1:

##Goal: 
Evaluate the performance of `pctrl` for varying participant policies.

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
$ sh sdx-parallel/setup/sdx-setup.sh
```

### Step 3: Place RIB file in appropriate directory.
```bash
$ cd ~/sdx-parallel/examples/test-largeIX
$ cp <rib file> rib1.txt
```

### Step 4: Explore the experiment script
```bash
$ cd ~/sdx-parallel/pctrl/
$ vi run_setup.sh
```
Experiment's params:
- ITERATIONS = 10 ---> Number of iterations
- FRAC=(0.2 0.4 0.6,0.8, 1.0) ---> fraction of IXP participants for which each participant has forwarding actions

### Step 5: Run the experiment
```bash
$ . change_fraction.sh
```

### Step 6: Data Collection
After the expriment is complete. We will have all the log files in the directory: `~/sdx-parallel/pctrl/data/`. 

Zip all the these files for data analysis. 



