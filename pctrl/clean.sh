sudo mn -c
sudo rm ~/sdx-ryu/xrs/ribs/172.0.0.*
sudo killall python
sudo killall exabgp
sudo fuser -k 6633/tcp
python clean_cqlsh.py
python initialize_ribs.py
