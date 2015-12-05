#!/usr/bin/env bash

cd ~

#  Dependencies for ryu
sudo apt-get install -y python-routes python-dev
sudo pip install oslo.config --upgrade
sudo pip install msgpack-python
sudo pip install eventlet

#  Ryu install
cd ~
git clone git://github.com/osrg/ryu.git
sudo cp iSDX/setup/ryu-flags.py ryu/ryu/flags.py
cd ryu
sudo python ./setup.py install
