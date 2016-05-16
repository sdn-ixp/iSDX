#!/usr/bin/env bash

cd ~

#  Dependencies for ryu
sudo apt-get install -y python-routes python-dev
# latest version does not allow use of latest oslo.config
sudo pip install oslo.config
sudo pip install msgpack-python
sudo pip install eventlet

#  Ryu install
cd ~
git clone git://github.com/osrg/ryu.git
sudo cat iSDX/setup/ryu-flags.py >>ryu/ryu/flags.py
cd ryu

# get version 3.6. Later might work. Latest does not.
git checkout 4f1a4db7

# Below should be temporary until ryu's pip-requires file is fixed
sed -i "s/python_version < '2.7'/(python_version != '2.7' and python_version != '3.0')/" tools/pip-requires
sed -i "s/python_version >= '2.7'/(python_version == '2.7' or python_version == '3.0')/" tools/pip-requires

sudo python ./setup.py install
