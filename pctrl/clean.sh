pgrep -fa mininet > /dev/null && sudo mn -c
sudo rm -f ~/iSDX/xrs/ribs/*.db
sudo killall python
sudo killall exabgp
sudo fuser -k 6633/tcp
python ~/iSDX/pctrl/clean_mongo.py
