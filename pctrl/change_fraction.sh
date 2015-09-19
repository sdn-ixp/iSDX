#!/bin/sh

EXPERIMENT_NAME='change_frac'
NUMBER_OF_PARTICIPANTS=1
INSTALL_ROOT='/home/glex/sdx-parallel'
EXAMPLE_NAME='test-largeIX'
UPDATE_FILE='updates.txt'
ITERATIONS=5
FRAC=(0.2 0.4 0.6 0.8 1.0)
RATE=5
MODE=0


cd $INSTALL_ROOT/examples/$EXAMPLE_NAME; python generate_configs.py ; cp $INSTALL_ROOT/examples/$EXAMPLE_NAME/asn_2_* $INSTALL_ROOT/pctrl

for iter in `seq 1 $ITERATIONS`
do
	echo "#### Running for Iteration $iter ####"
	for fraction in "${FRAC[@]}"
	do

		# Generate Policies & Copy asn json files
		echo "Generating policies for $fraction"
		cd $INSTALL_ROOT/examples/$EXAMPLE_NAME; python generate_policies.py $fraction
		# Clean DB & Initialize the rib
		echo "Cleaning MongoDB & Initializing Participant Rib"
		cd $INSTALL_ROOT/pctrl ; . clean.sh

		# Start the reflog
		echo "Starting Reflog..."
		`cd $INSTALL_ROOT/flanc ; nohup ./reflog.py localhost 5555 sdx logger.txt > /dev/null 2>&1 &`
		# Start Route Server
		echo "Starting RouteServer..."
		`cd $INSTALL_ROOT/xrs ; nohup python route_server.py $EXAMPLE_NAME > /dev/null 2>&1 &`

		# Start Participant controller
		OUTPUT_FILE_NAME=$EXPERIMENT_NAME"_FRAC"$fraction"_ITER"$iter
		for i in `seq 1 $NUMBER_OF_PARTICIPANTS`
		do
			echo "Starting Participant $i Controller..."
			cd $INSTALL_ROOT/pctrl ; python participant_controller.py $EXAMPLE_NAME $i $OUTPUT_FILE_NAME > /dev/null 2>&1 &
		done

		#Starting XBGP	
		echo "Starting XBGP..."
		`cd $INSTALL_ROOT/xbgp ; nohup ./xbgp.py localhost 6000 xrs $UPDATE_FILE $RATE $MODE > /dev/null 2>&1 &` 

		while [ `ps axf | grep xbgp | grep -v grep | wc -l` -ne 0 ] 
		do 
			echo "running"
			sleep 1m
		done

		`ps axf | grep participant_controller | grep -v grep | awk '{print "kill -SIGINT " $1}' | { while IFS= read -r cmd; do  $cmd; done }`
		sleep 30
		echo "completed for $fraction"
	done
done
