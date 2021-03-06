# generate network equivalent to generic test-mt
# 3 participants
# combination of inbound and outbound rules
# additional test for unmatched traffic on port 8888

mode multi-table
participants 3
peers 1 2 3

participant 1 100 3 08:00:27:89:3b:9f 172.0.0.1/16
participant 2 200 4 08:00:27:92:18:1f 172.0.0.11/16
participant 3 300 5 08:00:27:54:56:ea 172.0.0.21/16 6 08:00:27:bd:f8:b2 172.0.0.22/16

host h NETNUMB _ AS ROUTER    # node names of the form h1_a1 h2_a1

announce 1 100.0.0.0/24 110.0.0.0/24
announce 2 140.0.0.0/24 150.0.0.0/24
announce 3 140.0.0.0/24 150.0.0.0/24

outflow a1 -t 80 > b
outflow a1 -t 4321 > c
outflow a1 -t 4322 > c

inflow -t 4321 > c1
inflow -t 4322 > c2

listener AUTOGEN 80 4321 4322 8888

test regress {
	test xfer
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

test info {
	local ovs-ofctl dump-flows S1
	exec a1 ip route
	bgp a1
	exec b1 ip route
	bgp b1
	exec c1 ip route
	bgp c1
	exec c2 ip route
	bgp c2
}
