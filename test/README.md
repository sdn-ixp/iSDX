# Testing iSDX Behavior with Torch

This directory includes the **T**raffic **Orch**istrator (torch) tools for the construction, launching and automated regression testing of an iSDX system configuration.
It is designed to work with both software defined environments based on mininet and on true hardware switch configurations.

* Torch constructs and launches an iSDX configuration using a simplified network specification. The example below is equivalent to the test-ms configuration in the top-level examples directory. See the section on **Additional Examples** below for more sophisticated network configurations and policy variations.
* Torch can run an automated set of tests to validate the policies established for the iSDX. These are used to send traffic to specific destinations, verify that the traffic has indeed been delivered, and search for traffic on other nodes if it is not found where expected.  Torch can be also used to announce and withdraw routes to change the BGP view of the world and to dynamically add and remove flow rules.
* Torch can be run in an interactive mode for experimenting with dynamic routing changes and policy updates.

Torch consists of a constellation of traffic receivers and generators (tnodes) managed by a controlling process (tmgr), which uses a specification file to define the hosts, network and testing actions to be performed.
A tnode is automatically started in each quagga host as part of mininet initialization.
The tests are typically designed to generate traffic that will be influenced by the policies established in the switching fabric and the advertised BGP routes.
For example, the tests in test0-mt (multi-table) verify that traffic on specific tcp ports are directed to different destinations based on a combination of outbound (A1) and inbound (C1 and C2) flow rules.
The tests in tes1-ms (multi-switch) include the test-mt tests, but also include cases that withdraw a route from B1, and later restore it, causing dynamic changes in traffic flow.

