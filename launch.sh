RUN_DIR=~/iSDX
RIBS_DIR=$RUN_DIR/xrs/ribs
TEST_DIR=test-ms
LOG_FILE=SDXLog.log

case $1 in
    (1)
        if [ ! -d $RIBS_DIR ]
        then
            mkdir $RIBS_DIR
        fi

        cd $RUN_DIR/pctrl
        sh clean.sh

        cd $RUN_DIR
        rm -f $LOG_FILE
        python logServer.py $LOG_FILE
        ;;

    (2)
        # the following gets around issues with vagrant direct mount
        sudo rm -rf ~/mini_rundir
        cd $RUN_DIR/examples/$TEST_DIR/mininext
        find * | cpio -pdm ~/mini_rundir
        cd ~/mini_rundir
        sudo ./sdx_mininext.py

        #cd $RUN_DIR/examples/$TEST_DIR/mininext
        #sudo ./sdx_mininext.py
        ;;

    (3)
        set -x

        cd $RUN_DIR
        ryu-manager $RUN_DIR/flanc/refmon.py --refmon-config $RUN_DIR/examples/$TEST_DIR/config/sdx_global.cfg &
        sleep 1

        python launch.py xctrl.xctrl $RUN_DIR/examples/$TEST_DIR/config/sdx_global.cfg
        sudo python launch.py arproxy.arproxy $TEST_DIR &
        sleep 1

        sudo python launch.py xrs.route_server $TEST_DIR &
        sleep 1

        sudo python launch.py pctrl.participant_controller $TEST_DIR 1 &
        sudo python launch.py pctrl.participant_controller $TEST_DIR 2 &
        sudo python launch.py pctrl.participant_controller $TEST_DIR 3 &
        sleep 1

        exabgp $RUN_DIR/examples/$TEST_DIR/config/bgp.conf
        ;;
esac
