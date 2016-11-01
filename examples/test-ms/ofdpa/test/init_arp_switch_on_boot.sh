#!/bin/bash

sed -i '/^exit/d' /etc/rc.local

cat <<EOF  >> /etc/rc.local

sleep 1 #doesn't work without this
`pwd`/init_arp_switch.sh

exit 0
EOF
