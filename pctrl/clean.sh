sudo mn -c
sudo rm ~/iSDX/xrs/ribs/172.0.0.*
sudo killall python
sudo killall exabgp
sudo fuser -k 6633/tcp
