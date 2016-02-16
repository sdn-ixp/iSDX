
# generate slightly more complex case than test-ms
# 5 participants
# extra flows from a second sourcing node
# be careful if specifying duplicate advertised routes from both sources (100.0.0.1)
# as there are no return path rules


mode multi-switch
participants 5
peers 1 2 3 4 5

#participant ID ASN PORT MAC IP PORT MAC IP
participant 1 100 PORT MAC 172.0.0.1
participant 2 200 PORT MAC 172.0.0.11
participant 3 300 PORT MAC 172.0.0.21
participant 4 400 PORT MAC 172.0.0.31 PORT MAC 172.0.0.32
participant 5 500 PORT MAC 172.0.0.41

# announce (implies ifconfig of loopback interface, :# implies number of interfaces on that address - i.e., :2 -> 100.0.0.1 and 100.0.0.2, default is just .1
announce 1 100.0.0.0/24 
announce 2 110.0.0.0/24
announce 3 140.0.0.0/24 150.0.0.0/24
announce 4 140.0.0.0/24 150.0.0.0/24
announce 5 140.0.0.0/24 150.0.0.0/24

flow a1 80 >> c
flow a1 4321 >> d
flow a1 4322 >> d
flow d1 << 4321
flow d2 << 4322
flow b1 80 >> e
flow b1 4321 >> e
flow b1 4322 >> e

# node host interface_name interface_address ports
node a1 i0 100.0.0.1 80 4321 4322 8888
node b1 i0 110.0.0.1 80 4321 4322 8888
node c1 i0 140.0.0.1 80 4321 4322 8888
node c1 i1 150.0.0.1 80 4321 4322 8888
node d1 i0 140.0.0.1 80 4321 4322 8888
node d1 i1 150.0.0.1 80 4321 4322 8888
node d2 i0 140.0.0.1 80 4321 4322 8888
node d2 i1 150.0.0.1 80 4321 4322 8888
node e1 i0 140.0.0.1 80 4321 4322 8888
node e1 i1 150.0.0.1 80 4321 4322 8888

# test src_host src_bind_ifc src_port dst_host dst_ifc dst_port
test a1 i0 80 c1 i0 80
test a1 i0 4321 d1 i0 4321
test a1 i0 4322 d2 i0 4322
test a1 i0 8888 c1 i0 8888

test b1 i0 80 e1 i0 80
test b1 i0 4321 e1 i0 4321
test b1 i0 4322 e1 i0 4322
test b1 i0 8888 c1 i0 8888