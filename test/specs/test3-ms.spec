
# test multiple peering relationships
# 4 independent networks, each the same as the test-ms case

mode multi-switch
participants 12

peers 1 2 3
peers 4 5 6
peers 7 8 9
peers 10 11 12

#participant ID ASN PORT MAC IP PORT MAC IP
participant 1 100 PORT MAC 172.0.0.1
participant 2 200 PORT MAC 172.0.0.11
participant 3 300 PORT MAC 172.0.0.21 PORT MAC 172.0.0.22
participant 4 400 PORT MAC 172.0.0.31
participant 5 500 PORT MAC 172.0.0.41
participant 6 600 PORT MAC 172.0.0.51 PORT MAC 172.0.0.52
participant 7 400 PORT MAC 172.0.0.61
participant 8 500 PORT MAC 172.0.0.71
participant 9 600 PORT MAC 172.0.0.81 PORT MAC 172.0.0.82
participant 10 400 PORT MAC 172.0.0.91
participant 11 500 PORT MAC 172.0.0.101
participant 12 600 PORT MAC 172.0.0.111 PORT MAC 172.0.0.112

# announce (implies ifconfig of loopback interface, :# implies number of interfaces on that address - i.e., :2 -> 100.0.0.1 and 100.0.0.2, default is just .1
announce 1 100.0.0.0/24 110.0.0.0/24
announce 2 140.0.0.0/24 150.0.0.0/24
announce 3 140.0.0.0/24 150.0.0.0/24
announce 4 100.0.0.0/24 110.0.0.0/24
announce 5 140.0.0.0/24 150.0.0.0/24
announce 6 140.0.0.0/24 150.0.0.0/24
announce 7 100.0.0.0/24 110.0.0.0/24
announce 8 140.0.0.0/24 150.0.0.0/24
announce 9 140.0.0.0/24 150.0.0.0/24
announce 10 100.0.0.0/24 110.0.0.0/24
announce 11 140.0.0.0/24 150.0.0.0/24
announce 12 140.0.0.0/24 150.0.0.0/24

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

# node host interface_name interface_address ports
node a1 i0 100.0.0.1 80 4321 4322 8888
node a1 i1 110.0.0.1 80 4321 4322 8888

node b1 i0 140.0.0.1 80 4321 4322 8888
node b1 i1 150.0.0.1 80 4321 4322 8888

node c1 i0 140.0.0.1 80 4321 4322 8888
node c1 i1 150.0.0.1 80 4321 4322 8888
node c2 i0 140.0.0.1 80 4321 4322 8888
node c2 i1 150.0.0.1 80 4321 4322 8888


node d1 i0 100.0.0.1 80 4321 4322 8888
node d1 i1 110.0.0.1 80 4321 4322 8888

node e1 i0 140.0.0.1 80 4321 4322 8888
node e1 i1 150.0.0.1 80 4321 4322 8888

node f1 i0 140.0.0.1 80 4321 4322 8888
node f1 i1 150.0.0.1 80 4321 4322 8888
node f2 i0 140.0.0.1 80 4321 4322 8888
node f2 i1 150.0.0.1 80 4321 4322 8888


node g1 i0 100.0.0.1 80 4321 4322 8888
node g1 i1 110.0.0.1 80 4321 4322 8888

node h1 i0 140.0.0.1 80 4321 4322 8888
node h1 i1 150.0.0.1 80 4321 4322 8888

node i1 i0 140.0.0.1 80 4321 4322 8888
node i1 i1 150.0.0.1 80 4321 4322 8888
node i2 i0 140.0.0.1 80 4321 4322 8888
node i2 i1 150.0.0.1 80 4321 4322 8888


node j1 i0 100.0.0.1 80 4321 4322 8888
node j1 i1 110.0.0.1 80 4321 4322 8888

node k1 i0 140.0.0.1 80 4321 4322 8888
node k1 i1 150.0.0.1 80 4321 4322 8888

node l1 i0 140.0.0.1 80 4321 4322 8888
node l1 i1 150.0.0.1 80 4321 4322 8888
node l2 i0 140.0.0.1 80 4321 4322 8888
node l2 i1 150.0.0.1 80 4321 4322 8888

# test src_host src_bind_ifc src_port dst_host dst_ifc dst_port
test a1 i0 80 b1 i0 80
test a1 i0 4321 c1 i0 4321
test a1 i0 4322 c2 i0 4322
test a1 i0 8888 c1 i0 8888

test d1 i0 80 e1 i0 80
test d1 i0 4321 f1 i0 4321
test d1 i0 4322 f2 i0 4322
test d1 i0 8888 f1 i0 8888

test g1 i0 80 h1 i0 80
test g1 i0 4321 i1 i0 4321
test g1 i0 4322 i2 i0 4322
test g1 i0 8888 i1 i0 8888

test j1 i0 80 k1 i0 80
test j1 i0 4321 l1 i0 4321
test j1 i0 4322 l2 i0 4322
test j1 i0 8888 l1 i0 8888