#!/bin/sh

EXPERIMENT_NAME='change_rate'
NUMBER_OF_PARTICIPANTS=1
INSTALL_ROOT='/home/ubuntu/sdx-parallel'
EXAMPLE_NAME='test-largeIX'
UPDATE_FILE='updates.txt'
ITERATIONS=5
RATE=(20 40 60 80 100)
FRAC=0.2
MODE=1

cd $INSTALL_ROOT/examples/$EXAMPLE_NAME; python generate_configs.py ; cp $INSTALL_ROOT/examples/$EXAMPLE_NAME/asn_2_* $INSTALL_ROOT/pctrl

for iter in `seq 1 $ITERATIONS`
do
	echo "#### Running for Iteration $iter ####"
	for rate in "${RATE[@]}"
	do
		echo "Running XBGP for $rate"

		# Generate Policies & Copy asn json files
		echo "Generating policies for $FRAC"
		cd $INSTALL_ROOT/examples/$EXAMPLE_NAME; python generate_policies.py $FRAC		

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
		OUTPUT_FILE_NAME=$EXPERIMENT_NAME"_RATE"$rate"_ITER"$iter
		for i in `seq 1 $NUMBER_OF_PARTICIPANTS`
		do
			echo "Starting Participant $i Controller..."
			cd $INSTALL_ROOT/pctrl ; python participant_controller.py $EXAMPLE_NAME $i $OUTPUT_FILE_NAME > /dev/null 2>&1 &
		done

		#Starting XBGP	
		echo "Starting XBGP..."
		`cd $INSTALL_ROOT/xbgp ; nohup ./xbgp.py localhost 6000 xrs $UPDATE_FILE $rate $MODE > /dev/null 2>&1 &` 

		while [ `ps axf | grep xbgp | grep -v grep | wc -l` -ne 0 ] 
		do 
			echo "XBGP still running"
			sleep 1m
		done

		`ps axf | grep participant_controller | grep -v grep | awk '{print "kill -SIGINT " $1}' | { while IFS= read -r cmd; do  $cmd; done }`
		sleep 30
		echo "completed for $rate"
	done
done
