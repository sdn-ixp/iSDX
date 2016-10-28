#!/bin/bash

BASE=~/iSDX


TMGR=tmgr
#CONFIG=config.spec
#TMGR=tmgr2
CONFIG=torch.cfg

for i in {0..9999}
do
	LOG_DIR=$PWD/regress/regress.$(printf "%04d" $i)
	if [ ! -d $LOG_DIR ]
	then
		break
	fi
done

echo "Logging to $LOG_DIR"
mkdir -p $LOG_DIR

EXAMPLES=$BASE/test/output
# for now, tests must run from examples folder
EXAMPLES=$BASE/examples

# set to anything but 0 to run mininet in interactive mode - type control d continue
INTERACTIVE=0
STOPONERROR=0
PAUSEONERROR=0
MININET_TCPDUMP=0
REALNET=0


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
   -t)
     export MININET_TCPDUMP=1
     ;;
   -r)
     REALNET=1
     ;;
   -g)
     export GAUGE_CONFIG=`readlink -f "$2"`
     shift
     STATS_APP=stats/gauge.py
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
  echo "Usage: $0 -i -p -s -n number_of_loops -t test_name test_name ..." >&2
  echo "    -i runs interactive torch commands after tests" >&2
  echo "    -p pauses after any errors.  Implies -i if error" >&2
  echo "    -s is for stopping after any errors. Can be used with -p" >&2
  echo "    -t starts tcpdump on all routers and hosts in mininet." >&2
  echo "       Output is in /tmp/*.tcpdump and needs to be cleaned up manually" >&2
  echo "    -r is for running on a real network (no mininet)" >&2
  echo "    -g <gauge.conf> is for enabling collection of stats used by Grafana" >&2
  exit 1
fi

for TEST in $@
do
	if [ ! -e $EXAMPLES/$TEST/config/$CONFIG ] ; then
        echo $0 ERROR: Test $TEST is not defined
        exit 1
    fi
done

