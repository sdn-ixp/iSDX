#!/usr/bin/python

#  Author:
#  Marc Pucci (Vencore Labs)

# tnode: traffic node - gen / recv traffic on demand

import socket
import sys
import threading
import time
import json
import Queue
import platform
import os
import string
import subprocess
import copy

buf = "\x00" * 1024     # buffer for traffic generation
host = ""               # me
hosts = ""              # all known hosts from json config
tests = ""              # all known tests from json config
outq = Queue.Queue()    # save output messages in queue for later retrieval on command port, thread safe
generation = 0          # generation family of listeners for resetting earlier ones
lock = threading.Lock() # lock for accessing data reception results (completed and pending)
completed = { }         # completed data reception results
pending = { }           # pending data reception results

def main (argv):
    global host, hosts, tests
    
    if len(argv) == 3:      # get command connection details from json
        host = argv[1]
        cfile = argv[2]
    
        with open(cfile) as f:
            try:    
                config = json.load(f)
            except Exception, e:
                print 'bad json in config file: ' + cfile + ': ' + repr(e)
                exit()
        try:
            cmdifc = config["hosts"][host]['cmdifc']
            cmdport = config["hosts"][host]['cmdport']
        except:
            print 'No command interface spec for this host: ' + host
            exit()
    elif len(argv) == 2:     # get command connection by default based on OS
        host = argv[1]
        if platform.system() == 'Windows':
            cmdifc = '127.0.0.1'
            cmdport = base36(host)
        else:
            cmdifc = '/tmp/' + host
            cmdport = '0'
    else:
        print 'usage: tnode hostname [ config.json ]'
        exit()
           
    create_command_listener(cmdifc, cmdport)
    
    print host + ':00 Exiting'
    
# create a listener for commands

def create_command_listener (baddr, port):
    try:
        if baddr.find('/') >= 0:
            try:
                if os.path.exists(baddr):
                    os.unlink(baddr)
            except OSError:
                print 'could not create/remove unix socket ' + baddr
                return
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) # @UndefinedVariable
            s.bind(baddr)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((baddr, port))
    except socket.error , msg:
        print 'Bind failed on command interface ' + baddr + ' port ' + str(port) + ' Error Code : ' + str(msg[0]) + ' Message ' + msg[1] + '\n'
        return
    s.listen(5)
    output('XX', 'OK: Command listener established for ' + baddr + ' port ' + str(port))
    while True:
        conn, _ = s.accept()
        #print 'New cmd connection on ' + baddr + ':' + str(port) + ' from ' + addr[0] + ':' + str(addr[1])
        threading.Thread(target=cmd_thread, args=(conn, )).start()


def output(interface, s):
    outq.put(host + ':' + interface + ' ' + s + '\n')
    sys.stdout.write(host + ':' + interface + ' ' + s + '\n')

# create a listener for this interface

def create_listener (baddr, port, interface):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((baddr, port))
        s.listen(10)
    except socket.error, msg:
        return 'ERROR: Bind failed on ' + baddr + ':' + str(port) + ': ' + msg[1]
    t = threading.Thread(target=interface_listener_thread, args=(s, baddr, port, interface))
    t.start()
    return 'OK: listener established for ' + baddr + ':' + str(port)


def interface_listener_thread(s, baddr, port, interface):
    s.settimeout(10)
    mygeneration = generation
    while True:
        try:
            conn, addr = s.accept()
        except socket.timeout:
            if mygeneration == generation:
                continue
            else:
                output(interface, 'INFO: Listener terminating for ' + baddr + ':' + str(port))
                return
        fromto = addr[0] + ':' + str(addr[1]) + '->' + baddr + ':' + str(port)
        #print 'New connection on ' + baddr + ':' + str(port) + ' from ' + addr[0] + ':' + str(addr[1])
        threading.Thread(target=interface_thread , args=(conn, fromto, interface)).start()


# on-demand thread to consume data

