BASE=~/iSDX
LOG_FILE=SDXRegression.log.$$

# set to anything but 0 to run mininext in interactive mode - type control d continue
INTERACTIVE=0

if [ "$#" -lt 2 ] ; then
  echo "Usage: $0 number_of_loops test_name test_name ..." >&2
  exit 1
fi

LOOPCOUNT=$1
shift

for i in $@
do
	if [ ! -e $BASE/examples/$i ] ; then
        echo $0 ERROR: Test $i is not defined
        exit 1
    fi
done

rm -f $LOG_FILE

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
		
		# the cleanup script will kill this each test, so we have to restart it on same file
		python $BASE/logServer.py $LOG_FILE >/dev/null 2>&1 &
		sleep 1
		python $BASE/logmsg.py "running test: $TEST:$count"
		
		echo starting mininext
		
		MINICONFIGDIR=~/mini_rundir
		rm -rf $MINICONFIGDIR
		mkdir -p $MINICONFIGDIR
		cd $BASE/examples/$TEST/mininext
		find configs | cpio -pdm $MINICONFIGDIR

		M0=/tmp/sdxm0.$$
		mkfifo $M0
		cat <$M0 | ./sdx_mininext.py $MINICONFIGDIR/configs &
		M_PID=$!
	
		echo delaying for mininet
		sleep 15
		echo starting ryu
		ryu-manager $BASE/flanc/refmon.py --refmon-config $BASE/examples/$TEST/config/sdx_global.cfg >/dev/null 2>&1 &
		sleep 2

		echo starting xctrl
		cd $BASE/xctrl/
		./xctrl.py $BASE/examples/$TEST/config/sdx_global.cfg

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
		sh run_pctrlr.sh $TEST &
		sleep 3

		echo starting exabgp
		exabgp $BASE/examples/$TEST/config/bgp.conf >/dev/null 2>&1 &
		sleep 5

		echo starting $TEST
		cd $BASE/test
		python tmgr.py $BASE/examples/$TEST/config/test.cfg "regression terse"
		
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
		rm -f $M0

		echo cleaning up mininext
		sudo mn -c
		echo test done
	
	done
	count=`expr $count + 1`
done
exit
