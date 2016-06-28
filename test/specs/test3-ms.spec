
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
