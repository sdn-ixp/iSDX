#!/usr/bin/env bash

cd ~
wget http://openvswitch.org/releases/openvswitch-2.0.1.tar.gz
tar xf openvswitch-2.0.1.tar.gz
pushd openvswitch-2.0.1
DEB_BUILD_OPTIONS='parallel=8 nocheck' fakeroot debian/rules binary
popd
sudo dpkg -i openvswitch-common*.deb openvswitch-datapath-dkms*.deb python-openvswitch*.deb openvswitch-pki*.deb openvswitch-switch*.deb
rm -rf *openvswitch*
cd ~
