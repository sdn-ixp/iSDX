#!/bin/bash

# Script simply copies files needed for torch to the directory shared with
# the docker containers.

if [ $# -ne 2 ]; then
    echo "usage: $0 <base_iSDX_dir> <torch.cfg>"
    exit 1
fi

BASE=$1
TORCH=$2

SHARE='/tmp/share'
mkdir -p $SHARE

cp $BASE/test/{tnode,tlib}.py $SHARE
cp $TORCH $SHARE

