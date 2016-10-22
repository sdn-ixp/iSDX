mode multi-switch
participants 30
peers  1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30

participant 1 1 PORT MAC 172.0.0.1/16
participant 2 2 PORT MAC 172.0.0.2/16
participant 3 3 PORT MAC 172.0.0.3/16
participant 4 4 PORT MAC 172.0.0.4/16
participant 5 5 PORT MAC 172.0.0.5/16
participant 6 6 PORT MAC 172.0.0.6/16
participant 7 7 PORT MAC 172.0.0.7/16
participant 8 8 PORT MAC 172.0.0.8/16
participant 9 9 PORT MAC 172.0.0.9/16
participant 10 10 PORT MAC 172.0.0.10/16
participant 11 11 PORT MAC 172.0.0.11/16
participant 12 12 PORT MAC 172.0.0.12/16
participant 13 13 PORT MAC 172.0.0.13/16
participant 14 14 PORT MAC 172.0.0.14/16
participant 15 15 PORT MAC 172.0.0.15/16
participant 16 16 PORT MAC 172.0.0.16/16
participant 17 17 PORT MAC 172.0.0.17/16
participant 18 18 PORT MAC 172.0.0.18/16
participant 19 19 PORT MAC 172.0.0.19/16
participant 20 20 PORT MAC 172.0.0.20/16
participant 21 21 PORT MAC 172.0.0.21/16
participant 22 22 PORT MAC 172.0.0.22/16
participant 23 23 PORT MAC 172.0.0.23/16
participant 24 24 PORT MAC 172.0.0.24/16
participant 25 25 PORT MAC 172.0.0.25/16
participant 26 26 PORT MAC 172.0.0.26/16
participant 27 27 PORT MAC 172.0.0.27/16
participant 28 28 PORT MAC 172.0.0.28/16
participant 29 29 PORT MAC 172.0.0.29/16
participant 30 30 PORT MAC 172.0.0.30/16

host AS ROUTER _ IP           # testnode names of form a1_100 a1_110

announce 1 100.0.0.0/24
announce 2 140.0.0.0/24
announce 3 140.0.0.0/24
announce 4 140.0.0.0/24
announce 5 140.0.0.0/24
announce 6 140.0.0.0/24
announce 7 140.0.0.0/24
announce 8 140.0.0.0/24
announce 9 140.0.0.0/24
announce 10 140.0.0.0/24
announce 11 140.0.0.0/24
announce 12 140.0.0.0/24
announce 13 140.0.0.0/24
announce 14 140.0.0.0/24
announce 15 140.0.0.0/24
announce 16 140.0.0.0/24
announce 17 140.0.0.0/24
announce 18 140.0.0.0/24
announce 19 140.0.0.0/24
announce 20 140.0.0.0/24
announce 21 140.0.0.0/24
announce 22 140.0.0.0/24
announce 23 140.0.0.0/24
announce 24 140.0.0.0/24
announce 25 140.0.0.0/24
announce 26 140.0.0.0/24
announce 27 140.0.0.0/24
announce 28 140.0.0.0/24
announce 29 140.0.0.0/24
announce 30 140.0.0.0/24

flow a1 80 >> b
flow a1 81 >> c
flow a1 82 >> d
flow a1 83 >> e
flow a1 84 >> f
flow a1 85 >> g
flow a1 86 >> h
flow a1 87 >> i
flow a1 88 >> j
flow a1 89 >> k
flow a1 90 >> l
flow a1 91 >> m
flow a1 92 >> n
flow a1 93 >> o
flow a1 94 >> p
flow a1 95 >> q
flow a1 96 >> r
flow a1 97 >> s
flow a1 98 >> t
flow a1 99 >> u
flow a1 100 >> v
flow a1 101 >> w
flow a1 102 >> x
flow a1 103 >> y
flow a1 104 >> z
flow a1 105 >> aa
flow a1 106 >> ab
flow a1 107 >> ac
flow a1 108 >> ad

listener AUTOGEN  80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108

test regress {
	exec a1 arp
	test xfer
	exec a1 arp
}

test init {
	listener
}

test xfer {
	verify a1_100 b1_140 80
	verify a1_100 c1_140 81
	verify a1_100 d1_140 82
	verify a1_100 e1_140 83
	verify a1_100 f1_140 84
	verify a1_100 g1_140 85
	verify a1_100 h1_140 86
	verify a1_100 i1_140 87
	verify a1_100 j1_140 88
	verify a1_100 k1_140 89
	verify a1_100 l1_140 90
	verify a1_100 m1_140 91
	verify a1_100 n1_140 92
	verify a1_100 o1_140 93
	verify a1_100 p1_140 94
	verify a1_100 q1_140 95
	verify a1_100 r1_140 96
	verify a1_100 s1_140 97
	verify a1_100 t1_140 98
	verify a1_100 u1_140 99
	verify a1_100 v1_140 100
	verify a1_100 w1_140 101
	verify a1_100 x1_140 102
	verify a1_100 y1_140 103
	verify a1_100 z1_140 104
	verify a1_100 aa1_140 105
	verify a1_100 ab1_140 106
	verify a1_100 ac1_140 107
	verify a1_100 ad1_140 108
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
}

test flush {
	exec a1 ip -s -s neigh flush all
	exec b1 ip -s -s neigh flush all
}
