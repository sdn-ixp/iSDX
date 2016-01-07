# Testing iSDX Behavior

This directory includes tools for supporting the automated regression testing of the iSDX system.
It consists of a constellation of traffic receivers and generators (tnodes) whose behavior can be orchestrated by a managing process (tmgr), which uses a JSON specification to define the testing actions to be performed.
The tests are designed to generate traffic that will be influenced by the policies established in the switching fabric by the iSDX controller and to verify that the proper pathways are traversed.
The role of the testing framework using the multi-table configuration (test-mt) is shown below.

## Example Configuration 
![Experimental Setup](https://docs.google.com/drawings/d/1Hw2UdhdyfINE-BmS8xSCfEND3ZxkIzhgMoLKK9yb4Fc/pub?w=960&h=720)

This test setup consists of 3 Participating Autonomous Systems, A, B and C, with routers A1, B1, C1 and C2 implemented using mininext.
Routers B1, C1 and C2 have all advertised routes to 140.0.0.0/24.
Specific inbound and outbound policies established by A and C will alter the default routes used for traffic.
Participant A has outbound policies that steer port 80 traffic to B and port 4321 and 4322 traffic towards C.
Participant C has inbound policies that steer port 4321 traffic towards router C1 and port 4322 traffic towards router C2.

Each mininext router host now includes a tnode process that accepts instructions to bind to and listen for traffic on a specified interface and port, as well as commands to generate traffic towards a specified port using a specified outbound interface.
The tnodes contain no knowledge of the tests to be performed; they are dynamically driven by the tmgr controller and are subsequently interrogated by the tmgr to see if expected traffic has arrived.
The tnodes and tmgr communicate over a separate management network to avoid the need to establish SDX paths for their traffic.  This is based on unix domain sockets for the mininext case, and an additional set of interfaces for HW implementations.

A tnode executes a limited number of commands:
- create a listener on a given port and interface
- send traffic to a given destination using a specified port and interface
- retrieve the result of a previously generated transmission based on its ID
- execute a local command (e.g., route -n)

A tmgr uses a JSON specification to describe listeners, tests and programs.
Note that the tnodes on hosts B, C1 and C2 all open the same set of ports.
In this way, misdirected traffic will still find a home and can be interrogated with tmgr

```
{
	"hosts": {
	
		"a1": {
			"interfaces": {
	    	}
		} ,
		
		"b1": {
			"interfaces": {
	     		"i0": { "bind": "140.0.0.1", "port": 80 },
				"i1": { "bind": "140.0.0.1", "port": 4321 },
				"i2": { "bind": "140.0.0.1", "port": 4322 }
	    	}
		} ,
		
		"c1": {
			"interfaces": {
	     		"i0": { "bind": "140.0.0.1", "port": 80 },
				"i1": { "bind": "140.0.0.1", "port": 4321 },
				"i2": { "bind": "140.0.0.1", "port": 4322 }
	    	}
		} ,
		
		"c2": {
			"interfaces": {
	     		"i0": { "bind": "140.0.0.1", "port": 80 },
				"i1": { "bind": "140.0.0.1", "port": 4321 },
				"i2": { "bind": "140.0.0.1", "port": 4322 }
	    	}
		}
	} ,
	
	"tests": {
		"t0": { "src": "a1", "baddr": "100.0.0.1", "daddr": "140.0.0.1", "dport": 80, "xdst": "b1", "xifc": "i0" },
		"t1": { "src": "a1", "baddr": "100.0.0.1", "daddr": "140.0.0.1", "dport": 4321, "xdst": "c1", "xifc": "i1" },
		"t2": { "src": "a1", "baddr": "100.0.0.1", "daddr": "140.0.0.1", "dport": 4322, "xdst": "c2", "xifc": "i2" }
	} ,
	
	"commands": {
		"x0": { "cmd": "route -n" },
		"x1": { "cmd": "ps a" },
		"x2": { "cmd": "sudo ovs-ofctl dump-flows s1" },
		"x3": { "cmd": "sudo ovs-ofctl dump-flows s2" },
		"x4": { "cmd": "sudo ovs-ofctl dump-flows s3" },
		"x5": { "cmd": "sudo ovs-ofctl dump-flows s4" }	
	}
}
```

In the figure shown above, tmgr executes test t0.  This sends a request (1) to source a1 instructing it to bind to 100,0.0.1 and send traffic (2) to 140.0.0.1 on port 80.
A previously established listener i0 on host b1 port 80 receives the traffic.
Also in the test definition is the expected host (b1) and listener (i0) for the traffic.
The tmgr interrogates b1 (3) for any activity on that host to verify data delivery, and could potentially check other hosts for any misdirected traffic.

A test script will automate the entire process of establishing the mininext configuration, starting all the ancillary processes and running the tests.
A simple regression test would look like:
```
cd ~/iSDX/test
sudo sh startup.sh 2 test-mt test-ms
```
This will run tests test-mt and test-ms in the examples directory twice.
Log output will be placed in the test directory.
The tmgr test in the startup shell is:
```
python tmgr.py $BASE/examples/$TEST/config/test.cfg l 'r x0 a1 b1 c1 c2' 'e x1 x2 x3 x4 x5' t
```
Where $BASE is ~/iSDX and $TEST is the test name (test-ms or test-mt as found in the examples directory).
The specific operations are:
- l: start all listeners on all hosts
- 'r x0 a1 b1 c1 c2': remotely run command x0 (route -n) on hosts a1, b1, c1, and c2 
- 'e x1 x2 x3 x4 x5': execute commands x1, x2, x3, and x4 locally (to dump flows)
- t: run all tests
Other options can be found by executing tmgr without arguments.

The output from a single test will contain:
```
b1:i0 OK: listener established for 140.0.0.1:80
b1:i1 OK: listener established for 140.0.0.1:4321
b1:i2 OK: listener established for 140.0.0.1:4322
c1:i0 OK: listener established for 140.0.0.1:80
c1:i1 OK: listener established for 140.0.0.1:4321
c1:i2 OK: listener established for 140.0.0.1:4322
c2:i0 OK: listener established for 140.0.0.1:80
c2:i1 OK: listener established for 140.0.0.1:4321
c2:i2 OK: listener established for 140.0.0.1:4322

MM:a1 REXEC x0: route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
140.0.0.0       172.0.1.1       255.255.255.0   UG    0      0        0 a1-eth0
150.0.0.0       172.0.1.2       255.255.255.0   UG    0      0        0 a1-eth0
172.0.0.0       0.0.0.0         255.255.0.0     U     0      0        0 a1-eth0

MM:b1 REXEC x0: route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
100.0.0.0       172.0.1.2       255.255.255.0   UG    0      0        0 b1-eth0
110.0.0.0       172.0.1.1       255.255.255.0   UG    0      0        0 b1-eth0
172.0.0.0       0.0.0.0         255.255.0.0     U     0      0        0 b1-eth0

MM:c1 REXEC x0: route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
100.0.0.0       172.0.1.4       255.255.255.0   UG    0      0        0 c1-eth0
110.0.0.0       172.0.1.2       255.255.255.0   UG    0      0        0 c1-eth0
172.0.0.0       0.0.0.0         255.255.0.0     U     0      0        0 c1-eth0

MM:c2 REXEC x0: route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
100.0.0.0       172.0.1.4       255.255.255.0   UG    0      0        0 c2-eth0
110.0.0.0       172.0.1.2       255.255.255.0   UG    0      0        0 c2-eth0
172.0.0.0       0.0.0.0         255.255.0.0     U     0      0        0 c2-eth0

MM:00 EXEC: x1: ps a
  PID TTY      STAT   TIME COMMAND
18821 pts/0    S+     0:00 sudo sh startup.sh 1 test-ms
18822 pts/0    S+     0:00 sh startup.sh 1 test-ms
18824 pts/0    R+     0:11 python /home/vagrant/iSDX/logServer.py SDXRegression.log.18822
...

MM:00 EXEC: x2: sudo ovs-ofctl dump-flows s1
NXST_FLOW reply (xid=0x4):
 cookie=0x14, duration=15.059s, table=0, n_packets=4, n_bytes=168, idle_age=14, priority=6,arp,in_port=3,dl_dst=ff:ff:ff:ff:ff:ff actions=output:5,output:6,output:7,output:8,output:4
 cookie=0x8, duration=15.077s, table=0, n_packets=11, n_bytes=1089, idle_age=1, priority=7,tcp,dl_dst=08:00:27:54:56:ea,
tp_dst=179 actions=output:7
 ...

MM:00 EXEC: x3: sudo ovs-ofctl dump-flows s2
NXST_FLOW reply (xid=0x4):
 cookie=0x21, duration=15.149s, table=0, n_packets=0, n_bytes=0, idle_age=15, priority=1 actions=output:1
 ...

MM:00 EXEC: x4: sudo ovs-ofctl dump-flows s3
NXST_FLOW reply (xid=0x4):
 cookie=0x10002, duration=2.172s, table=0, n_packets=0, n_bytes=0, idle_age=2, priority=2,tcp,dl_src=08:00:27:89:3b:9f,dl_dst=20:00:00:00:00:00/60:00:00:00:00:00,tp_dst=4321 actions=mod_dl_dst:80:00:00:00:00:03,output:2
 ...

MM:00 EXEC: x5: sudo ovs-ofctl dump-flows s4
NXST_FLOW reply (xid=0x4):
 cookie=0x16, duration=15.430s, table=0, n_packets=0, n_bytes=0, idle_age=15, priority=2,arp,in_port=1,arp_tpa=172.0.1.0
/24 actions=output:2
 ...

a1:XX INFO TEST 5666885175 bind:100.0.0.1 dst:140.0.0.1:80
a1:XX OK: TEST 5666885175 done
b1:i0 OK: XFER 5666885175 100.0.0.1:58270->140.0.0.1:80 29.1567709123 MBpS
MM:b1 OK: TEST t0 5666885175 TEST PASSED 29.1567709123 MBpS
a1:XX INFO TEST 3518395828 bind:100.0.0.1 dst:140.0.0.1:4321
a1:XX OK: TEST 3518395828 done
c1:i1 OK: XFER 3518395828 100.0.0.1:45081->140.0.0.1:4321 81.2279277926 MBpS
MM:c1 OK: TEST t1 3518395828 TEST PASSED 81.2279277926 MBpS
a1:XX INFO TEST 3575402122 bind:100.0.0.1 dst:140.0.0.1:4322
a1:XX OK: TEST 3575402122 done
c2:i2 OK: XFER 3575402122 100.0.0.1:50616->140.0.0.1:4322 30.8792736737 MBpS
MM:c2 OK: TEST t2 3575402122 TEST PASSED 30.8792736737 MBpS
MM:00 INFO: BYE
```

If you need to debug a test, the simplest way is to edit the startup.sh script and change the environment variable INTERACTIVE to a non zero value
This will leave the network intact and not start the cleanup script until you exit mininext with a control-D.
You can then run tmgr interactively in another window, or use mininext commands to check routes.
A useful tmgr command is 'pending' which will query all tnodes for any results that have not been claimed, which would likely be due to misdirected traffic.

