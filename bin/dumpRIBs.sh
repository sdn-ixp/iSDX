#!/bin/bash

for rib in 'input' 'local' 'output'; do
    echo RIB: $rib
    for i in {100,200,300}
    do
	echo == AS $i
	mongoexport -db demo -c ${rib}_$i -f as_path,prefix,next_hop
    done
    echo
done
