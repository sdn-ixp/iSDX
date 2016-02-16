
# test inbound rules
# 2 participants - receiver has multiple router connections

mode multi-switch
participants 2
peers 1 2

#participant ID ASN PORT MAC IP PORT MAC IP
participant 1 100 PORT MAC 172.0.0.1 
participant 2 200 PORT MAC 172.0.0.11 PORT MAC 172.0.0.12 PORT MAC 172.0.0.13 PORT MAC 172.0.0.14 PORT MAC 172.0.0.15 PORT MAC 172.0.0.16 PORT MAC 172.0.0.17 PORT MAC 172.0.0.18 PORT MAC 172.0.0.19

# announce (implies ifconfig of loopback interface, :# implies number of interfaces on that address - i.e., :2 -> 100.0.0.1 and 100.0.0.2, default is just .1
announce 1 100.0.0.0/24 
announce 2 140.0.0.0/24 

flow b1 << 80
flow b2 << 81
flow b3 << 82
flow b4 << 83
flow b5 << 84
flow b6 << 85
flow b7 << 86
flow b8 << 87
flow b9 << 88

# node host interface_name interface_address ports

node a1 i0 100.0.0.1 77 80 81 82 83 84 85 86 87 88
node b1 i0 140.0.0.1 77 80 81 82 83 84 85 86 87 88
node b2 i0 140.0.0.1 77 80 81 82 83 84 85 86 87 88
node b3 i0 140.0.0.1 77 80 81 82 83 84 85 86 87 88
node b4 i0 140.0.0.1 77 80 81 82 83 84 85 86 87 88
node b5 i0 140.0.0.1 77 80 81 82 83 84 85 86 87 88
node b6 i0 140.0.0.1 77 80 81 82 83 84 85 86 87 88
node b7 i0 140.0.0.1 77 80 81 82 83 84 85 86 87 88
node b8 i0 140.0.0.1 77 80 81 82 83 84 85 86 87 88
node b9 i0 140.0.0.1 77 80 81 82 83 84 85 86 87 88


# test src_host src_bind_ifc src_port dst_host dst_ifc dst_port
test a1 i0 77 b1 i0 77
test a1 i0 80 b1 i0 80
test a1 i0 81 b2 i0 81
test a1 i0 82 b3 i0 82
test a1 i0 83 b4 i0 83
test a1 i0 84 b5 i0 84
test a1 i0 85 b6 i0 85
test a1 i0 86 b7 i0 86
test a1 i0 87 b8 i0 87
test a1 i0 88 b9 i0 88

