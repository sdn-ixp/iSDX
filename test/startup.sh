BASE=~/iSDX
TEST=test-ms
TEST=test-mt

if [ "$#" -ne 1 ] ; then
  echo "Usage: $0 test_name" >&2
  exit 1
fi

if [ -e $BASE/examples/$1 ] ; then
	TEST=$1
else
	echo "Usage: test_name $1 is not known" >&2
	exit 1
fi

echo -------------------------------
echo running test: $TEST
echo -------------------------------

(
  echo delaying for mininet
  sleep 15
  echo starting ryu
  ryu-manager $BASE/flanc/refmon.py --refmon-config $BASE/examples/$TEST/config/sdx_global.cfg >/dev/null 2>&1 &
  echo starting xctrl
  cd $BASE/xctrl/
  ./xctrl.py $BASE/examples/$TEST/config/sdx_global.cfg >/dev/null 2>&1 &
  sleep 3
  echo starting arp proxy
  cd $BASE/arproxy/
  sudo python arproxy.py $TEST >/dev/null 2>&1 &
  sleep 3
  echo starting route server
  cd $BASE/xrs/
  sudo python route_server.py $TEST >/dev/null 2>&1 &
  sleep 3
  echo starting participants
  cd $BASE/pctrl/
  sh run_pctrlr.sh $TEST >/dev/null 2>&1 &
  sleep 3
  echo starting exabgp
  exabgp $BASE/examples/$TEST/config/bgp.conf >/dev/null 2>&1 &
  sleep 5
  echo starting $TEST
  cd $BASE/test
  sudo python tmgr.py $BASE/examples/$TEST/config/test.json d l 'r x0 a1 b1 c1 c2' t
  
) &

echo starting mininext
cd $BASE/examples/$TEST/mininext
sudo ./sdx_mininext.py
echo exiting mininext
echo cleaning
cd $BASE/pctrl/
sh clean.sh
echo done

