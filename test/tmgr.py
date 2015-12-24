#!/usr/bin/python

#  Author:
#  Marc Pucci (Vencore Labs)

# tmgr - traffic manager - controls a constellation of traffic nodes
# to gen and recv traffic from / to specific bound interfaces and ports

import sys
import json
import socket
import random
import string
import platform
import os
import subprocess
import traceback
import time

config = {}     # JSON configuration data
hosts = {}
tests = {}
cmdfuncs = {}
commands = {}

def main (argv):
    global config, hosts, tests, cmdfuncs, commands
    
    if len(argv) < 2:
        print 'usage: tmgr config.json [ commands ]'
        exit()
    
    cfile = argv[1]
    
    try:
        f = open(cfile)
    except Exception, e:
        print 'cannot open configuration file: ' + cfile + ': ' + repr(e)
        exit()
        
    try:    
        config = json.load(f)
    except Exception, e:
        print 'bad data in configuration file: ' + cfile + ': ' + repr(e)
        exit()
    f.close()
    
    try:
        hosts = config["hosts"]
    except:
        print 'no host data in configuration file: ' + cfile
        exit()
    
    try:
        tests = config["tests"]
    except:
        print 'no test data in configuration file: ' + cfile
        exit()
        
    commands = config.get('commands', {})
        
    cmdfuncs = {
        'reset': (reset, hosts, 'reset (close) listeners - takes a few seconds to take effect'),
        'z': (reset, hosts, None),
        'kill': (kill, hosts, 'terminate traffic nodes'),
        'k': (kill, hosts, None),
        'listener': (listener, hosts, 'start listeners on nodes with bind addr and port'),
        'l': (listener, hosts, None),
        'dump': (dump, hosts, 'dump output from hosts - mainly to see if nodes are on-line'),
        'd': (dump, hosts, None),
        'test': (test, tests, 'execute tests - send request to source node and check expected destination'),
        't': (test, tests, None),
        'rexec': (rexec, None, 'run command on remote hosts'),
        'r': (rexec, None, None),
        'exec': (run, None, 'run command on this host'),
        'e': (run, None, None),
        'config': (show, None, 'show json configuration'),
        'c': (show, None, None),
        'help': (help, None, 'print this message'),
        'h': (help, None, None),
        '?': (help, None, None),
        'quit': (quit, None, 'exit this manager - leave nodes intact'),
        'q': (quit, None, None)
    }
    
    if len(argv) == 2:
        while True:
            try:
                parse(raw_input("> "))
            except EOFError:
                break
            except Exception, e:
                print 'MM:00 INFO: ' + repr(e)
                traceback.print_exc(file=sys.stdout)
                break
    else:
        for i in range(2, len(argv)):
            parse(argv[i])
        
    print 'MM:00 INFO: BYE' 


def parse (input):
    global cmdfuncs
    
    tokens = input.split()
    n = len(tokens)
    if n == 0:
        return
    cmd = tokens[0]
    if cmd[0] == '#':
        return
    
    # search for the command
    # if there is a dictionary in the list, iterate over all the elements or all the arguments
    # else pass the entire set of arguments to the command
    
    foo = cmdfuncs.get(cmd)
    if foo != None:
        func, jset, msg = foo
        if jset is None:
            func(tokens)
            return
        if n == 1:
            for h in sorted(jset):
                func(h)
        else:
            for i in range(1, n):
                func(tokens[i])
        return

    print 'MM:00 ERROR: unknown command: ' + cmd
    

# connect to the cmd interface or a host
# the host must be in the json file
# if it defines cmdifc and cmdport, use them; else use defaults
# todo: cache the ifc and port

def connect (host, why):
    global config
    
    try:
        hostdata = config['hosts'][host]
    except:
        print 'MM:' + host + ' ERROR: ' + why + ': Unknown host: ' + host
        return None
        
    try:
        cmdifc = hostdata['cmdifc']
        cmdport = hostdata['cmdport']
    except:
        if platform.system() == 'Windows':
            cmdifc = '127.0.0.1'
            cmdport = base36(host)
        else:
            cmdifc = '/tmp/' + host
            cmdport = 0
    
    print 'MM:' + host + ' INFO: ' + why + ': Connecting to ' + host + ' at ' + cmdifc + ':' + str(cmdport)

    try:
        if cmdifc.find('/') >= 0:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) # @UndefinedVariable
            s.connect(cmdifc)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((cmdifc, cmdport))
    except Exception, e:
        print 'MM:' + host + ' ERROR: ' + why + ': ' + repr(e)
        return None
    return s 
 

