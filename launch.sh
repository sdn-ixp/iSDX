RUN_DIR=~/iSDX
RIBS_DIR=$RUN_DIR/xrs/ribs
TEST_DIR=$1
LOG_FILE=SDXLog.log

set -x

case $2 in
    (1)
        if [ ! -d $RIBS_DIR ]
        then
            mkdir $RIBS_DIR
        fi

        cd $RUN_DIR
        sh pctrl/clean.sh

        rm -f $LOG_FILE
        python logServer.py $LOG_FILE
        ;;

    (2)
        # the following gets around issues with vagrant direct mount
        MINICONFIGDIR=~/mini_rundir
        sudo rm -rf $MINICONFIGDIR
        mkdir -p $MINICONFIGDIR
        cd $RUN_DIR/examples/$TEST_DIR/mininext
        find configs | cpio -pdm $MINICONFIGDIR
        cd ~
        sudo $RUN_DIR/examples/$TEST_DIR/mininext/sdx_mininext.py $MINICONFIGDIR/configs

        #cd $RUN_DIR/examples/$TEST_DIR/mininext
        #sudo ./sdx_mininext.py
        ;;

    (3)
        cd $RUN_DIR/flanc
        ryu-manager refmon.py --refmon-config $RUN_DIR/examples/$TEST_DIR/config/sdx_global.cfg &
        sleep 1

        cd $RUN_DIR/xctrl
        python xctrl.py $RUN_DIR/examples/$TEST_DIR/config/sdx_global.cfg

        cd $RUN_DIR/arproxy
        sudo python arproxy.py $TEST_DIR &
        sleep 1

        cd $RUN_DIR/xrs
        sudo python route_server.py $TEST_DIR &
        sleep 1

        cd $RUN_DIR/pctrl
        sudo python participant_controller.py $TEST_DIR 1 &
        sudo python participant_controller.py $TEST_DIR 2 &
        sudo python participant_controller.py $TEST_DIR 3 &
        sleep 1

        cd $RUN_DIR
        exabgp examples/$TEST_DIR/config/bgp.conf
        ;;
esac
