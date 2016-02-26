# generate network equivalent to generic test-mt
# 3 participants
# combination of inbound and outbound rules
# additional test for unmatched traffic on port 8888

mode multi-table
participants 3
peers 1 2 3

participant 1 100 PORT MAC 172.0.0.1/16
participant 2 200 PORT MAC 172.0.0.11/16
participant 3 300 PORT MAC 172.0.0.21/16 PORT MAC 172.0.0.22/16

host AS ROUTER _ IP           # testnode names of form a1_100 a1_110

announce 1 100.0.0.0/24 110.0.0.0/24
announce 2 140.0.0.0/24 150.0.0.0/24
announce 3 140.0.0.0/24 150.0.0.0/24

flow a1 80 >> b
flow a1 4321 >> c
flow a1 4322 >> c
flow c1 << 4321
flow c2 << 4322

node AUTOGEN 80 4321 4322 8888

# test src_host dst_host dst_port
# binding addresses are taken from the corresponding node definition
# destination is an expected destination
test a1_100 b1_140 80
test a1_100 c1_140 4321
test a1_100 c2_140 4322
test a1_100 c1_140 8888