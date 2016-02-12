#!/usr/bin/env bash

while [ "$1" != "" ]; do
    if [ $1 = "--no-mininet" ]; then
	NO_MININET=1
    fi
    shift
done

cd ~

# Install Quagga
sudo apt-get install -y quagga

# Install MiniNExT
# MiniNExT dependencies
sudo apt-get install -y help2man python-setuptools

if [ -z "$NO_MININET" ]; then
    git clone https://github.com/USC-NSL/miniNExT.git miniNExT/
    cd miniNExT
    git checkout 1.4.0
    sudo make install
    cd ~
fi

# Install Requests
sudo pip install requests

# Install SDX
# use existing iSDX that is mounted by Vagrant
#git clone https://github.com/sdn-ixp/iSDX.git
cd iSDX
sudo chmod 755 xrs/client.py xrs/route_server.py
mkdir xrs/ribs
cd ~

# Install ExaBGP
sudo pip install -U exabgp
