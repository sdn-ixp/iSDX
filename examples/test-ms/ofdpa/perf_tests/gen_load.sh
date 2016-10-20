#!/bin/bash

# Generate flows to fill the flow table of the switch

if [ $# -ne 1 ]; then
    echo "usage: $0 <nflows>"
    exit 1
fi

NFLOWS=$1

echo BURST: 1450218588.0
echo PARTICIPANT: 0

# loop: insert a bunch, then remove them
for j in {1..3}; do

    for i in $(seq 256 $((NFLOWS+256))); do
	#DST=`printf "%02x" $(((i+1) % 256))`
	DST=`printf "%02x" $((($RANDOM+1) % 256))`
	SRC=`printf "%02x" $(((i+2) % 255))`
    
	echo {\"rule_type\": \"main\", \"mod_type\": \"insert\", \"priority\": 2, \"cookie\": [$i, 65535], \"action\": {\"fwd\": [\"inbound\"], \"set_eth_dst\": \"80:00:00:00:00:$DST\"}, \"match\": {\"eth_src\": \"08:00:27:89:3b:$SRC\", \"eth_dst\": [\"$DST:00:00:00:00:00\", \"ff:00:00:00:00:00\"], \"tcp_dst\": $((i+4000))}}
    done

    # insert one that won't be removed
    echo {\"rule_type\": \"main\", \"mod_type\": \"insert\", \"priority\": 2, \"cookie\": [1024, 65535], \"action\": {\"fwd\": [\"inbound\"], \"set_eth_dst\": \"80:00:00:00:00:aa\"}, \"match\": {\"eth_src\": \"08:00:27:89:3b:bb\", \"eth_dst\": [\"aa:00:00:00:00:00\", \"ff:00:00:00:00:00\"], \"tcp_dst\": $((4000+$j))}}
    
    # Remove all rules
    # echo {\"rule_type\": \"outbound\", \"mod_type\": \"remove\", \"cookie\": [0, 0]}
    
    # Remove rules with bit mask 0x100
    echo {\"rule_type\": \"main\", \"mod_type\": \"remove\", \"cookie\": [256, 256]}

done

echo