def interface_thread(conn, fromto, interface):
    try:
        #conn.send('You have reached ' + name + '\n')
        count = 0
        conn.settimeout(5)   # platform dependent - sometimes new connection inherits from accept()
        t = time.time();
        rand = conn.recv(10)    # id is 10 characters
        lock.acquire()
        # keep at 7 tokens
        pending[rand] = host + ':' + interface + ' INFO: XFER ' + rand + ' IS STILL PENDING\n'
        lock.release()
        while True:
            data = conn.recv(2048)
            #print 'got: ' + str(len(data))
            if not data: 
                break
            if len(data) == 0:
                break
            count += len(data)
        t = time.time() - t
        msg = host + ':' + interface + ' OK: XFER ' + rand + ' ' + fromto + ' ' + str(count/(t*1e6)) + ' MBpS' + '\n'
    except Exception, e:
        msg = host + ':' + interface + ' ERROR: XFER ' + rand + ' ' + fromto + ' ' + repr(e) + '\n'
    try:
        conn.close()
    except:
        pass
    lock.acquire()
    pending.pop(rand)
    completed[rand] = msg
    lock.release()


# on-demand thread to process a command

def cmd_thread(conn):
    global generation
    data = conn.recv(1024)
    
    if len(data) == 0:
        conn.sendall(host + ':XX ERROR: No data\n')
        conn.close()
        return;
    
    tokens = data.split()
    n = len(tokens)
    if n == 0:
        conn.sendall(host + ':XX ERROR: Null data\n')
        conn.close()
        return;
    
    cmd = tokens[0]
    
    if cmd == 'quit':
        conn.sendall(host + ':XX OK: EXITING\n')
        conn.close()
        os._exit(1)

    if cmd == 'dump' and n == 1:
        while not outq.empty():
            conn.sendall(outq.get())
        conn.close()
        return;
    
    if cmd == 'exec':
        tokens.pop(0)
        try:
            p = subprocess.Popen(tokens, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
        except:
            out = 'Command Failed\n'
            err = ''
        conn.sendall(out)
        conn.sendall(err)
        conn.close()
        return
    
    if cmd == 'listener' and n == 4:
        name = tokens[1]
        addr = tokens[2]
        port = tokens[3]
        r = create_listener(addr, int(port), name)
        conn.sendall(host +':' + name + ' ' + r + '\n')
        conn.close()
        return;
    
    if cmd == 'test' and n == 5:
        rand = tokens[1]
        baddr = tokens[2]
        daddr = tokens[3]
        dport = tokens[4]
        
        m = rand + ' bind:' + baddr + ' dst:' + daddr + ':' + str(dport)
    
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((baddr, 0))
            s.settimeout(5)
            s.connect((daddr, int(dport)))
            s.sendall(rand) #must be 10 characters
            for _ in range(2000):
                s.sendall(buf)
            s.shutdown(1)
            #time.sleep(1)  # seems to be needed on windows or we get a violent server exception
            s.close()
        except Exception, e:
            conn.sendall(host + ':XX ERROR: ' + 'TEST ' + m + ' ERROR: ' + repr(e) + '\n')
            conn.close()
            return
        
        conn.sendall(host + ':XX OK: ' + 'TEST ' + m + ' TRANSFER COMPLETE\n')     
        conn.close()
        return;
    
    if cmd == 'result' and n == 2:
        rid = tokens[1]
        lock.acquire()
        c = completed.get(rid)
        p = pending.get(rid)
        if c is None and p is None:
            lock.release()
            msg = host + ':XX ERROR: RESULT ' + rid + ' does not exist\n'
        elif p is not None:
            lock.release()
            msg = p
        else:
            completed.pop(rid)
            lock.release()
            msg = c
        conn.sendall(msg)
        conn.close()
        return
    
    if cmd == 'reset':
        generation += 1
        conn.sendall(host + ':XX OK: ' + 'RESET new generation = ' + str(generation) + '\n')     
        conn.close()
        return;
    
    if cmd == 'result' and n == 1:
        lock.acquire()
        c = copy.copy(completed)
        p = copy.copy(pending)
        lock.release()
        for i in c:
            conn.sendall(c[i])
        for i in p:
            conn.sendall(p[i])
        conn.close()
        return
    
    conn.sendall(host + ':XX ERROR: Bad command: ' + data)
    conn.close()

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