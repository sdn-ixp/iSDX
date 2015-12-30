BASE=~/iSDX
LOG_FILE=SDXRegression.log

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

while [ $LOOPCOUNT -gt 0 ]
do
	for TEST in $@
	do

		echo -------------------------------
		echo running test: $TEST
		echo -------------------------------
		
		# the cleanup script will kill this each test, so we have to restart it on same file
		python $BASE/logServer.py $LOG_FILE >/dev/null 2>&1 &
		
		(
		  echo delaying for mininet
		  sleep 15
		  echo starting ryu
		  ryu-manager $BASE/flanc/refmon.py --refmon-config $BASE/examples/$TEST/config/sdx_global.cfg >/dev/null 2>&1 &
		  echo starting xctrl
		  cd $BASE/xctrl/
		  ./xctrl.py $BASE/examples/$TEST/config/sdx_global.cfg &
		  sleep 3
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
		  python tmgr.py $BASE/examples/$TEST/config/test.cfg l 'r x0 a1 b1 c1 c2' t
		  echo WAITING FOR MININEXT TO TERMINATE
		  
		) &
		
		echo starting mininext
		
		MINICONFIGDIR=~/mini_rundir
		rm -rf $MINICONFIGDIR
		mkdir -p $MINICONFIGDIR
		cd $BASE/examples/$TEST/mininext
		find configs | cpio -pdm $MINICONFIGDIR
		
		
		(sleep 45; echo quit) | ./sdx_mininext.py $MINICONFIGDIR/configs
		echo exiting mininext
		echo cleaning
		cd $BASE/pctrl/
		sh clean.sh
		echo test done
	
	done
	LOOPCOUNT=`expr $LOOPCOUNT - 1`
done
exit
