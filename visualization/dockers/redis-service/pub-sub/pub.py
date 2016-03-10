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

        #message = '{name} says: {message}'.format(**locals())
        message = "C1|" + str(time) + "|" + str(cpuA) + "|" + str(cpuB)
        print message
        r.publish(channel, message)

    	for lsp in ['1', '2', '3', '4']:
            val = randint(0,100)
            message1 = "barf|" + str(lsp) + "|" + str(val)
            r.publish(channel, message1)
            print message1
            message2 = "barb|" + str(lsp) + "|" + str(val)
            r.publish(channel, message2)
            print message2
            t.sleep(1)

        for lsp in ['1', '2', '3', '4']:
            val = randint(0,1000)
            message1 = "dialf|" + str(lsp) + "|" + str(val)
            r.publish(channel, message1)
            print message1
            message2 = "dialb|" + str(lsp) + "|" + str(val)
            r.publish(channel, message2)
            print message2
            t.sleep(1)

    	message = "ng|SF|CHICAGO|" + str(cpuA);
    	r.publish(channel, message)
        t.sleep(1)
        message = "ng|DALLAS|SF|" + str(cpuB);
    	r.publish(channel, message)
    	print message
        message = "pathf|lsp1|NY->Chicago->Dallas";
    	r.publish(channel, message)
        t.sleep(1)
        message = "pathb|lsp1|NY->Chicago->Dallas->LA->Tampa->LA->Tampa->LA->Tampa";
    	r.publish(channel, message)
        t.sleep(1)
