
# test outbound rules
# 1 source, many receivers


mode multi-switch
participants 9
peers 1 2 3 4 5 6 7 8 9

#participant ID ASN PORT MAC IP PORT MAC IP
participant 1 100 PORT MAC 172.0.0.1
participant 2 200 PORT MAC 172.0.0.11
participant 3 300 PORT MAC 172.0.0.21
participant 4 400 PORT MAC 172.0.0.31
participant 5 500 PORT MAC 172.0.0.41
participant 6 600 PORT MAC 172.0.0.51
participant 7 700 PORT MAC 172.0.0.61
participant 8 800 PORT MAC 172.0.0.71
participant 9 900 PORT MAC 172.0.0.81

# announce (implies ifconfig of loopback interface, :# implies number of interfaces on that address - i.e., :2 -> 100.0.0.1 and 100.0.0.2, default is just .1
announce 1 100.0.0.0/24 
announce 2 140.0.0.0/24 
announce 3 140.0.0.0/24 
announce 4 140.0.0.0/24 
announce 5 140.0.0.0/24 
announce 6 140.0.0.0/24 
announce 7 140.0.0.0/24 
announce 8 140.0.0.0/24 
announce 9 140.0.0.0/24 


flow a1 80 >> b
flow a1 81 >> c
flow a1 82 >> d
flow a1 83 >> e
flow a1 84 >> f
flow a1 85 >> g
flow a1 86 >> h
flow a1 87 >> i

# node host interface_name interface_address ports

node a1 i0 100.0.0.1 77 80 81 82 83 84 85 86 87
node b1 i0 140.0.0.1 77 80 81 82 83 84 85 86 87
node c1 i0 140.0.0.1 77 80 81 82 83 84 85 86 87
node d1 i0 140.0.0.1 77 80 81 82 83 84 85 86 87
node e1 i0 140.0.0.1 77 80 81 82 83 84 85 86 87
node f1 i0 140.0.0.1 77 80 81 82 83 84 85 86 87
node g1 i0 140.0.0.1 77 80 81 82 83 84 85 86 87
node h1 i0 140.0.0.1 77 80 81 82 83 84 85 86 87
node i1 i0 140.0.0.1 77 80 81 82 83 84 85 86 87

# test src_host src_bind_ifc src_port dst_host dst_ifc dst_port
test a1 i0 77 c1 i0 77
test a1 i0 80 b1 i0 80
test a1 i0 81 c1 i0 81
test a1 i0 82 d1 i0 82
test a1 i0 83 e1 i0 83
test a1 i0 84 f1 i0 84
test a1 i0 85 g1 i0 85
test a1 i0 86 h1 i0 86
test a1 i0 87 i1 i0 87