count=1
(( pad = $(echo $LOOPCOUNT | wc -c) - 1 ))
while (( count <= LOOPCOUNT ))
do
	pcount=$(printf %0${pad}d $count)
	for TEST in $@
	do

		echo -------------------------------
		echo running test: $TEST:$count
		if [ $INTERACTIVE != '0' ]
		then
			echo "****** RUNNING IN INTERACTVE MODE - type control-D when finished to continue **********"
		fi
		if [ $MININET_TCPDUMP != '0' -a $REALNET = '0' ]
		then
		    echo "****** TCPDUMP RUNNING on all ROUTERS.  'sudo rm /tmp/*.tcpdump' when done **********"
		fi
		echo -------------------------------

		# the cleanup script will kill this each test, so we have to restart it on same file - new version puts each test in its own log
		#tcpdump -i lo -w $LOG_DIR/lo.$pcount.pcap &

		python $BASE/logServer.py $LOG_DIR/$TEST.$pcount.log >/dev/null 2>&1 &
		sleep 1
		python $BASE/logmsg.py "running test: $TEST:$count"

		if [[ $REALNET = '0' ]]
		then
		    echo starting mininet

		    M0=/tmp/sdxm0.$$
		    mkfifo $M0

		    SYNC=/tmp/sdxsync.$$
		    mkfifo $SYNC

		    rm /var/run/quagga/*
		    cd $EXAMPLES/$TEST/mininet
		    cat $M0 | python ./sdx_mininet.py mininet.cfg "$BASE/test/tnode.py ../config/torch.cfg" $SYNC &
		    M_PID=$!
		    cat $SYNC

		    #sleep 2
		    #tcpdump -i x1-eth0 -w $BASE/test/$LOG_DIR/x1-eth0.$pcount.pcap &
		    #tcpdump -i x2-eth0 -w $BASE/test/$LOG_DIR/x2-eth0.$pcount.pcap &
		    #tcpdump -i s1-eth1 -w $BASE/test/$LOG_DIR/s1-eth1.$pcount.pcap &
		    #tcpdump -i s1-eth2 -w $BASE/test/$LOG_DIR/s1-eth2.$pcount.pcap &
		    #tcpdump -i s1-eth3 -w $BASE/test/$LOG_DIR/s1-eth3.$pcount.pcap &
		    #tcpdump -i s1-eth4 -w $BASE/test/$LOG_DIR/s1-eth4.$pcount.pcap &
		    #tcpdump -i s1-eth5 -w $BASE/test/$LOG_DIR/s1-eth5.$pcount.pcap &
		    #tcpdump -i s1-eth6 -w $BASE/test/$LOG_DIR/s1-eth6.$pcount.pcap &
		    #tcpdump -i s1-eth7 -w $BASE/test/$LOG_DIR/s1-eth7.$pcount.pcap &
		    #tcpdump -i s1-eth8 -w $BASE/test/$LOG_DIR/s1-eth8.$pcount.pcap &
		    #sleep 2
		fi

		echo starting ryu
		cd $BASE/flanc
		echo GAUGE_CONFIG is $GAUGE_CONFIG
		echo RUNNING ryu-manager ryu.app.ofctl_rest $STATS_APP refmon.py --refmon-config $EXAMPLES/$TEST/config/sdx_global.cfg
		 ryu-manager ryu.app.ofctl_rest $STATS_APP refmon.py --refmon-config $EXAMPLES/$TEST/config/sdx_global.cfg 2> $LOG_DIR/refmon.$pcount.stderr &
		sleep 10

		echo starting xctrl
		cd $BASE/xctrl/
		python ./xctrl.py $EXAMPLES/$TEST/config/sdx_global.cfg
		sleep 4
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
				python participant_controller.py $TEST $part &
				sleep 0.5
			fi
		done < $EXAMPLES/$TEST/config/sdx_policies.cfg
		sleep 5
		echo starting exabgp
		exabgp $EXAMPLES/$TEST/config/bgp.conf >/dev/null 2>&1 &
		sleep 10
		echo starting $TEST
		cd $BASE/test
		python $TMGR.py $EXAMPLES/$TEST/config/$CONFIG "test init regress"

		if grep -iq exception $LOG_DIR/refmon.$pcount.stderr
		then
		    echo "*** EXCEPTION in refmon.  See $LOG_DIR/refmon.$pcount.stderr"
		fi
		   
		FAIL=`grep -c FAILED $LOG_DIR/$TEST.$pcount.log`
		if [[ $FAIL = '0' ]]
		then
			echo "Test $TEST:$count succeeded.  All tests passed"
			python $BASE/logmsg.py "Test $TEST:$count succeeded.  All tests passed"
		else
			echo "Test $TEST:$count failed."
			python $BASE/logmsg.py "Test $TEST:$count failed."
			python $TMGR.py $EXAMPLES/$TEST/config/$CONFIG "test info"
			if [ $PAUSEONERROR != '0' ]
			then
				echo; echo "************ ERROR OCCCURED - PAUSING ************"
				echo enter TORCH commands followed by control-d to exit
				echo; echo "**************************************************"
				python $TMGR.py $EXAMPLES/$TEST/config/$CONFIG
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
			python $TMGR.py $EXAMPLES/$TEST/config/$CONFIG
		fi

		#echo capturing what processes are using what ports
		#for port in 4444 5555 6000 6633 6666 # 179 9020 27017
		#do
		#	echo ============ PORT $port
		#	lsof -i:$port
		#	echo ------------
		#	ps -fp $(lsof -i:$port -t)
		#done | python $BASE/loglines.py
		#sleep 2

		if [ $REALNET = '1' ]; then
		    echo cleaning up flows in switches
		    for i in {1..4}; do 
			echo === dpid $i
			ofdpa_delete_flows $i
			ofdpa_delete_groups $i
		    done
		fi

		echo cleaning up processes and files
		(
		sudo killall tcpdump
		sudo killall python /usr/bin/python /usr/lib/quagga/bgpd /usr/lib/quagga/zebra
		sudo killall exabgp
		sudo fuser -k 6633/tcp
		python ~/iSDX/pctrl/clean_mongo.py
		sudo rm -f ~/iSDX/xrs/ribs/*.db
		) >/dev/null 2>&1

		if [ $REALNET = '0' ]; then
		    echo telling mininet to shutdown
		    echo quit >$M0

		    wait $M_PID
		    rm -f $M0 $SYNC

		    echo cleaning up mininet
		    sudo mn -c >/dev/null 2>&1
		fi
		echo test done

	done
	(( count += 1 ))
done
exit
