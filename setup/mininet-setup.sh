#!/usr/bin/env bash

git clone git://github.com/mininet/mininet
pushd mininet
git checkout -b 2.1.0p1 2.1.0p1
./util/install.sh -fn03
popd