## Example Configuration 
![Experimental Setup](https://docs.google.com/drawings/d/1LK9VEROcRoXWtfJXkBJ5guFLMEzu-PqZxLG4hCILtDI/pub?w=960&h=720)

This test setup consists of 3 Participating Autonomous Systems, A, B and C, with routers A1, B1, C1 and C2 implemented using mininet.
Routers B1, C1 and C2 have all advertised routes to 140.0.0.0/24 and 150.0.0.0/24.
Router A1 has announced routes to 100.0.0.0/24 and 110.0.0.0/24.
Specific outbound and inbound policies established by A and C will alter the default routes used for traffic.
Participant A has outbound policies that steer port 80 traffic to B and port 4321 and 4322 traffic towards C.
Participant C has inbound policies that steer port 4321 traffic towards router C1 and port 4322 traffic towards router C2.

### Testing Route Withdrawal with In-place iSDX Policies

In this example we verify that traffic will be routed according to established policies, and that when a route is withdrawn, traffic will not be sent to an autonomous system even if it has an explicit policy to do so. For the latter case, we will withdraw the route to 140.0.0.0/24 for edge router B1. This should redirect A's traffic on port 80 to C1 instead of using the outbound rule to send it to B. The steps are:

1. Tmgr instructs h1_a1 to send traffic to port 80 on the 140 network. The expectation is that this will be routed to B based on A's outbound rule.
2. The tnode at h1_a1 binds a socket to the 100 network and connects to and sends data to the 140 network.
3. Tmgr queries the tnode on the expected destination behind B (h1_b1) for evidence of the transfer.
4. Tmgr instructs B1 to withdraw its route for the 140 network.
5. Tmgr again instructs h1_a1 to send traffic to port 80 on the 140 network. Even though A still has an outbound rule for port 80, the traffic will be routed via C1 to h1_c1.
6. As before, the tnode at h1_a1 binds a socket to the 100 network and connects to and sends data to the 140 network.
7. As the test definition still defines h1_b1 as the recipient, tmgr will query for the traffic there. Failing to find it there, tmgr will interrogate all hosts to locate the transfer, in this case, on h1_c1

The network specification is shown below. Only the **test name { commands }** sequences define tests that will be run by tmgr. The remaining information defines the configuration of the network.

```
mode multi-switch                         # iSDX mode - multi-table or multi-switch
participants 3                            # number of participants
peers 1 2 3                               # peering relationships

participant 1 100 5 08:00:27:89:3b:9f 172.0.0.1/16    # participant id, ASN, switch port, MAC, IP
participant 2 200 6 08:00:27:92:18:1f 172.0.0.11/16
participant 3 300 7 08:00:27:54:56:ea 172.0.0.21/16 8 08:00:27:bd:f8:b2 172.0.0.22/16 # 2 border routers

#host AS ROUTER _ IP                       # node names of form a1_100 a1_110
host h NETNUMB _ AS ROUTER                 # node names of the form h1_a1 h2_a1

announce 1 100.0.0.0/24 110.0.0.0/24       # routes advertised by A
announce 2 140.0.0.0/24 -150.0.0.0/24      # routes advertised by B (minus => create host but don't announce)
announce 3 140.0.0.0/24 150.0.0.0/24       # routes advertised by C

flow a1 80 >> b
flow a1 4321 >> c
flow a1 4322 >> c
flow c1 << 4321
flow c2 << 4322

listener AUTOGEN 80 4321 4322 8888         # which tcp ports to listen to for data transfer connections
	
test init {                                # init - start the tcp listeners
	listener
}

test regress {                             # regression - transfers intermixed with withdraw / announce
	test xfer                              # run the data transfers - traffic on 80 will go to B
	withdraw b1 140.0.0.0/24               # withdraw B1 advertisement for route to 140
	exec a1 ip -s -s neigh flush all       # flush a1 arp cache
	delay 2
	test xfer                              # run the data transfer - traffic on 80 will NOT go to B
	announce b1 140.0.0.0/24               # restore the B1 announcement of the route to 140
	exec a1 ip -s -s neigh flush all       # flush a1 arp cache
	delay 2
	test xfer                              # run the data transfers - traffic on 80 will go to B
}

test xfer {                                # common definition of data transfers
	verify h1_a1 h1_b1 80
	verify h1_a1 h1_c1 4321
	verify h1_a1 h1_c2 4322
	verify h1_a1 h1_c1 888
}

test info {                                # dump the world
	local ovs-ofctl dump-flows s1          #   switches
	local ovs-ofctl dump-flows s2
	local ovs-ofctl dump-flows s3
	local ovs-ofctl dump-flows s4
	exec a1 ip route                       #   routes seen by this router
	bgp a1                                 #   routes advertised by this router
	exec b1 ip route
	bgp b1
	exec c1 ip route
	bgp c1
	exec c2 ip route
	bgp c2
}
``` 
When creating a software (mininet) configuration, each edge router (e.g., c2) and interior host (e.g., h1_c2) will include a tnode process to receive and act upon commands.
The tnodes contain no knowledge of the tests to be performed; they are dynamically driven by the tmgr controller and are subsequently interrogated by tmgr to see if expected traffic has arrived.
This includes establishing initial listeners on specified tcp and udp ports to receive traffic.
The tnodes and tmgr communicate over a separate management network to avoid the need to establish SDX paths for their traffic.  This is based on unix domain sockets for the mininet case, and an additional set of interfaces for HW implementations.

***NOTE*** The latest version of the torch software has split the mininet specification apart from the torch tests.
As a convenience, the spec file format has remained the same, but the torch _tmgr_ command now uses a separate _torch.cfg_ file to define the hosts and commands.
This file is automatically generated when the spec file is processed.
As an example, the _torch.cfg_ file corresponding to the above spec is shown below.
The tests are copied directly.
The details for the hosts are separately enumerated so torch commands can find hosts (for common torch commands),
BGP edge-routers (for announce/withdraw torch commands) and
participants (for dynamic flow manipulation).
More importantly, this separation makes it easier to test a hardware implementation without constructing an equivalent mininet configuration first.
```
bgprouters {
        a1 /tmp/a1
        b1 /tmp/b1
        c1 /tmp/c1
        c2 /tmp/c2
}

hosts {
        h1_a1 /tmp/h1_a1 100.0.0.1 80 4321 4322 8888
        h1_b1 /tmp/h1_b1 140.0.0.1 80 4321 4322 8888
        h1_c1 /tmp/h1_c1 140.0.0.1 80 4321 4322 8888
        h1_c2 /tmp/h1_c2 140.0.0.1 80 4321 4322 8888
        h2_a1 /tmp/h2_a1 110.0.0.1 80 4321 4322 8888
        h2_b1 /tmp/h2_b1 150.0.0.1 80 4321 4322 8888
        h2_c1 /tmp/h2_c1 150.0.0.1 80 4321 4322 8888
        h2_c2 /tmp/h2_c2 150.0.0.1 80 4321 4322 8888
}

participants {
        a localhost:5551
        b localhost:5552
        c localhost:5553
}

test regress {
        test xfer
}

test info {
        local ovs-ofctl dump-flows S1
        local ovs-ofctl dump-flows S2
        local ovs-ofctl dump-flows S3
        local ovs-ofctl dump-flows S4
        exec a1 ip route
        bgp a1
        exec b1 ip route
        bgp b1
        exec c1 ip route
        bgp c1
        exec c2 ip route
        bgp c2
}

test init {
        listener
}

test xfer {
        verify h1_a1 h1_b1 80
        verify h1_a1 h1_c1 4321
        verify h1_a1 h1_c2 4322
        verify h1_a1 h1_b1 8888
}
```

To run an end-to-end test, create a test.spec file as above and then use the *gen_test.py* script from the test directory to build the detailed iSDX configuration files. All configuration files will be places in *output/testname* where *testname* is the name of the specification file with the *.spec* suffix removed.
Move this directory to the top-level *examples* directory. The *buildall.sh* script will construct and move all the examples below.

To execute the tests from the example above, run:

```
cd ~/iSDX/test
sh buildall.sh
sudo bash startup.sh test1-ms
```
This will run the iSDX software on the configuration *test1-ms* in the *examples* directory.
Log output will be placed in the *regress* directory.

Abridged output from this test will include:

<pre>
<b>MM:h1_a1 VERIFY: h1_a1:XX OK: TEST 2005119051 bind:100.0.0.1 dst:140.0.0.1:80 TRANSFER COMPLETE
MM:h1_b1 TEST PASSED 2005119051 100.0.0.1:49703->140.0.0.1:80 9.2429986625 MBpS</b>
...
MM:b1 WITHDRAW:  140.0.0.0/24
MM:00: DELAY 5
<b>MM:h1_a1 VERIFY: h1_a1:XX OK: TEST 5652012792 bind:100.0.0.1 dst:140.0.0.1:80 TRANSFER COMPLETE
MM:h1_b1 TEST FAILED - DATA NOT FOUND ON EXPECTED HOST (h1_b1) - checking all hosts
MM:h1_c1 TEST MISDIRECTED 5652012792 to h1_c1:00 COMPLETE 5652012792 100.0.0.1:37085->140.0.0.1:80 9.82659147608 MBpS</b>
...
MM:b1 ANNOUNCE:  140.0.0.0/24
MM:a1 REXEC: ip -s -s neigh flush all 
*** Flush is complete after 1 round ***
MM:00: DELAY 2
<b>MM:h1_a1 VERIFY: h1_a1:XX OK: TEST 2829810118 bind:100.0.0.1 dst:140.0.0.1:80 TRANSFER COMPLETE
MM:h1_b1 TEST PASSED 2829810118 100.0.0.1:38560->140.0.0.1:80 8.68190197967 MBpS</b>
...
</pre>
```
```

To pause a test so additional tmgr commands can be issued, use the *-i* option.
This will run any supplied tests and then accept tmgr commands directly from the startup.sh window.


# Creating Configurations and Tests


## Specification File Format
By convention, participants or autonomous systems (AS) are numbered from **1**.
In a flow rule, the corresponding AS is lettered starting from **a**.
Edge routers, which map to quagga hosts, are identified as the AS letter concatenated with the edge router ID, starting from 1 (although internally and for autogenerated MAC address (see below) the index runs from 0).
If more than 26 AS'es are needed, doubling of letters is used, i.e., participant 27 is **aa**, participant 28 is **ab**.

A specification file contains the following constructs in the order shown.
- __mode__ 
defines the switch configuration to be used.
Values are either 'multi-switch' or 'multi-table'
- __participants__
declares the number of participating autonomous systems in the configuration.
- __peers__
declares the peering relationships between participating autonomous systems.
Multiple peerings can be defined.
- __participant__
defines the configuration for each AS.
The additional arguments are:
  * participant number - starts with 1
  * autonomous system number
  * switch port number - starts at 3 for mode multi-table and at 5 for mode multi-switch.  The special argument 'PORT' will automatically use the next available port number regardless of mode.
  * mac address for this edge router.
  The special argument 'MAC' will generate a unique MAC address with a known pattern to simplify debugging.
  Currently the format is 08:00:bb:bb:PP:RR where PP is the participant number and RR is the router index.
  * IP address for this interface
  * Additional triplets of port, mac and IP for the other edge routers in this AS
- __host__ defines the format for labeling hosts (not routers).
Host names are constructed automatically and implied in the *verify* tests described below.
A host name is constructed by concatenating one or more of the following sequences:
  * *characters*  -    a sequence of characters that will be used in the host name as is
  * NETNUMB - the index of the AS networks reachable from this AS starting with 1 
  * IP - the first 8 bits of the network address reachable from this AS
  * ROUTER - the index of the border router for this AS
  * AS - the letter(s) coresponding to the participant number
  
  Two example formats are shown below.
  The firsrt format is convenient when there are large numbers of participants or participant border routers as the route prefix is incorporated into the host name.
  The second format is the convention used in the *test-ms* and *test-mt* examples.
  ```
  host AS ROUTER _ IP                    # host names of form a1_100 a1_110
  host h NETNUMB _ AS ROUTER             # host names of the form h1_a1 h2_a1
  ```
- __announce__ declares the networks that this AS can reach.
The additional arguments are:
  * participant number for these announcements
  * one or more CIDR format network descriptions of the form a.b.c.d/prefix-bits. An interface on the corresponding quagga host will be created with the default address a.b.c.1.
  **NOTE:** If an announced network begins with a minus sign, a host will be created to represent that network, but a route to that network will not be announced to the world.
- __outflow__ defines an outbound flow rule. **NOTE:** If no inbound or outbound flow rules are defined statically, dynamic flows in that direction will not work.
  * `outflow edgerouter [-c cookie] [-s srcaddr/prefix] [-d dstaddr/prefix] [-u udpport] [-t tcpport] > participant`
- __inflow__ defines an inbound flow rule. **NOTE:** If no inbound or outbound flow rules are defined statically, dynamic flows in that direction will not work.
  * `inflow [-c cookie] [-s srcaddr/prefix] [-d dstaddr/prefix] [-u udpport] [-t tcpport] > edge_router`
- __listener__ defines the listeners that will be created on each quagga host to receive data routed through the switching fabric.
The additional arguments are:
  * host for this listener
  * binding address to use on that host
  * one or more tcp ports on which to listen
- __test name { commands }__ defines a labeled group of torch commands that can be invoked as a whole. See the next section for a description of the command set.

## Torch Usage
The tnode and tmgr commands use the same configuration file to define host locationss and the predefined tests.
(Tnode only uses the locations; all test details are sent by tmgr.)
```
python tnode.py torch.cfg hostname
python tmgr.py torch.cfg [ command ... ]
```
For tmgr, each command line command is considered a line of input, so if multiple tokens are involved, use quotes (e.g., tmgr torch.cfg 'test xfer' 'withdraw b1 140.0.0.0/24').
If no command line commands are given, tmgr will read standard input for commands.

## Torch Commands
```
    hosts                           # list known hosts, bgprouters and participants
    listener host bind port         # start a listener on the host to receive data
    test test_name ...              # run a multi-command test
    verify srchost dsthost tcpport  # verify a data transfer - see below for details
    announce edgerouter network ... # advertise a BGP route
    withdraw edgerouter network ... # withdraw a BGP route
    outflow edgerouter [-c cookie] [-s srcaddr/prefix] [-d dstaddr/prefix] [-u udpport] [-t tcpport] > participant  # define a new outbound flow
    inflow [-c cookie] [-s srcaddr/prefix] [-d dstaddr/prefix] [-u udpport] [-t tcpport] > edge_router              # define a new inbound flow
    unflow participant cookies ...  # remove participant flows
    bgp edgerouter                  # show advertised bgp routes - router password is hardcoded (ugh)
    router edgerouter arg arg ...   # run arbitrary command on router - args will be surrounded by enable/quit
    delay seconds                   # pause for things to settle
    exec host|edgerouter cmd arg ...# execute cmd on node
    local cmd arg arg               # execute cmd on local machine
    pending host                    # check if any pending or unclaimed data transfers are on host
    send host bind daddr port       # send data xmit request to source node
    comment commentary ...          # print a comment
    reset host                      # reset (close) listeners - takes a few seconds to take effect
    kill host                       # terminate a node, non recoverable
    dump host                       # dump any messages from a node - mainly to see if nodes are on-line
    config                          # print result of spec file parsing
    help                            # print this message
    echo host arg ...				# simple tnode echo-back
    quit                            # exit this manager; leaves nodes intact
```        
##### More details on the verify command
  The traffic manager will coordinate with the traffic node on the source host to bind a socket to the appropriate interface and send data to the address implied by the destination host.
  Since in general there will be multiple edge routers that advertise the same network, it is up to the switching fabric to determine the ultimate destination based on flow rules and possibly default routing (if no flow rules match).
  
  The use of the destination host name in the verify command is only a convenience to specify that address.
  Tmgr will look up that host and get the corresponding network address as described by the *announce* configuration line in the spec file.
  However, the destination edge router name will be used by the traffic manager to confirm that the data transfer did indeed terminate on that edge router, and therefore that the switching fabric properly routed the traffic.
  If it is not found there, the traffic manager will search all hosts for the transfer results.

## Additional Examples
The specification files can be found in the *test/specs* directory.
To generate the configuration files, run the buildall.sh script from the test directory.
This will create all necessary data files and move them to the top-level *examples* directory.
(Currently, these configuration files must be placed in that directory for the iSDX software to find them, but the tests can be run from the *test* directory.)

In the following diagrams, the black dashed lines indicate an Autonomous System (AS).
The colored dash-dot-dash lines indicate a peering relationship among AS'es (except for test6-ms, which uses colors to distinguish the multiple outbound rules).

### Configurations test0-ms and test0-mt
These configurations are equivalent to the test-ms and test-mt examples in the top level examples directory and are defined here as placeholders for the data transfer tests.

### Configurations test1-ms and test1-mt
These configurations are equivalent to test-ms and test-mt in the examples directory with the exception that the host names used follow the torch naming convention of **AS_NAME | ROUTER_NUMBER | UNDERSCORE _ NETWORK_PREFIX**.
For example c1_140 is the name of the host attached to the 140 network interface on the c1 edge router.
These examples also withdraw and announce the B1 route for 140.0.0.0/24.
 
AS A directs its port 80 traffic to AS B, and its port 4321 and 4322 traffic to AS C.
AS C has inbound rules that further refine flows to routers C1 for port 4321 and C2 for port 4322.
```
flow a1 80 >> b
flow a1 4321 >> c
flow a1 4322 >> c
flow c1 << 4321
flow c2 << 4322
```
![Experimental Setup](https://docs.google.com/drawings/d/1mOw8i23mZYNSj1eH4wwXECLwx6SViR0NaI4bgnAnaHs/pub?w=960&h=720)

### Configuration test2-ms 
This configuration is patterned on test1-ms, but adds 2 AS'es. It is intended to replicate a hardware test-bed configuration. A, C and D are patterned after A, B and C in test 1. An additional source, B, has its port 80 traffic sent to E. B also sends port 4321 and 4322 traffic to D.
```
flow a1 80 >> c
flow a1 4321 >> d
flow a1 4322 >> d
flow d1 << 4321
flow d2 << 4322
flow b1 80 >> e
flow b1 4321 >> e
flow b1 4322 >> e
```
![Experimental Setup](https://docs.google.com/drawings/d/1H8d_kWxee9txHfZx2k479A8NXjQHuHR3qnuTrcf3sBc/pub?w=960&h=720)

### Configuration test3-ms
This configuration replicates test1-ms four times, with each set of 3 AS'es restricted to its own peering group.
```
flow a1 80 >> b
flow a1 4321 >> c
flow a1 4322 >> c
flow c1 << 4321
flow c2 << 4322

flow d1 80 >> e
flow d1 4321 >> f
flow d1 4322 >> f
flow f1 << 4321
flow f2 << 4322

flow g1 80 >> h
flow g1 4321 >> i
flow g1 4322 >> i
flow i1 << 4321
flow i2 << 4322

flow j1 80 >> k
flow j1 4321 >> l
flow j1 4322 >> l
flow l1 << 4321
flow l2 << 4322
```
![Experimental Setup](https://docs.google.com/drawings/d/1LHTyuZR8qbzq7wp1HgpiprpMGeQ2XY2sUvlu6XwgcNM/pub?w=960&h=720)

### Configuration test4-ms
This configuration includes only outbound flow rules. AS A sends traffic to 8 other AS'es based on port number.
```
flow a1 80 >> b
flow a1 81 >> c
flow a1 82 >> d
flow a1 83 >> e
flow a1 84 >> f
flow a1 85 >> g
flow a1 86 >> h
flow a1 87 >> i
```
![Experimental Setup](https://docs.google.com/drawings/d/17XaTGOoCNJ8LDa5q_1Gh1-fpz64S7uRoY_m74mWXpRE/pub?w=960&h=720)

### Configuration test5-ms
This configuration includes only inbound flow rules. Inbound traffic is routed to 1 of 8 edge routers based on port number.
```
flow b1 << 80
flow b2 << 81
flow b3 << 82
flow b4 << 83
flow b5 << 84
flow b6 << 85
flow b7 << 86
flow b8 << 87
flow b9 << 88
```
![Experimental Setup](https://docs.google.com/drawings/d/1VTqNpCAfSlrvFzB8uM2bflbTBSGsMwV1AnWoc2IBwsc/pub?w=960&h=720)

### Configuration test6-ms
This configuration includes outbound flows across all AS'es. Each AS sources traffic to its 2 neighbors. Port 80 traffic moves clockwise.  Port 81 traffic moves counter clockwise.
```
flow a1 80 >> b
flow b1 80 >> c
flow c1 80 >> a
flow a1 81 >> c
flow b1 81 >> a
flow c1 81 >> b
```

![Experimental Setup](https://docs.google.com/drawings/d/1BjwMis_0_1QpmcmBonSbojuwbHC64L6YdB61zrJUl64/pub?w=960&h=720)

### Configuration test7-ms
This configuration demonstrates dynamic flow creation and deletion. The initial flow set-up is shown below.
The extra argument to the flow description specifies the cookie used by the switching fabric and is needed to remove the flow in a subsequent step.
Participant C is a catch-all and will be the default destination for any traffic not matched by a flow.
Similarly, e1 and f1 are used for traffic destined to e and f when there are no corresponding inbound rules.

Traffic from A is split as: port 80 to D, ports 81, 82 and 83 to E, and will remain consistent for the entire test.

Traffic from B is split as: port 80 to D, ports 81, 82 and 83 to F. Eventually the port 80, 81, 82 traffic will be sent to E.

Inbound rules for E and F will apply to port 81 (e2 and f2) and 82 (e3 and f3) traffic only. Port 83 traffic will default to e1 and f1

```
flow a1 1 80 >> d
flow a1 2 81 >> e
flow a1 3 82 >> e
flow a1 4 83 >> e

flow b1 5 80 >> d
flow b1 6 81 >> f
flow b1 7 82 >> f
flow b1 8 83 >> f

flow e2 9 << 81
flow e3 10 << 82
flow f2 11 << 81
flow f3 12 << 82
```

![Experimental Setup](https://docs.google.com/drawings/d/1Z8YKPaMJ1j-XQ84DynaYVvXBJKRgd97cfRrzAUvI2ws/pub?w=960&h=720)

The torch command _test xfer_ will exercise and verify this configuration.

The torch command _unflow b 5 6 7 8_ removes all of participant B's flows.
At this point, all traffic from B will default to participant C.

The torch command _test xfer2_ will exercise and verify this configuration.

Finally, we add new flows, this time sending ports 81, 82 and 83 to partipant E, while port 80 goes back to participant D.
````
flow b1 5 80 >> d
flow b1 6 81 >> e
flow b1 7 82 >> e
flow b1 8 83 >> e
exec a1 ip -s -s neigh flush all
exec b1 ip -s -s neigh flush all
````
The arp flushes ensure that the changes have propogated before the final test, _test xfer3_ is executed, verifying the new flows.
