from settings import r
import sys
import time as t
from random import randint
import datetime

if __name__ == '__main__':
    channel = sys.argv[1]

    print 'Welcome to {channel}'.format(**locals())

    while True:
        cpuA = randint(0,100)
        cpuB = randint(0,100)
        time = datetime.datetime.fromtimestamp(t.time()).strftime('%Y-%m-%d %H:%M:%S')
        message = "C1|" + str(time) + "|" + str(cpuA) + "|" + str(cpuB)
        print message
        r.publish(channel, message)
	message = "C2|" + str(time) + "|" + str(cpuA) + "|" + str(cpuB)
        print message
        r.publish(channel, message)
	message = "B|" + str(time) + "|" + str(cpuA) + "|" + str(cpuB)
        print message
        r.publish(channel, message)

    	message = "ng|Outbound|Main|" + str(cpuA);
    	r.publish(channel, message)
        t.sleep(1)
        message = "ng|ARP-Proxy|Inbound|" + str(cpuB);
	message = "network_graph|Main|BGP-Proxy|bgp|20"
    	r.publish(channel, message)
