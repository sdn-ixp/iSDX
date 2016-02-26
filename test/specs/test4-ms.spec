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

flow a1 80 >> b
flow a1 81 >> c
flow a1 82 >> d
flow a1 83 >> e
flow a1 84 >> f
flow a1 85 >> g
flow a1 86 >> h
flow a1 87 >> i

node AUTOGEN 77 80 81 82 83 84 85 86 87

test a1_100 c1_140 77
test a1_100 b1_140 80
test a1_100 c1_140 81
test a1_100 d1_140 82
test a1_100 e1_140 83
test a1_100 f1_140 84
test a1_100 g1_140 85
test a1_100 h1_140 86
test a1_100 i1_140 87

