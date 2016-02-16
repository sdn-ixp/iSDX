
# generate network equivalent to generic test-mt
# 3 participants
# combination of inbound and outbound rules
# additional test for unmatched traffic on port 8888

mode multi-table
participants 3
peers 1 2 3

#participant ID ASN PORT MAC IP PORT MAC IP
participant 1 100 PORT MAC 172.0.0.1
participant 2 200 PORT MAC 172.0.0.11
participant 3 300 PORT MAC 172.0.0.21 PORT MAC 172.0.0.22

# announce (implies ifconfig of loopback interface, :# implies number of interfaces on that address - i.e., :2 -> 100.0.0.1 and 100.0.0.2, default is just .1
announce 1 100.0.0.0/24:2 110.0.0.0/24
announce 2 140.0.0.0/24 150.0.0.0/24
announce 3 140.0.0.0/24 150.0.0.0/24

flow a1 80 >> b
flow a1 4321 >> c
flow a1 4322 >> c
flow c1 << 4321
flow c2 << 4322

# node host interface_name interface_address ports
node b1 i0 140.0.0.1 80 4321 4322 8888
node b1 i1 150.0.0.1 80 4321 4322 8888
node a1 i0 100.0.0.1 80 4321 4322 8888
node a1 i1 110.0.0.1 80 4321 4322 8888
node c1 i0 140.0.0.1 80 4321 4322 8888
node c1 i1 150.0.0.1 80 4321 4322 8888
node c2 i0 140.0.0.1 80 4321 4322 8888
node c2 i1 150.0.0.1 80 4321 4322 8888

# test src_host src_bind_ifc src_port dst_host dst_ifc dst_port
test a1 i0 80 b1 i0 80
test a1 i0 4321 c1 i0 4321
test a1 i0 4322 c2 i0 4322
test a1 i0 8888 c1 i0 8888

