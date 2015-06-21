#!/usr/bin/env bash

git clone git://github.com/mininet/mininet
pushd mininet
git checkout -b 2.1.0p2 2.1.0p2
./util/install.sh -fn03
popd
