
# test multiple peering relationships
# 4 independent networks, each the same as the test-ms case

mode multi-switch
participants 12

#peers 1 2 3 4 5 6 7 8 9 10 11 12
peers 1 2 3
peers 4 5 6
peers 7 8 9
peers 10 11 12

#participant ID ASN PORT MAC IP PORT MAC IP
participant 1 100 PORT MAC 172.0.0.1/16
participant 2 200 PORT MAC 172.0.0.11/16
participant 3 300 PORT MAC 172.0.0.21/16 PORT MAC 172.0.0.22/16
participant 4 400 PORT MAC 172.0.0.31/16
participant 5 500 PORT MAC 172.0.0.41/16
participant 6 600 PORT MAC 172.0.0.51/16 PORT MAC 172.0.0.52/16
participant 7 700 PORT MAC 172.0.0.61/16
participant 8 800 PORT MAC 172.0.0.71/16
participant 9 900 PORT MAC 172.0.0.81/16 PORT MAC 172.0.0.82/16
participant 10 1000 PORT MAC 172.0.0.91/16
participant 11 1100 PORT MAC 172.0.0.101/16
participant 12 1200 PORT MAC 172.0.0.111/16 PORT MAC 172.0.0.112/16

host AS ROUTER _ IP           # host names of form a1_100 a1_110

announce 1 100.0.0.0/24
announce 2 140.0.0.0/24 
announce 3 140.0.0.0/24 
announce 4 101.0.0.0/24 
announce 5 140.0.0.0/24 
announce 6 140.0.0.0/24 
announce 7 102.0.0.0/24 
announce 8 140.0.0.0/24 
announce 9 140.0.0.0/24 
announce 10 103.0.0.0/24 
announce 11 140.0.0.0/24 
announce 12 140.0.0.0/24 

outflow a1 -t 80 > b
outflow a1 -t 4321 > c
outflow a1 -t 4322 > c
inflow -t 4321 > c1
inflow -t 4322 > c2

outflow d1 -t 80 > e
outflow d1 -t 4321 > f
outflow d1 -t 4322 > f
inflow -t 4321 > f1
inflow -t 4322 > f2

outflow g1 -t 80 > h
outflow g1 -t 4321 > i
outflow g1 -t 4322 > i
inflow -t 4321 > i1
inflow -t 4322 > i2

outflow j1 -t 80 > k
outflow j1 -t 4321 > l
outflow j1 -t 4322 > l
inflow -t 4321 > l1
inflow -t 4322 > l2

listener AUTOGEN 80 4321 4322 8888

# test src_host dst_host dst_port
# binding addresses are taken from the corresponding node definition
# destination is an expected destination

test init {
	listener
}

test regress {
	verify a1_100 b1_140 80
	verify a1_100 c1_140 4321
	verify a1_100 c2_140 4322
	verify a1_100 b1_140 8888
	
	verify d1_101 e1_140 80
	verify d1_101 f1_140 4321
	verify d1_101 f2_140 4322
	verify d1_101 e1_140 8888
	
	verify g1_102 h1_140 80
	verify g1_102 i1_140 4321
	verify g1_102 i2_140 4322
	verify g1_102 h1_140 8888
	
	verify j1_103 k1_140 80
	verify j1_103 l1_140 4321
	verify j1_103 l2_140 4322
	verify j1_103 k1_140 8888
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
