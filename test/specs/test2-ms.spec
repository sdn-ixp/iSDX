# generate slightly more complex case than test-ms
# 5 participants
# extra flows from a second sourcing node
# be careful if specifying duplicate advertised routes from both sources (100.0.0.1)
# as there are no return path rules

mode multi-switch
participants 5
peers 1 2 3 4 5

#participant ID ASN PORT MAC IP PORT MAC IP
participant 1 100 PORT MAC 172.0.0.1/16
participant 2 200 PORT MAC 172.0.0.11/16
participant 3 300 PORT MAC 172.0.0.21/16
participant 4 400 PORT MAC 172.0.0.31/16 PORT MAC 172.0.0.32/16
participant 5 500 PORT MAC 172.0.0.41/16

host AS ROUTER _ IP           # testnode names of form a1_100 a1_110

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
flow b1 4321 >> d
flow b1 4322 >> d

node AUTOGEN 80 4321 4322 8888

# test src_host src_bind_ifc src_port dst_host dst_ifc dst_port
test a1_100 c1_140 80
test a1_100 d1_140 4321
test a1_100 d2_140 4322
test a1_100 c1_140 8888

test b1_110 e1_140 80
test b1_110 d1_140 4321
test b1_110 d2_140 4322
test b1_110 c1_140 8888