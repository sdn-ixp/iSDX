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

echo running regression $RTEST

if [ "$#" -lt 1 ] ; then
  echo "Usage: $0 -i -p -s -n number_of_loops -t traffic_test_group_name test_name test_name ..." >&2
  echo "    -i is for interactive commands to mininet after running tests" >&2
  echo "    -p is for pause after any errors.  Type return to continue" >&2
  echo "    -s is for stopping after any errors. Can be used with -p" >&2
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
			echo "****** RUNNING MININET IN INTERACTVE MODE - type control-D at end of test to continue **********"
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
		cat <$M0 | ./sdx_mininet.py mininet.cfg $BASE/test/tnode.py $SYNC &
		M_PID=$!
		cat $SYNC
		
		echo starting ryu
		cd $BASE/flanc
		ryu-manager ryu.app.ofctl_rest refmon.py --refmon-config $EXAMPLES/$TEST/config/sdx_global.cfg >/dev/null 2>&1 &
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

		cd $BASE/pctrl/
		while read -r part other
		do
        	if [[ $other == *"participant"* ]]
			then
				part=`echo $part | tr -d :\"`
				echo starting participant $part
				sudo python participant_controller.py $TEST $part &
				sleep 1
			fi
		done < $EXAMPLES/$TEST/config/sdx_policies.cfg
		sleep 5

		echo starting exabgp
		exabgp $EXAMPLES/$TEST/config/bgp.conf >/dev/null 2>&1 &
		sleep 10

		echo starting $TEST
		cd $BASE/test
		python tmgr.py $EXAMPLES/$TEST/config/test.cfg "regression $RTEST"
		
		FAIL=`grep -c FAILED $LOG_DIR/$TEST.$count.log`
		if [ $FAIL = '0' ]
		then
			echo "Test $TEST:$count succeeded.  All tests passed"
			python $BASE/logmsg.py "Test $TEST:$count succeeded.  All tests passed"
		else
			python $BASE/logmsg.py "Test $TEST:$count failed.  Retrying"
			echo TEST FAILED - SLEEPING AND RETRYING
			sleep 3 # 60
			python tmgr.py $EXAMPLES/$TEST/config/test.cfg "regression verbose-retry"
			NFAIL=`grep -c FAILED $LOG_DIR/$TEST.$count.log`
			if [ $NFAIL = $FAIL ]
			then
				echo "Test $TEST:$count succeeded on retry."
				python $BASE/logmsg.py "Test $TEST:$count succeeded on retry."
			fi
			if [ $PAUSEONERROR != '0' ]
			then
				echo "******************************* pausing until carriage return *************************"
				read </dev/tty
			fi
			if [ $STOPONERROR != '0' ]
			then
				count=9999999		# terminates loop
			fi
		fi
		
		if [ $INTERACTIVE != '0' ]
		then
			echo; echo "************************"
			echo enter mininet commands followed by control-d to exit
			echo; echo "************************"
			while read in
			do
				echo $in 
			done >$M0
		fi

		echo cleaning up processes and files
		(
		sudo killall python 
		sudo killall exabgp
		sudo fuser -k 6633/tcp
		python ~/iSDX/pctrl/clean_mongo.py
		sudo rm -f ~/iSDX/xrs/ribs/*.db
		) >/dev/null 2>&1
		
		if [ $INTERACTIVE = '0' ]
		then
			echo telling mininet to shutdown
			echo quit >$M0
		fi
		wait $M_PID
		rm -f $M0 $SYNC

		echo cleaning up mininet
		sudo mn -c >/dev/null 2>&1
		echo test done
	
	done
	count=`expr $count + 1`
done
exit
