'''
Created on Jul 4, 2016

@author: Marc Pucci (Vencore Labs)
'''

'''
generate really big configurations
'''

import sys

import genlib

def main (argv):
    global outdir
    
    if len(argv) < 2:
        print 'usage: gen_big #_of_participants'
        exit()
    
    limit = int(argv[1])
    maxsub = 254
    minsub = 1
    peers = "peers "
    port = 80

    print "mode multi-switch"
    print "participants " + str(limit)
    
    for i in range(1, limit + 1):
        peers += " " + str(i)
    print peers
    print
    
    a = 172
    b = 0
    d = minsub
    c = 0
    for i in range(1, limit + 1):
        if d > maxsub:
            d = minsub
            c += 1
        print "participant " + str(i) + " " + str(i) + " PORT MAC " + str(a) + "." + str(b) + "." + str(c) + "." + str(d) + "/16"
        d += 1

    print
    print "host AS ROUTER _ IP           # testnode names of form a1_100 a1_110"
    print
    
    d = minsub
    c = 0
    for i in range(1, limit + 1):
        if d > maxsub:
            d = minsub
            c += 1
        if i == 1:
            print "announce " + str(i) + " 100.0.0.0/24"
        else:
            print "announce " + str(i) + " 140.0.0.0/24"
        d += 1
    print
    
    p = port
    listener = "listener AUTOGEN "   
    for i in range(2, limit + 1):
        listener += " " + str(p)
        print "flow " + genlib.part_router2host(1, 0) + " " + str(p) + " >> " + genlib.part2as(i)
        p += 1
    print
    print listener
    print
    
    print "test regress {\n\ttest xfer\n}"
    print
    print "test init {\n\tlistener\n}"
    print
    
    p = port
    print "test xfer {"
    for i in range(2, limit + 1):
        print "\tverify " + genlib.part_router2host(1, 0) + "_100 " + genlib.part_router2host(i, 0) + "_140" + " " + str(p)
        p += 1
    print "}"
    print
    
    print "test info {"
    print "\tlocal ovs-ofctl dump-flows S1"
    print "\tlocal ovs-ofctl dump-flows S2"
    print "\tlocal ovs-ofctl dump-flows S3"
    print "\tlocal ovs-ofctl dump-flows S4"
    print "\texec a1 ip route"
    print "\tbgp a1"
    print "\texec b1 ip route"
    print "\tbgp b1"
    print "\texec c1 ip route"
    print "\tbgp c1"
    print "}"
    print

    print "test flush {"
    for router in ('a1', 'b1'):
        print "\texec " + router + " ip -s -s neigh flush all"
    print "}"
    
        
if __name__ == "__main__":
    main(sys.argv)
