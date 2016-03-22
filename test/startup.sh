#!/bin/bash

BASE=~/iSDX
LOG_DIR=regress/regress.$$
echo "Logging to $LOG_DIR"
mkdir -p $LOG_DIR

EXAMPLES=$BASE/test/output
# for now, tests must run from examples folder
EXAMPLES=$BASE/examples

# set to anything but 0 to run mininet in interactive mode - type control d continue
INTERACTIVE=0
STOPONERROR=0
PAUSEONERROR=0



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
   -i)
     INTERACTIVE=1
     ;;
   -p)
     PAUSEONERROR=1
     ;;
   -s)
     STOPONERROR=1
     ;;
   -*)
     echo "Usage error.  Type just $0 for options" >&2
     exit 1
     ;;
   *)
     break
     ;;
  esac
  shift
done

if [ "$#" -lt 1 ] ; then
  echo "Usage: $0 -i -p -s -n number_of_loops -t traffic_test_group_name test_name test_name ..." >&2
  echo "    -i runs interactive torch commands after tests" >&2
  echo "    -p pauses after any errors.  Implies -i if error" >&2
  echo "    -s is for stopping after any errors. Can be used with -p" >&2
  exit 1
fi

for TEST in $@
do
	if [ ! -e $EXAMPLES/$TEST/config/config.spec ] ; then
        echo $0 ERROR: Test $TEST is not defined
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
			echo "****** RUNNING IN INTERACTVE MODE - type control-D when finished to continue **********"
		fi
		echo -------------------------------
		
		# the cleanup script will kill this each test, so we have to restart it on same file - new version puts each test in its own log
		python $BASE/logServer.py $LOG_DIR/$TEST.$count.log >/dev/null 2>&1 &
		sleep 1
		python $BASE/logmsg.py "running test: $TEST:$count"
		
		echo starting mininet
		
		M0=/tmp/sdxm0.$$
		mkfifo $M0
		
		SYNC=/tmp/sdxsync.$$
		mkfifo $SYNC
		
		rm /var/run/quagga/*
		cd $EXAMPLES/$TEST/mininet
		cat $M0 | python ./sdx_mininet.py mininet.cfg $BASE/test/tnode.py $SYNC &
		M_PID=$!
		cat $SYNC
		
		echo starting ryu
		cd $BASE/flanc
		ryu-manager ryu.app.ofctl_rest refmon.py --refmon-config $EXAMPLES/$TEST/config/sdx_global.cfg >/dev/null 2>&1 &
		#sleep 2

		echo starting xctrl
		cd $BASE/xctrl/
		python ./xctrl.py $EXAMPLES/$TEST/config/sdx_global.cfg

		echo starting arp proxy
		cd $BASE/arproxy/
		python arproxy.py $TEST &
		#sleep 3

		echo starting route server
		cd $BASE/xrs/
		python route_server.py $TEST &
		#sleep 3

		cd $BASE/pctrl/
		while read -r part other
		do
        	if [[ $other == *"participant"* ]]
			then
				part=`echo $part | tr -d :\"`
				echo starting participant $part
				sudo python participant_controller.py $TEST $part &
				#sleep 1
			fi
		done < $EXAMPLES/$TEST/config/sdx_policies.cfg
		sleep 5

		echo starting exabgp
		exabgp $EXAMPLES/$TEST/config/bgp.conf >/dev/null 2>&1 &
		sleep 5

		echo starting $TEST
		cd $BASE/test
		python tmgr.py $EXAMPLES/$TEST/config/config.spec "test init regress"
		
		FAIL=`grep -c FAILED $LOG_DIR/$TEST.$count.log`
		if [ $FAIL = '0' ]
		then
			echo "Test $TEST:$count succeeded.  All tests passed"
			python $BASE/logmsg.py "Test $TEST:$count succeeded.  All tests passed"
		else
			if [ $PAUSEONERROR != '0' ]
			then
				echo; echo "************ ERROR OCCCURED - PAUSING ************"
				echo enter TORCH commands followed by control-d to exit
				echo; echo "**************************************************"
				python tmgr.py $EXAMPLES/$TEST/config/config.spec
			fi
			if [ $STOPONERROR != '0' ]
			then
				count=9999999		# terminates loop
			fi
		fi
		
		if [ $INTERACTIVE != '0' ]
		then
			echo; echo "************************"
			echo enter TORCH commands followed by control-d to exit
			echo; echo "************************"
			python tmgr.py $EXAMPLES/$TEST/config/config.spec
		fi

		echo cleaning up processes and files
		(
		sudo killall python /usr/bin/python /usr/lib/quagga/bgpd /usr/lib/quagga/zebra
		sudo killall exabgp
		sudo fuser -k 6633/tcp
		python ~/iSDX/pctrl/clean_mongo.py
		sudo rm -f ~/iSDX/xrs/ribs/*.db
		) >/dev/null 2>&1
		
		echo telling mininet to shutdown
		echo quit >$M0

		wait $M_PID
		rm -f $M0 $SYNC

		echo cleaning up mininet
		sudo mn -c >/dev/null 2>&1
		echo test done
	
	done
	count=`expr $count + 1`
done
exit
