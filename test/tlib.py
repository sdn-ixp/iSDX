'''
Created on Oct 4, 2016

@author: Marc Pucci
'''

# TODO
# This library was initially common to gen_test and tmgr/tnode.
# it split when I separated configuration from test
# they need to become common again


import json
import collections

# host is specified as either name:port or /tmp/socket. In the latter case, port is None
# bind is the binding address for host listeners
# tcp and udp are lists of ports to listen on
Nodename = collections.namedtuple('Nodename', 'host, port, bind, tcp, udp' )

class parser:
    
    bgprouters = {}                 # hosts that are routers, not listeners, but we may want to send commands to anyway
    tests = {}                      # holds details for named tests
    participants = {}               # address of participant
    hosts = {}                      # address of a data source or sync host

    def __init__(self, cfile):

        try:
            f = open(cfile)
        except Exception, e:
            raise Exception('cannot open configuration file: ' + cfile + ': ' + repr(e))
        
        lines = 0    
        for line in f:
            lines += 1
            line = line.partition('#')[0]
            
            gather = []
            if "{" in line:
                got = False
                for line2 in f:
                    line2 = line2.partition('#')[0]

                    lines += 1
                    if '}' in line2:
                        got = True
                        break
                    gather.append(line2)
                if not got:
                    f.close()
                    raise Exception('Fatal error on line ' + str(lines) + ': unmatched { ... }')
            
            try:
                self._parse(line, gather)
            except Exception as err:
                f.close()
                raise Exception('Fatal error on line ' + str(lines) + ': ' + line + ' (' + str(err) + ')')
        f.close        
        
    def _parse (self, line, gather):
        tokens = line.split()
        if len(tokens) == 0:
            return
        
        if tokens[0] == 'participants':
            self._do_participants(tokens, gather)
        elif tokens[0] == 'flow':
            self._do_flow(tokens)
        elif tokens[0] == 'announce':
            self._do_announce(tokens)
        elif tokens[0] == 'test':
            self._do_test(tokens, gather)
        elif tokens[0] == 'listener':
            self._do_listener(tokens)
        elif tokens[0] == 'hosts':
            self._do_hosts(tokens, gather)
        elif tokens[0] == 'bgprouters':
            self._do_bgprouters(tokens, gather)
        else:
            raise Exception('unrecognized command')
    
    def _do_bgprouters (self, args, gather):
        if len(args) != 2 or args[1] != "{":
            raise Exception('usage: bgprouters {\n             host=name:port | /named/pipe\n         }\n ')
        for line in gather:
            n, t = self.getname(line)
            if n is None:
                continue
            self.bgprouters[n] = t
        #print self.bgprouters
        
    def _do_hosts (self, args, gather):
        if len(args) != 2 or args[1] != "{":
            raise Exception('usage: hosts {\n             host=name:port | /named/pipe\n         }\n ')
        for line in gather:
            n, t = self.getname(line)
            if n is None:
                continue
            self.hosts[n] = t
        #print self.hosts
        
    def _do_participants (self, args, gather):
        if len(args) != 2 or args[1] != "{":
            raise Exception('usage: participants {\n             host=name:port | /named/pipe\n         }\n ')
        for line in gather:
            n, t = self.getname(line)
            if n is None:
                continue
            self.participants[n] = t
        #print self.participants
    
    def getname (self, arg):
        arg = arg.partition('#')[0].strip('\n')
        args = arg.split()
        if len(args) == 0:
            return None, None
        if len(args) == 1:
            raise Exception('name host:port | /named/pipe [ bind_address [ tcp_ports ... ] ]')
        
        # print(args)
    
        name = args[0]
        addr = args[1]
        port = None
        bind = None
        tcp = []
        udp = []
        
        addr_port = addr.partition(':')
        if len(addr_port) == 3 and addr_port[1] == ':':
            addr = addr_port[0]
            port = addr_port[2]
            
        if len(args) >= 3:
            bind = args[2]
            
        for i in range(3, len(args)):
            tcp.append(args[i])
        
        # print(name + " " + addr + ' ' + str(port) + ' ' + str(bind) + ' ' + str(tcp) + ' ' + str(udp))
        return name, Nodename(addr, port, bind, tcp, udp)
        
            
    def _do_flow (self, args):
        if args[3] == '>>':
            self._outbound(args[1], args[2], args[4])
        elif args[2] == '<<':
            self._inbound(args[1], args[3])
        else:
            raise Exception('bad flow format')
        
            
    def _get_policy (self, name):        
        try:
            policy = self.policies[name]
        except:
            policy = {}
            policy["outbound"] = []
            policy["inbound"] = []
            self.policies[name] = policy
        return policy
    
                  
    def _inbound (self, dst, port):        
        #print 'inbound: dst=' + dst + ' port=' + port
        das, dasport = host2as_router(dst)
        n = as2part(das)
        
        policy = self._get_policy(n)
        tmp_policy = {}
        tmp_policy["cookie"] = self.cookie_id
        self.cookie_id += 1
    
        tmp_policy["match"] = {}
        tmp_policy["match"]["tcp_dst"] = int(port)
        tmp_policy["action"] = {"fwd": int(dasport)}
    
        # Add this to participants' outbound policies
        policy["inbound"].append(tmp_policy)
            
    
    def _outbound (self, src, port, dst):        
        #print 'outbound: src=' + src + ' port=' + port + ' dst=' + dst
        sas, sasport = host2as_router(src)
        das = dst  # destination is an AS not a host !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
        #print 'sas=' + sas + ' sasport=' + sasport + ' das=' + das
        
        n = as2part(sas)
        policy = self._get_policy(n)
            
        tmp_policy = {}
    
        # Assign Cookie ID
        tmp_policy["cookie"] = self.cookie_id
        self.cookie_id += 1
    
        # Match
        tmp_policy["match"] = {}
        tmp_policy["match"]["tcp_dst"] = int(port)
        # forward to participant number: convert name to assumed number (a=1)
        tmp_policy["action"] = {"fwd": int(as2part(das))}
        
        policy["outbound"].append(tmp_policy)
    
    
    
    hostformer = []
    
    def _do_host (self, args):        
        self.hostformer = []
        if len(args) < 2: 
            raise Exception('usage: host sequence of chars, IP, ROUTER, NET, AS (will be concatenated)')
        for i in range(1, len(args)):
            self.hostformer.append(args[i])
    
    
    # announce participant# name network name network ...
    # if a network starts with a dash, it will be configured but not announced to BGP
    
    def _do_announce (self, args):        
        if len(args) < 3: 
            raise Exception('usage: announce participant# network network ...')      
        
        announcements = []
        networks = []
        announce = True
        
        part = args[1]
        p = self.participants.get(part, {})
        netnumb = 0
        for i in range(2, len(args)):
            net = args[i]
            if net[0] == '-':
                net = net[1:]
                announce = False
            ip_fix = net.split('/')
            if len(ip_fix) != 2:
                raise Exception('Invalid network announcement ' + net)
            ip = ip_fix[0].split('.')
            if len(ip) != 4:
                raise Exception('Invalid ip address ' + ip_fix[0])
            if announce:
                announcements.append(net)
            networks.append(net)
            for r in p['Ports']:  # routers
                n = self.genname(netnumb, net, part2as(part), r['index'])
                #print 'auto gen nodename = ' + n
                # seed with the bind address in case will autogen nodes
                # and empty ports for sanity
                self.listeners[n] = {'bind': ip[0] + '.' + ip[1] + '.' + ip[2] + '.' + '1',
                            'ports': [] }
            netnumb += 1
        p['announcements'] = announcements
        p['networks'] = networks
    
    def _do_test (self, args, gather):
        if len(args) != 3 or args[2] != "{":
            raise Exception('usage: test testname {\n             test commands\n         }\n ')
        testname = args[1]
        testcmds = []
        
        for line in gather:
            line = line.partition('#')[0]
            args = line.split()
            if len(args) == 0:
                continue
            
            testcmds.append(line.strip())
        self.tests[testname] = testcmds    
        