# grab any tnode queued data - this is usually just the result of a test
    
def dump (host):
    return generic(host, 'DUMP', 'dump\n')


# force tnode to exit

def kill (host):
    return generic(host, 'KILL', 'quit\n')


# terminate all listeners on a tnode, tnode does not exit

def reset (host):
    return generic(host, 'RESET', 'reset\n')


# execute a command locally

def run (args):
    if len(args) < 2:
        print 'MM:00 EXEC: ERROR usage: exec cmd cmd ...'
        print 'Commands are:'
        for c in sorted(commands):
            print '  ' + c + ': ' + commands[c].get('cmd', '<CMD>')
        return
    
    for i in range(1, len(args)):
        cmdname = args[i]
        try:
            c = commands[cmdname]['cmd']
        except:
            print 'MM:00 ERROR: EXEC FAILED unknown or poorly specified cmd: ' + cmdname
            continue
        print 'MM:00 EXEC: ' + cmdname + ': ' + c
        ca = c.split()
        try:
            p = subprocess.Popen(ca, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
        except Exception, e:
            out = ''
            err = 'Command Failed: ' + repr(e)
        print out + err
    return None
    

# execute a command remotely

def rexec (args):
    if len(args) < 3:
        print 'MM:00 REXEC: ERROR usage: rexec cmd host host ...'
        print 'Commands are:'
        for c in sorted(commands):
            print '  ' + c + ': ' + commands[c].get('cmd', '<CMD>')
        return
    cmdname = args[1]
    try:
        c = commands[cmdname]['cmd']
    except:
        print 'MM:00 ERROR: REXEC FAILED unknown or poorly specified cmd: ' + cmdname
        return
    for i in range(2, len(args)):
        host = args[i]
        print 'MM:' + host + ' REXEC ' + cmdname + ': ' + c
        generic(host, 'REXEC', 'exec ' + c + '\n')
        
        
# generic command interface to a tnode - send cmd, capture data

def generic (host, label, cmd):
    s = connect(host, label)
    if s == None:
        return None
    
    alldata = ''
    try:
        s.send(cmd)
        
        while True:
            data = s.recv(1024)
            if len(data) == 0:
                break
            alldata += data
            sys.stdout.write(data)
        s.close()
    except Exception, e:
        print 'MM:' + host + ' ERROR: ' + label + ': '+ repr(e)
        try:
            s.close()
        except:
            pass
        return None
    return alldata

 
# run a test from the json config - tell source to send to dst IP addr.
# expect result from appropriate host and interface       
 
def test (tn):
    global config
    rand = str(random.randint(1000000000, 9999999999)) # must be 10 characters
    try:
        src = config["tests"][tn]['src']
        baddr = config["tests"][tn]['baddr']
        daddr = config["tests"][tn]['daddr']
        dport = config["tests"][tn]['dport']
        xifc = config["tests"][tn]['xifc']
        xdst = config["tests"][tn]['xdst']
    except:
        print 'MM:00 ERROR: TEST FAILED unknown or poorly specified test: ' + tn
        return
            
    s = connect(src, 'TEST')
    if s == None:
        return
    
    try:
        s.send('test ' + rand + ' ' + baddr + ' ' + daddr + ' ' + str(dport) + '\n')
        alldata = ''
        while True:
            data = s.recv(1024)
            if len(data) == 0:
                break
            alldata += data
            sys.stdout.write(data)
        s.close()
    except Exception, e:
        print 'MM:00 ERROR: TEST FAILED ' + repr(e)
        return
    
    if alldata.find("ERROR") >= 0:
        print 'MM:00 ERROR: TEST ' + tn + ' TEST FAILED aborted'
        return
    
    for i in range(5):
        out = generic(xdst, 'RESULT', 'result ' + rand + '\n')   
        all = out.splitlines() # each line of result
        if len(all) < 1:
            print 'MM:00 ERROR: TEST FAILED No result from ' + xdst
            return
        result = all[len(all)-1]
        tokens = result.split()
        # keep legal messages with 7 tokens
        # b1:i0 OK: XFER 7186879947 127.0.0.1:55702->127.0.0.1:2220 12.9620259424 MBpS
        # c1:XX INFO: RESULT:  1514184701 is still pending
        if len(tokens) != 7:
            print 'MM:' + xdst + ' ERROR: TEST ' + tn + ' TEST FAILED - bad return string'
            return
        if tokens[3] != rand:
            print 'MM:' + xdst + ' ERROR: TEST ' + tn + ' TEST FAILED - incorrect id returned'
            return
        if not tokens[0].endswith(xifc):
            print 'MM:' + xdst + ' ERROR: TEST ' + tn + ' TEST FAILED - response on incorrect interface: sb: ' + xifc
            return
        if tokens[6] == 'PENDING':
            time.sleep(1)
            continue
        if not tokens[1] == 'OK:':
            print 'MM:' + xdst + ' ERROR: TEST ' + tn + ' TEST FAILED - BAD RESULT'
            return
        print 'MM:' + xdst + ' OK: TEST ' + tn + ' ' + rand + ' TEST PASSED ' + tokens[5] + ' ' + tokens[6]
        return
    print 'MM:' + xdst + ' ERROR: TEST ' + tn + ' ' + rand + ' TEST FAILED: PENDING TOO LONG'



def listener (host):
    interfaces = config["hosts"][host]['interfaces']
    
    for name in sorted(interfaces):
        s = connect(host, 'LISTENER')
        if s == None:
            return
        try:
            interface = interfaces[name]
            addr = interface['bind']
            port = interface['port']
        except:
            print 'MM: ' + host + 'ERROR: Bad interface spec ' + name
            continue
            
        try:
            s.send('listener ' + name + ' ' + addr + ' ' + str(port) + '\n')
            while True:
                data = s.recv(1024)
                if len(data) == 0:
                    break
                sys.stdout.write(data)
            s.close()
        except Exception, e:
            print 'MM:00 ERROR: ' + repr(e)
  
            
def show (args):
    print 'Hosts and Listening Interfaces:'
    for h in sorted(hosts):
        print h + ':'
        for i in sorted(hosts[h]['interfaces']):
            iv = hosts[h]['interfaces'][i]
            print '  ' + i + ': ' + iv.get('bind', '<MISSING BIND>') + ':' + str(iv.get('port', '<MISSING PORT>'))
    print
    print 'Tests: src -> dst with expected Listener:'
    for t in sorted(tests):
        tv = tests[t]
        print '  ' + t + ': ' + tv.get('src', '<SRC>') + \
            '(' + tv.get('baddr', '<BIND>') + ') -> ' + \
            tv.get('daddr', '<DADDR>') + ':' + \
            str(tv.get('dport', '<DPORT>')) + \
            '   exp: ' + tv.get('xdst', '<XDST>') + ':' + tv.get('xifc', '<XIFC>')
    print
    print 'Commands:'
    for c in sorted(commands):
        print '  ' + c + ': ' + commands[c].get('cmd', '<CMD>')
    if len(args) != 1:
        print
        print 'Complete configuration:'
        print json.dumps(config, indent=4, sort_keys=True)
 
        
def quit (args):
    print 'MM:00 EXITING'
    os._exit(0)

        
def help (args):
    for h in sorted(cmdfuncs):
        msg = cmdfuncs.get(h)[2]
        if msg is not None:
            print h + ':  ' + msg
    print
    print 'usual sequence is: dump, listener, test'

    
        
def base36(s):
    n = 0
    for c in string.lower(s):
        if c.isdigit():
            n = n * 36 + ord(c) - ord('0')
            continue
        if c.isalpha():
            n = n * 36 + ord(c) - ord('a') + 10
            continue
        n = n * 36 + 35  #treat everything else as a 'z'
    return n
        
if __name__ == "__main__":
    main(sys.argv)
