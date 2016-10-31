# generate network equivalent to generic test-ms
# 3 participants
# combination of inbound and outbound rules
# additional test for unmatched traffic on port 8888

mode multi-switch
participants 3
peers 1 2 3

participant 1 100 PORT MAC 172.0.0.1/16
participant 2 200 PORT MAC 172.0.0.11/16
participant 3 300 PORT MAC 172.0.0.21/16 PORT MAC 172.0.0.22/16

host AS ROUTER _ IP           # testnode names of form a1_100 a1_110

announce 1 100.0.0.0/24 -110.0.0.0/24
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
	withdraw b1 140.0.0.0/24
	exec a1 ip -s -s neigh flush all
	delay 4
	test xfer2
	announce b1 140.0.0.0/24
	exec a1 ip -s -s neigh flush all
	delay 4
	test xfer
}
	
test init {
	listener
}

test xfer {
	verify a1_100 b1_140 80
	verify a1_100 c1_140 4321
	verify a1_100 c2_140 4322
	verify a1_100 b1_140 8888
}

test xfer2 {
	verify a1_100 c1_140 80
	verify a1_100 c1_140 4321
	verify a1_100 c2_140 4322
	verify a1_100 c1_140 8888
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
