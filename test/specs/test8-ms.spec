# test dynmaic flows with ip address matching

mode multi-switch
participants 5
peers 1 2 3 4 5

#participant ID ASN PORT MAC IP PORT MAC IP
participant 1 100 PORT MAC 172.0.0.1/16 
participant 2 200 PORT MAC 172.0.0.11/16 PORT MAC 172.0.0.12/16 PORT MAC 172.0.0.13/16
participant 3 300 PORT MAC 172.0.0.21/16 PORT MAC 172.0.0.22/16 PORT MAC 172.0.0.23/16
participant 4 400 PORT MAC 172.0.0.31/16 PORT MAC 172.0.0.32/16 PORT MAC 172.0.0.33/16
participant 5 500 PORT MAC 172.0.0.41/16 PORT MAC 172.0.0.42/16 PORT MAC 172.0.0.43/16

host AS ROUTER _ IP           # host names of form a1_100 a1_110

announce 1 100.0.0.0/24 101.0.0.0/24 102.0.0.0/24 103.0.0.0/24
announce 2 140.0.0.0/24 141.0.0.0/24 142.0.0.0/24 143.0.0.0/24
announce 3 140.0.0.0/24 141.0.0.0/24 142.0.0.0/24 143.0.0.0/24
announce 4 140.0.0.0/24 141.0.0.0/24 142.0.0.0/24 143.0.0.0/24
announce 5 140.0.0.0/24 141.0.0.0/24 142.0.0.0/24 143.0.0.0/24

outflow a1 -t 80 > b
outflow a1 -t 81 > c
outflow a1 -t 82 > d
outflow a1 -t 83 > e

inflow -t 80 > b3
inflow -t 81 > c3
inflow -t 82 > d3
inflow -t 83 > e3


listener AUTOGEN 80 81 82 83 88

test init {
	listener
}

test regress {
	test xfer
}

test xfer {
	verify a1_100 b3_140 80
	verify a1_100 c3_140 81
	verify a1_100 d3_140 82
	verify a1_100 e3_140 83
	
	verify a1_100 b1_140 88
	verify a1_101 b1_140 88
	verify a1_102 b1_140 88
	verify a1_103 b1_140 88
	
	verify a1_100 b1_141 88
	verify a1_101 b1_141 88
	verify a1_102 b1_141 88
	verify a1_103 b1_141 88
	
	verify a1_100 b1_142 88
	verify a1_101 b1_142 88
	verify a1_102 b1_142 88
	verify a1_103 b1_142 88
	
	verify a1_100 b1_143 88
	verify a1_101 b1_143 88
	verify a1_102 b1_143 88
	verify a1_103 b1_143 88
}

test out {
	outflow a1 -c 40 -s 103.0.0.0/24 > c
}

test in {
	inflow -c 33 -s 101.0.0.0/24 > b2
	inflow -c 33 -s 101.0.0.0/24 > c2
	inflow -c 33 -s 101.0.0.0/24 > d2
	inflow -c 33 -s 101.0.0.0/24 > e2
}

test info {
	local ovs-ofctl dump-flows S1
	local ovs-ofctl dump-flows S2
	local ovs-ofctl dump-flows S3
	local ovs-ofctl dump-flows S4
}