# convert participant + index into a1, b1, c1, c2, etc., index starts at 0
def part_router2host(part, router):
    return part2as(part) + str(router + 1)

# names run from a - z, then aa, ab, ac, ... az, ba
nameset = 'abcdefghijklmnopqrstuvwxyz'
routerset = '0123456789'

def as2part (name):
    p = 0
    for c in name:
        p = p * len(nameset)
        n = nameset.find(c)
        if n < 0:
            raise Exception('bad AS name: ' + name)
        p += n + 1
    if p < 1: ############# TODO  or p > number_of_participants:
        return None
    return str(p)


def part2as (part):
    part = int(part)    # just in case
    if part < 1: ############## TODO  or part > number_of_participants:
        raise Exception('Illegal participant number: ' + str(part))
    base = len(nameset)
    n = ''
    while part != 0:
        n += nameset[(part-1) % base]
        part = (part - 1) / base
    return n[::-1]


def host2as_router(name):
    asys = ''
    r = ''
    lookforasys = True
    foundasys = False
    for c in name:
        if c in nameset:
            if not lookforasys:
                return None, None
            asys += c;
            foundasys = True
        elif c in routerset:
            if not foundasys:
                return None, None
            lookforasys = False
            r += c
    if not foundasys or r == '':
        return None, None
    n = int(r)
    if n <= 0:
        return None, None
    n -= 1  # routers run from 0 even though host is called a1, a2
    
    ################# TODO 
    # is this a valid AS and router?
    #p = as2part(asys)   # will raise exception if out of range
    #if n >= len(self.participants[p]['Ports']): # number of edge-routers
        #raise Exception('router does not exist for ' + name)
    return asys, str(n)

if __name__ == "__main__":
    p = parser('specs/test1-ms.spec')
    print 'bgprouters'
    print json.dumps(p.bgprouters, indent=4, sort_keys=True) 
    print 'peers'
    print json.dumps(p.peers, indent=4, sort_keys=True) 
    print 'listeners'
    print json.dumps(p.listeners, indent=4, sort_keys=True) 
    print 'tests'
    print json.dumps(p.tests, indent=4, sort_keys=True) 
    print 'mode'
    print json.dumps(p.mode, indent=4, sort_keys=True) 
    print 'policies'
    print json.dumps(p.policies, indent=4, sort_keys=True) 
    print 'participants'
    print json.dumps(p.participants, indent=4, sort_keys=True) 