# generate slightly more complex case than test-ms
# 5 participants
# extra flows from a second sourcing node
# be careful if specifying duplicate advertised routes from both sources (100.0.0.1)
# as there are no return path rules

mode multi-switch
participants 6
peers 1 2 3 4 5 6

#participant ID ASN PORT MAC IP PORT MAC IP
participant 1 100 PORT MAC 172.0.0.1/16
participant 2 200 PORT MAC 172.0.0.11/16
participant 3 300 PORT MAC 172.0.0.21/16
participant 4 400 PORT MAC 172.0.0.31/16
participant 5 500 PORT MAC 172.0.0.41/16 PORT MAC 172.0.0.42/16 PORT MAC 172.0.0.43/16
participant 6 600 PORT MAC 172.0.0.51/16 PORT MAC 172.0.0.52/16 PORT MAC 172.0.0.53/16

host AS ROUTER _ IP           # host names of form a1_100 a1_110

announce 1 100.0.0.0/24 
announce 2 110.0.0.0/24
announce 3 140.0.0.0/24 
announce 4 140.0.0.0/24 
announce 5 140.0.0.0/24
announce 6 140.0.0.0/24 

outflow a1 -c 1 -t 80 > d
outflow a1 -c 2 -t 81 > e
outflow a1 -c 3 -t 82 > e
outflow a1 -c 4 -t 83 > e

outflow b1 -c 5 -t 80 > d
outflow b1 -c 6 -t 81 > f
outflow b1 -c 7 -t 82 > f
outflow b1 -c 8 -t 83 > f

inflow -c 9 -t 81 > e2
inflow -c 10 -t 82 > e3
inflow -c 11 -t 81 > f2
inflow -c 12 -t 82 > f3

listener AUTOGEN 80 81 82 83 88

test init {
	listener
}

test regress {
	comment b flows should go to d and f
	test xfer
	comment removing b flow rules
	comment b flows should all default to c
	unflow b 5 6 7 8
	delay 5
	test xfer2
	comment adding b flow rules to use d for 80 and e for 81 and 82
	comment b flows should now go to d and e
	outflow b1 -c 5 -t 80 > d
	outflow b1 -c 6 -t 81 > e
	outflow b1 -c 7 -t 82 > e
	outflow b1 -c 8 -t 83 > e

	exec a1 ip -s -s neigh flush all
	exec b1 ip -s -s neigh flush all
	
	delay 5
	test xfer3
}

test xfer {
	verify a1_100 d1_140 80
	verify a1_100 e2_140 81
	verify a1_100 e3_140 82
	verify a1_100 e1_140 83
	verify a1_100 c1_140 88
	exec b1 arp
	verify b1_110 d1_140 80
	verify b1_110 f2_140 81
	verify b1_110 f3_140 82
	verify b1_110 f1_140 83
	verify b1_110 c1_140 88
}

test xfer2 {
	verify a1_100 d1_140 80
	verify a1_100 e2_140 81
	verify a1_100 e3_140 82
	verify a1_100 e1_140 83
	verify a1_100 c1_140 88
	exec b1 arp
	verify b1_110 c1_140 80
	verify b1_110 c1_140 81
	verify b1_110 c1_140 82
	verify b1_110 c1_140 83
	verify b1_110 c1_140 88
}

test xfer3 {
	verify a1_100 d1_140 80
	verify a1_100 e2_140 81
	verify a1_100 e3_140 82
	verify a1_100 e1_140 83
	verify a1_100 c1_140 88
	exec b1 arp
	verify b1_110 d1_140 80
	verify b1_110 e2_140 81
	verify b1_110 e3_140 82
	verify b1_110 e1_140 83
	verify b1_110 c1_140 88
}

test info {
	comment empty info
}

test info2 {
	local ovs-ofctl dump-flows S1
	local ovs-ofctl dump-flows S2
	local ovs-ofctl dump-flows S3
	local ovs-ofctl dump-flows S4
}