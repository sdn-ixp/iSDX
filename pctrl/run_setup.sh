#!/bin/sh

EXPERIMENT_NAME='demo2'
NUMBER_OF_PARTICIPANTS=1
INSTALL_ROOT='/home/glex/sdx-parallel'
EXAMPLE_NAME='test-amsix'
UPDATE_FILE='updates.20150802.0000.txt'
FRAC=0.2

# Generate Policies & Copy asn json files

cd $INSTALL_ROOT/examples/$EXAMPLE_NAME; python generate_configs.py $FRAC ; cp $INSTALL_ROOT/examples/$EXAMPLE_NAME/asn_2_* $INSTALL_ROOT/pctrl

# Clean DB & Initialize the rib

sh clean.sh

# Start the reflog
`cd $INSTALL_ROOT/flanc ; nohup ./reflog.py localhost 5555 sdx logger.txt > /dev/null 2>&1 &`
# Start Route Server
`cd $INSTALL_ROOT/xrs ; nohup python route_server.py $EXAMPLE_NAME > /dev/null 2>&1 &`

# Start Participant controller
for i in `seq 1 $NUMBER_OF_PARTICIPANTS`
do
	python participant_controller.py $EXAMPLE_NAME $i $EXPERIMENT_NAME > /dev/null 2>&1 &
done

`cd $INSTALL_ROOT/xbgp ; nohup ./xbgp.py localhost 6000 xrs $UPDATE_FILE > /dev/null 2>&1 &` 

while [ `ps axf | grep xbgp | grep -v grep | wc -l` -ne 0 ] 
do 
	echo "running"
done

`ps axf | grep participant_controller | grep -v grep | awk '{print "kill -SIGINT " $1}' | { while IFS= read -r cmd; do  $cmd; done }`

echo "completed"
