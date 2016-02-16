mode multi-switch
participants 3
peers 1 2 3

participant 1 100 PORT MAC 172.0.0.10
participant 2 200 PORT MAC 172.0.0.20
participant 3 300 PORT MAC 172.0.0.30

announce 1 110.0.0.0/24 140.0.0.0/24 150.0.0.0/24
announce 2 120.0.0.0/24 150.0.0.0/24 160.0.0.0/24
announce 3 130.0.0.0/24 160.0.0.0/24 140.0.0.0/24

flow a1 80 >> b
flow b1 80 >> c
flow c1 80 >> a
flow a1 81 >> c
flow b1 81 >> a
flow c1 81 >> b

node a1 i110 110.0.0.1 80 81 88
node a1 i140 140.0.0.1 80 81 88
node a1 i150 150.0.0.1 80 81 88

node b1 i120 120.0.0.1 80 81 88
node b1 i150 150.0.0.1 80 81 88
node b1 i160 160.0.0.1 80 81 88

node c1 i130 130.0.0.1 80 81 88
node c1 i160 160.0.0.1 80 81 88
node c1 i140 140.0.0.1 80 81 88

test a1 i110 80 b1 i160 80
test b1 i120 80 c1 i140 80
test c1 i130 80 a1 i150 80

test a1 i110 81 c1 i160 81
test b1 i120 81 a1 i140 81
test c1 i130 81 b1 i150 81

test a1 i110 88 b1 i160 88
test b1 i120 88 c1 i140 88
test c1 i130 88 a1 i150 88