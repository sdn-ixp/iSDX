# test outbound rules
# 1 source, many receivers

mode multi-switch
participants 9
peers 1 2 3 4 5 6 7 8 9

#participant ID ASN PORT MAC IP PORT MAC IP
participant 1 100 PORT MAC 172.0.0.1/16
participant 2 200 PORT MAC 172.0.0.11/16
participant 3 300 PORT MAC 172.0.0.21/16
participant 4 400 PORT MAC 172.0.0.31/16
participant 5 500 PORT MAC 172.0.0.41/16
participant 6 600 PORT MAC 172.0.0.51/16
participant 7 700 PORT MAC 172.0.0.61/16
participant 8 800 PORT MAC 172.0.0.71/16
participant 9 900 PORT MAC 172.0.0.81/16

host AS ROUTER _ IP           # host names of form a1_100 a1_110

announce 1 100.0.0.0/24 
announce 2 140.0.0.0/24 
announce 3 140.0.0.0/24 
announce 4 140.0.0.0/24 
announce 5 140.0.0.0/24 
announce 6 140.0.0.0/24 
announce 7 140.0.0.0/24 
announce 8 140.0.0.0/24 
announce 9 140.0.0.0/24 

outflow a1 -t  80 > b
outflow a1 -t  81 > c
outflow a1 -t  82 > d
outflow a1 -t  83 > e
outflow a1 -t  84 > f
outflow a1 -t  85 > g
outflow a1 -t  86 > h
outflow a1 -t  87 > i

listener AUTOGEN 77 80 81 82 83 84 85 86 87

test init {
	listener
}

test regress {
	verify a1_100 b1_140 77
	verify a1_100 b1_140 80
	verify a1_100 c1_140 81
	verify a1_100 d1_140 82
	verify a1_100 e1_140 83
	verify a1_100 f1_140 84
	verify a1_100 g1_140 85
	verify a1_100 h1_140 86
	verify a1_100 i1_140 87
}

test info {
	local ovs-ofctl dump-flows S1
	local ovs-ofctl dump-flows S2
	local ovs-ofctl dump-flows S3
	local ovs-ofctl dump-flows S4
}
