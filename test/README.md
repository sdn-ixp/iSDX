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

A tmgr uses a JSON specification to describe listeners, tests and programs:

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
		"x1": { "cmd": "ps a" }	
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
for i in 1 2 3 4 5 6 7 8 9 10
do
	sudo sh startup.sh test-mt
done
```
The expected output looks like:
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
100.0.0.0       172.0.1.2       255.255.255.0   UG    0      0        0 c1-eth0
110.0.0.0       172.0.1.1       255.255.255.0   UG    0      0        0 c1-eth0
172.0.0.0       0.0.0.0         255.255.0.0     U     0      0        0 c1-eth0
MM:c2 REXEC x0: route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
100.0.0.0       172.0.1.2       255.255.255.0   UG    0      0        0 c2-eth0
110.0.0.0       172.0.1.1       255.255.255.0   UG    0      0        0 c2-eth0
172.0.0.0       0.0.0.0         255.255.0.0     U     0      0        0 c2-eth0
a1:XX INFO TEST 4811259117 bind:100.0.0.1 dst:140.0.0.1:80
a1:XX OK: TEST 4811259117 done
b1:i0 OK: XFER 4811259117 100.0.0.1:42906->140.0.0.1:80 241.731661517 MBpS
MM:b1 OK: TEST t0 4811259117 TEST PASSED 241.731661517 MBpS
a1:XX INFO TEST 4421257800 bind:100.0.0.1 dst:140.0.0.1:4321
a1:XX OK: TEST 4421257800 done
c1:i1 OK: XFER 4421257800 100.0.0.1:37810->140.0.0.1:4321 186.235681901 MBpS
MM:c1 OK: TEST t1 4421257800 TEST PASSED 186.235681901 MBpS
a1:XX INFO TEST 3580719343 bind:100.0.0.1 dst:140.0.0.1:4322
a1:XX OK: TEST 3580719343 done
c2:i2 OK: XFER 3580719343 100.0.0.1:57181->140.0.0.1:4322 266.701893691 MBpS
MM:c2 OK: TEST t2 3580719343 TEST PASSED 266.701893691 MBpS
MM:00 INFO: BYE
```
