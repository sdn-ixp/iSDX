#!/bin/bash

BASE=~/iSDX
LOG_DIR=regress/regress.$$
echo "Logging to $LOG_DIR"
mkdir -p $LOG_DIR

# if you change EXAMPLES to point elsewhere (like the examples dir unsed iSDX)
#    change the ../../../ ... tnode.py line in multi-table-sdx_mininext.py and multi-switch-sdx_mininext.py 
EXAMPLES=$BASE/test/output
EXAMPLES=$BASE/examples

# set to anything but 0 to run mininext in interactive mode - type control d continue
INTERACTIVE=0

# name of regression test to use by default
RTEST=terse
#number of tests to run
LOOPCOUNT=1

while [[ $# > 1 ]]
do
  key="$1"

  case $key in
  -n|--loopcount)
     LOOPCOUNT="$2"
     shift
     ;;
  -t|--traffic_test_name)
     RTEST="$2"
     shift
     ;;
   -*)
     echo "Usage: $0 -n number_of_loops -t traffic_test_group_name test_name test_name ..." >&2
     exit 1
     ;;
   *)
     break
     ;;
  esac
  shift
done

echo running regression $RTEST

if [ "$#" -lt 1 ] ; then
  echo "Usage: $0 -n number_of_loops -t traffic_test_group_name test_name test_name ..." >&2
  exit 1
fi

for i in $@
do
	if [ ! -e $EXAMPLES/$i ] ; then
        echo $0 ERROR: Test $i is not defined
        exit 1
    fi
done

count=1
while [ $count -le $LOOPCOUNT ]
do
	for TEST in $@
	do

		echo -------------------------------
		echo running test: $TEST:$count
		if [ $INTERACTIVE != '0' ]
		then
			echo "****** RUNNING MININEXT IN INTERACTVE MODE - type control-D at end of test to continue **********"
		fi
		echo -------------------------------
		
		# the cleanup script will kill this each test, so we have to restart it on same file - new version puts each test in its own log
		python $BASE/logServer.py $LOG_DIR/$TEST.$count.log >/dev/null 2>&1 &
		sleep 1
		python $BASE/logmsg.py "running test: $TEST:$count"
		
		echo starting mininext
		
		MINICONFIGDIR=~/mini_rundir
		rm -rf $MINICONFIGDIR
		mkdir -p $MINICONFIGDIR
		cd $EXAMPLES/$TEST/mininext
		find configs | cpio -pdm $MINICONFIGDIR

		M0=/tmp/sdxm0.$$
		mkfifo $M0
		
		SYNC=/tmp/sdxsync.$$
		mkfifo $SYNC
		
		cat <$M0 | ./sdx_mininext.py $MINICONFIGDIR/configs $SYNC &
		M_PID=$!
	
		echo delaying for mininet
		
		cat $SYNC
		echo starting ryu
		ryu-manager $BASE/flanc/refmon.py --refmon-config $EXAMPLES/$TEST/config/sdx_global.cfg >/dev/null 2>&1 &
		sleep 2

		echo starting xctrl
		cd $BASE/xctrl/
		./xctrl.py $EXAMPLES/$TEST/config/sdx_global.cfg

		echo starting arp proxy
		cd $BASE/arproxy/
		python arproxy.py $TEST &
		sleep 3

		echo starting route server
		cd $BASE/xrs/
		python route_server.py $TEST &
		sleep 3

		echo starting participants
		cd $BASE/pctrl/
		while read -r part other
		do
        	if [[ $other == *"participant"* ]]
			then
				part=`echo $part | tr -d :\"`
				echo starting participant $part
				sudo python participant_controller.py $TEST $part &
			fi
		done < $EXAMPLES/$TEST/config/sdx_policies.cfg
		sleep 5

		echo starting exabgp
		exabgp $EXAMPLES/$TEST/config/bgp.conf >/dev/null 2>&1 &
		sleep 10

		echo starting $TEST
		cd $BASE/test
		python tmgr.py $EXAMPLES/$TEST/config/test.cfg "regression $RTEST"
		
		if [ $INTERACTIVE != '0' ]
		then
			echo; echo "************************"
			echo enter mininext commands followed by control-d to exit
			echo; echo "************************"
			while read in
			do
				echo $in 
			done >$M0
		fi

		echo cleaning up processes and files
		sudo killall python
		sudo killall exabgp
		sudo fuser -k 6633/tcp
		python ~/iSDX/pctrl/clean_mongo.py
		sudo rm -f ~/iSDX/xrs/ribs/*.db

		if [ $INTERACTIVE = '0' ]
		then
			echo telling mininext to shutdown
			echo quit >$M0
		fi
		echo waiting for mininext to exit
		wait $M_PID
		rm -f $M0 $SYNC

		echo cleaning up mininext
		sudo mn -c
		echo test done
	
	done
	count=`expr $count + 1`
done
exit
