#!/usr/bin/env bash

cd ~

# Install Quagga 
sudo apt-get install -y quagga

# Install MiniNExT
# MiniNExT dependencies
sudo apt-get install -y help2man python-setuptools

git clone https://github.com/USC-NSL/miniNExT.git miniNExT/  
cd miniNExT  
git checkout 1.4.0  
sudo make install

# Install Requests
sudo pip install requests

# Install SDX
cd ~
git clone https://github.com/sdn-ixp/sdx-ryu.git
sudo chmod 755 ~/sdx-ryu/xrs/client.py ~/sdx-ryu/xrs/route_server.py ~/sdx-ryu/examples/simple/mininet/sdx_mininext.py
mkdir ~/sdx-ryu/xrs/ribs

# Install ExaBGP
sudo pip install -U exabgp
