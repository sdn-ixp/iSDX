'''
Created on Jan 18, 2016

@author: Marc Pucci (Vencore Labs)
'''

'''
Convert simple rules into json policy definitions
assumptions:

participants are labeled from 'a' ... and correspond to 1 ...
ports (C1, C2) correspond to 0, 1, ... are router connections from name C1 = only 1 digit is assumed

create file with name 'participant_#.py where number runs from 1 to n (a - z)
# NOTE changed to .cfg, not .py
'''

import sys
import json
import os
import shutil
import collections
import random

noisy = False                   # print extra output for debugging
cookie_id = 1                   # common cookie ID for flow rules (should this be per participant?)
policies = {}                   # details on participant policies (flow rules)
participants = {}               # details on each participant
peers = []                      # holds multiple peer group relationships
number_of_participants = 0      # needed for participants without rules
mode = None                     # operating mode - multi-table or multi-switch
modemin = 1000                  # first available switch port for this mode
outdir = 'output'               # base directory for results, will have XXXXX from XXXXX.spec added to it
template_dir = 'templates'      # directory for templates for configurations
sdx_mininet_template = None     # mode specific version of sdx_mininet.py
sdx_global_template = None      # mode specific version of sdx_global.cfg
nodes = {}                      # testing definitions of tnode ports
rhosts = []                     # hosts that are routers, not listeners, but we may want to send commands to anyway
tests = []                      # testing definitions of test operations
genmini = False                 # don't generate mininet sub directories for quagga

def main (argv):
    global outdir
    
    if len(argv) < 2:
        print 'usage: gen_test specification_file'
        exit()
    
    cfile = argv[1]
    
    # use consistent set of random numbers so mac addresses stay the same
    r = 0
    for c in cfile:
        r += ord(c)
    random.seed(r)

    try:
        f = open(cfile)
    except Exception, e:
        print 'cannot open configuration file: ' + cfile + ': ' + repr(e)
        exit()
    
    lines = 0    
    for line in f:
        lines += 1
        try:
            if parse(line) is False:
                print 'Fatal error on line ' + str(lines) + ': ' + line
                f.close()
                exit()
        except Exception as err:
            print 'Fatal error on line ' + str(lines) + ': ' + line + ' (' + str(err) + ')'
            f.close()
            exit()
    f.close
        
    # perform basic sanity checks
    
    if mode is None:
        print 'mode is not defined - must be multi-table or multi-switch'
        exit()
        
    m = seenall()
    if m is not None:
        print 'specification for ' + m + ' is missing'
        exit()
        
    if portgap():
        print 'There is a gap in the port numbering - this is known to break things'
        exit()
        
    # inbound and outbound rules are checked in global, instead of in policy files, sigh ...    
    for part in participants:
        p = participants.get(part)
        if len(policies[part]['inbound']) != 0:
            p['Inbound Rules'] = True
        else:
            p['Inbound Rules'] = False
        if len(policies[part]['outbound']) != 0:
            p['Outbound Rules'] = True
        else:
            p['Outbound Rules'] = False
        
    try:
        b = os.path.basename(cfile)
        s = b.split('.')
        b = s[0]
        outdir = os.path.join(outdir, b)
        os.mkdir(outdir)
        print 'Output will be in ' + outdir
    except:
        print 'Output directory ' + outdir + ' already exists or cannot be made'
        exit()
        
    mininet_dir = os.path.join(outdir, 'mininet')
    os.mkdir(mininet_dir)
    if genmini:
        mininet_configs_dir = os.path.join(mininet_dir, 'configs')
        os.mkdir(mininet_configs_dir)
    config_dir = os.path.join(outdir, 'config')
    os.mkdir(config_dir)
    policies_dir = os.path.join(outdir, 'policies')
    os.mkdir(policies_dir)
    
    # README.md file
    
    src_file = 'test-README.md'
    src_file = os.path.join(template_dir, src_file)
    dst_file = 'README.md'
    dst_file = os.path.join(outdir, dst_file)
    print 'generating ' + dst_file + ' from ' + src_file
    fin = open(src_file)
    fout = open(dst_file, 'w')
    for line in fin:
        if '_SPECFILE_' in line:
            line = line.replace('_SPECFILE_', cfile)
            dprint(line, fout)
            continue
        if '_SPECIFICATION_' in line:
            f = open(cfile)
            for l in f:
                dprint(l.strip('\n'), fout)
            f.close()
            continue
        dprint(line.rstrip('\n'), fout)
    fin.close()
    fout.close()
    
    # sdx_mininet.py
    
    dst_file = 'sdx_mininet.py'
    dst_file = os.path.join(mininet_dir, dst_file)
    print 'copying ' + sdx_mininet_template + ' to ' + dst_file
    shutil.copy(sdx_mininet_template, dst_file)
    
    # sdnip.py - one size fits all
    
    dst_file = 'sdnip.py'
    dst_file = os.path.join(mininet_dir, dst_file)
    sdnip_template = os.path.join(template_dir, 'sdnip.py')
    print 'copying ' + sdnip_template + ' to ' + dst_file
    shutil.copy(sdnip_template, dst_file)
    
    # per participant policy files (flow rules)
    # policy file that includes these file names
    
    sdx_policies = {}
    
    for p in policies:
        participant_file = 'participant_' + p + '.cfg'
        dir_participant_file = os.path.join(policies_dir, participant_file)
        print 'generating configuration file ' + dir_participant_file
                
        # don't include empty inbound or outbound definitions (sigh)
        if len(policies[p]['outbound']) == 0:
            policies[p].pop('outbound')
        if len(policies[p]['inbound']) == 0:
            policies[p].pop('inbound')
        if noisy:              
            print json.dumps(policies[p], indent=4, sort_keys=True)
        
        with open(dir_participant_file,'w') as f:
            json.dump(policies[p], f, indent=4, sort_keys=True)
        sdx_policies[p] = participant_file
    
    policy_file = 'sdx_policies.cfg'
    policy_file = os.path.join(config_dir, policy_file)
    print "generating policy file " + policy_file
    if noisy:
        print json.dumps(sdx_policies, indent=4, sort_keys=True)
    with open(policy_file,'w') as f:
        json.dump(sdx_policies, f, indent=4, sort_keys=True)
        
    # Fine Tune Participants
    ehport = 5001
    for p in sorted(participants):
        part = participants[p]
        part['EH_SOCKET'] = ['localhost', ehport]
        part['Flanc Key'] = 'Part' + p + 'Key'
        ehport += 1
        part['ASN'] = int(part['ASN'])
        
    print 'participants'
    if noisy:
        print json.dumps(participants, indent=4, sort_keys=True)
    
    # sdx_global.cfg
    
    dst_file = 'sdx_global.cfg'
    dst_file = os.path.join(config_dir, dst_file)
    print 'creating ' + dst_file + ' from ' + sdx_global_template
    
    fin = open(sdx_global_template)
    gc = json.load(fin)
    fin.close
    gc['Participants'] = participants
    
    for p in sorted(participants):
        ports = []
        for r in participants[p]['Ports']:  # routers
            ports.append(r['Id'])
        #print ports
        if len(ports) == 1:
            gc['RefMon Settings']['fabric connections']['main'][p] = ports[0]
        else:
            gc['RefMon Settings']['fabric connections']['main'][p] = ports
    # there are refmon settings for the fabric that assign the next port, but it doesn't seem to be used
            
    with open(dst_file,'w') as f:
        json.dump(gc, f, indent=4, sort_keys=True)
    
    # quagga
    
    quagga = {}
    for p in participants:
        for r in participants[p]['Ports']:  # routers
            # print r
            q = {}
            q['ip'] = r['NET']
            q['mac'] = r['MAC']
            q['port'] = r['Id']     #switch port
            q['networks'] = participants[p]['announce']
            
            netnames = []
            for netnumb in range(len(q['networks'])):
                netnames.append(genname(netnumb, q['networks'][netnumb], part2as(p), r['index']))
            q['netnames'] = netnames
            
            q['asn'] = participants[p]['ASN']
            # convert participant + index into a1, b1, c1, c2, etc.
            hostname = part_router2host(p, r['index'])
            # cmds.append('sudo python tnode.py ' + hostname)    # handle in sdx_mininet.py to simplify finding tnode.py
            quagga[hostname] = q
    
    mininet_file = 'mininet.cfg'
    mininet_file = os.path.join(mininet_dir, mininet_file)
    print 'generating mininet configuration file ' + mininet_file       
    if noisy:
        print json.dumps(quagga, indent=4, sort_keys=True)
    with open(mininet_file,'w') as f:
        json.dump(quagga, f, indent=4, sort_keys=True)
        
    # exabgp bgp.conf file
    '''
    neighbor 172.0.0.22 {
        description "Virtual AS C Router C2";
        router-id 172.0.255.254;
        local-address 172.0.255.254;
        local-as 65000;
        peer-as 300;
        hold-time 180;
    }
    '''
    src_exabgp_file = 'exabgp-bgp.conf'
    src_exabgp_file = os.path.join(template_dir, src_exabgp_file)
    dst_exabgp_file = 'bgp.conf'
    dst_exabgp_file = os.path.join(config_dir, dst_exabgp_file)
    print 'generating exabgp bgp.conf configuration file ' + dst_exabgp_file + ' using ' + src_exabgp_file
    fin = open(src_exabgp_file)
    fout = open(dst_exabgp_file, 'w')
    for line in fin:
        if '_NEIGHBORS_' not in line:
            dprint(line.rstrip('\n'), fout)
            continue
        for part in sorted(participants):
            p = participants[part]
            for r in p['Ports']:    # routers
                dprint('\n\tneighbor ' + r['IP'].split('/')[0] + ' {', fout)
                dprint('\t\tdescription "' + r['description'] + '";', fout)
                dprint('\t\trouter-id 172.0.255.254;', fout)
                dprint('\t\tlocal-address 172.0.255.254;', fout)
                dprint('\t\tlocal-as 65000;', fout)
                dprint('\t\tpeer-as ' + str(p['ASN']) + ';', fout)
                dprint('\t\thold-time 180;', fout)
                dprint('\t}', fout)
    fin.close()
    fout.close()
    
    # test.cfg test configuration
        
    testcfg = {}
    testcfg['hosts'] = nodes
       
    # generate list of all nodes for creating cmds that run on all nodes
    l = ''
    for node in sorted(nodes):
        l += ' ' + node
    testcfg['rhosts'] = rhosts
    # list of all routers.  these are not listeners, but we want to run commands on them
    r = ''
    for rtr in rhosts:
        r += ' ' + rtr
    
    testcfg['tests'] = {}

    i = 0
    for t in tests:
        testcfg['tests']['t' + str(i).zfill(2)] = t
        i += 1
    
    testcfg['commands'] = {}
    testcfg['commands'] = {'x0': 'route -n',
                        "x1": "ps ax",
                        "x2": "sudo ovs-ofctl dump-flows s1",
                        "x3": "sudo ovs-ofctl dump-flows s2",
                        "x4": "sudo ovs-ofctl dump-flows s3",
                        "x5": "sudo ovs-ofctl dump-flows s4",
                        "x6": "sudo ovs-ofctl show s1"
                        }
    
    testcfg['regressions'] = {}
    testcfg['regressions']['verbose'] = "l 'r x0" + r + "' 'e x1 x2 x3 x4 x5 x6' t"
    testcfg['regressions']['verbose-retry'] = "'r x0" + r + "' 'e x1 x2 x3 x4 x5 x6' t"
    testcfg['regressions']['terse'] = "l t"
    testcfg['regressions']['terse-retry'] = "'r x0" + r + "' t"
    
    dst_file = 'test.cfg'
    dst_file = os.path.join(config_dir, dst_file)
    print 'creating ' + dst_file
    if noisy:
        print json.dumps(testcfg, indent=4, sort_keys=True)
    with open(dst_file,'w') as f:
        json.dump(testcfg, f, indent=4, sort_keys=True)
        

    if not genmini:
        return
    
    # quagga bgpd.conf file
    '''
    !
    ! Zebra configuration saved from vty
    !   2013/10/02 20:47:51
    !
    hostname Virtual-AS-A
    password bgpd
    log stdout
    !
    router bgp 100
     bgp router-id 172.0.0.1
     neighbor 172.0.255.254 remote-as 65000
     neighbor 172.0.255.254 next-hop-self
     network 100.0.0.0/24
     network 110.0.0.0/24
     redistribute static
    !
    line vty
    !
    '''
    for part in sorted(participants):
        p = participants[part]
        for r in p['Ports']:   # routers  
            mininet_configs_host_dir = os.path.join(mininet_configs_dir, r['hostname'])
            os.mkdir(mininet_configs_host_dir)
  
            src_quagga_file = 'quagga-bgpd.conf'
            dst_quagga_file = 'bgpd.conf'
            dst_quagga_file = os.path.join(mininet_configs_host_dir, dst_quagga_file)
            src_quagga_file = os.path.join(template_dir, src_quagga_file)
            print 'generating quagga bgpd.conf configuration file ' + dst_quagga_file + ' using ' + src_quagga_file
            fin = open(src_quagga_file)
            fout = open(dst_quagga_file, 'w')
            for line in fin:
                if '_NETWORKS_' in line:
                    for a in p['announce']:
                        dprint(' network ' + a, fout)
                    continue

                if '_ASN_' in line:
                    line = line.replace('_ASN_', str(p['ASN']))
                    dprint(line, fout)
                    continue

                if '_DESCRIPTION_' in line:
                    line = line.replace('_DESCRIPTION_', r['description'].replace(' ', '-'))
                    dprint(line, fout)
                    continue
                
                if '_IP_' in line:
                    line = line.replace('_IP_', r['IP'])
                    dprint(line, fout)
                    continue
            
                dprint(line.rstrip('\n'), fout)
            fin.close()
            fout.close()
            
            # zebra
            
            src_quagga_file = 'quagga-zebra.conf'
            dst_quagga_file = 'zebra.conf'
            dst_quagga_file = os.path.join(mininet_configs_host_dir, dst_quagga_file)
            src_quagga_file = os.path.join(template_dir, src_quagga_file)
            print 'generating quagga zebra.conf configuration file ' + dst_quagga_file + ' using ' + src_quagga_file
            fin = open(src_quagga_file)
            fout = open(dst_quagga_file, 'w')
            for line in fin:
                if '_HOSTNAME_' in line:
                    line = line.replace('_HOSTNAME_', r['description'].replace(' ', '-'))
                    dprint(line, fout)
                    continue
                if '_HOST_' in line:
                    line = line.replace('_HOST_', r['hostname'])
                    dprint(line, fout)
                    continue
                dprint(line.rstrip('\n'), fout)
            fin.close()
            fout.close()            
            
            copylist = ( ('quagga-daemons', 'daemons'),
                         ('quagga-debian.conf', 'debian.conf')
                         )
            for c in copylist:
                src_file = os.path.join(template_dir, c[0])
                dst_file = os.path.join(mininet_configs_host_dir, c[1])
                print 'copying ' + src_file + ' to ' + dst_file
                shutil.copy(src_file, dst_file)
    

def dprint (line, fout):
    if noisy:
        print line
    fout.write(line + '\n')
    

def parse (line):
    line = line.partition('#')[0]
    tokens = line.split()
    if len(tokens) == 0:
        return True
    seen(tokens[0])
    
    if tokens[0] == 'participants':
        return do_participants(tokens)
    if tokens[0] == 'participant':
        return do_participant(tokens)
    if tokens[0] == 'flow':
        return do_flow(tokens)
    if tokens[0] == 'announce':
        return do_announce(tokens)
    if tokens[0] == 'peers':
        return do_peers(tokens)
    if tokens[0] == 'mode':
        return do_mode(tokens)
    if tokens[0] == 'test':
        return do_test(tokens)
    if tokens[0] == 'node':
        return do_node(tokens)
    if tokens[0] == 'host':
        return do_host(tokens)
    return False

    
def do_participants (args):
    global number_of_participants
    
    number = args[1]
    for i in range(1, int(number) + 1):
        get_policy(str(i))
    number_of_participants = int(number)
    return True

        
def do_flow (args):
    if args[3] == '>>':
        return outbound(args[1], args[2], args[4])
    if args[2] == '<<':
        return inbound(args[1], args[3])
    return False
    
        
def get_policy(name):
    global policies
    
    try:
        policy = policies[name]
    except:
        policy = {}
        policy["outbound"] = []
        policy["inbound"] = []
        policies[name] = policy
    return policy

              
def inbound (dst, port):
    global policies, cookie_id
    
    #print 'inbound: dst=' + dst + ' port=' + port
    das, dasport = host2as_router(dst)
    n = as2part(das)
    
    policy = get_policy(n)
    tmp_policy = {}
    tmp_policy["cookie"] = cookie_id
    cookie_id += 1

    tmp_policy["match"] = {}
    tmp_policy["match"]["tcp_dst"] = int(port)
    tmp_policy["action"] = {"fwd": int(dasport)}

    # Add this to participants' outbound policies
    policy["inbound"].append(tmp_policy)
    return True    
        

def outbound (src, port, dst):
    global cookie_id, policies
    
    #print 'outbound: src=' + src + ' port=' + port + ' dst=' + dst
    sas, sasport = host2as_router(src)
    das = dst  # destination is an AS not a host !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
    #print 'sas=' + sas + ' sasport=' + sasport + ' das=' + das
    
    n = as2part(sas)
    policy = get_policy(n)
        
    tmp_policy = {}

    # Assign Cookie ID
    tmp_policy["cookie"] = cookie_id
    cookie_id += 1

    # Match
    tmp_policy["match"] = {}
    tmp_policy["match"]["tcp_dst"] = int(port)
    # forward to participant number: convert name to assumed number (a=1)
    tmp_policy["action"] = {"fwd": int(as2part(das))}
    
    policy["outbound"].append(tmp_policy)
    return True


'''
    participant 3 300 7 08:00:27:54:56:ea 172.0.0.21 8 08:00:27:bd:f8:b2 172.0.0.22
    
    neighbor 172.0.0.21 {
        description "Virtual AS C Router C1";
        router-id 172.0.255.254;
        local-address 172.0.255.254;
        local-as 65000;
        peer-as 300;
        hold-time 180;
    }
    neighbor 172.0.0.22 {
        description "Virtual AS C Router C2";
        router-id 172.0.255.254;
        local-address 172.0.255.254;
        local-as 65000;
        peer-as 300;
        hold-time 180;
    }
'''

def do_participant (args):
    global participants
    
    if len(args) < 6 or len(args) % 3 != 0:
        return False
    part = args[1]
    ipart = int(part)
    asn = args[2]
    
    i = 3
    
    p = participants.get(part, {})
    p['ASN'] = asn
    routers = []
    index = 0
    while i < len(args):
        port = checkport(args[i])
        mac = checkmac(args[i+1], ipart, index)
        ip = args[i+2]
        i += 3
        #print 'part=' + part + ' asn=' + asn + ' port=' + port + ' mac=' + mac + ' ip=' + ip

        router = {}
        router['hostname'] = part_router2host(part, index)
        rhosts.append(part_router2host(part, index))
        router['Id'] = int(port) # switch port
        router['MAC'] = mac
        if len(ip.split('/')) != 2:
            raise Exception('malformed network address ' + ip)
        router['IP'] = ip.split('/')[0]
        router['NET'] = ip
        router['index'] = index
        router['description'] = 'Virtual AS ' + part2as(part)
        if len(args) > 6:
            router['description'] += ' Router ' + router['hostname']
        index += 1
        routers.append(router)
    p['Ports'] = routers
    
    # get the peer group and gen the peer set (less this instance)
    found = False
    for pg in peers:
        if found:
            break
        for n in pg:
            if n == ipart:
                found = True
                mypeers = []
                for m in pg:
                    if m != ipart:
                        mypeers.append(m)
                p['Peers'] = mypeers
                break
    '''        
    # do inbound and outbound rules exist (participant defs must follow flows)      
    if len(policies[part]['inbound']) != 0:
        p['Inbound Rules'] = True
    else:
        p['Inbound Rules'] = False
    if len(policies[part]['outbound']) != 0:
        p['Outbound Rules'] = True
    else:
        p['Outbound Rules'] = False
    '''        
    participants[part] = p
    return True

# define formatter for names of hosts.  special macros are:
# IP first part of network address, i.e., 150 in 150.0.0.0.24
# ROUTER - router number styarting from 1
# NET - network number starting from 1
# AS - AS letter name

hostformer = []

def do_host (args):
    global hostformer
    
    hostformer = []
    if len(args) < 2: 
        raise Exception('usage: host sequence of chars, IP, ROUTER, NET, AS (will be concatenated)')
    for i in range(1, len(args)):
        hostformer.append(args[i])
    return True

def genname (netnumb, ip, asys, router):
    h = ''
    for i in hostformer:
        if i == 'NETNUMB':
            h += str(netnumb + 1)
        elif i == 'IP':
            h += ip.split('.')[0]
        elif i == 'ROUTER':
            h += str(int(router) + 1)
        elif i == 'AS':
            h += asys
        else:
            h += i
    return h


# announce participant# name network name network ...

def do_announce (args):
    global announcements, participants
    
    if len(args) < 3: 
        raise Exception('usage: announce participant# network network ...')      
    
    announce = []
    
    part = args[1]
    p = participants.get(part, {})
    netnumb = 0
    for i in range(2, len(args)):
        net = args[i]
        ip_fix = net.split('/')
        if len(ip_fix) != 2:
            raise Exception('Invalid network announcement ' + net)
        ip = ip_fix[0].split('.')
        if len(ip) != 4:
            raise Exception('Invalid ip address ' + ip_fix[0])
        announce.append(net)
        for r in p['Ports']:  # routers
            n = genname(netnumb, net, part2as(part), r['index'])
            print 'auto gen nodename = ' + n
            # seed with the bind address in case will autogen nodes
            # and empty ports for sanity
            nodes[n] = {'bind': ip[0] + '.' + ip[1] + '.' + ip[2] + '.' + '1',
                        'ports': [] }
        netnumb += 1
    p['announce'] = announce
    return True


def do_peers (args):
    global number_of_participants
    
    if len(args) == 1:
        return False
    p = []
    for i in range(1, len(args)):
        n = int(args[i])
        if n < 1 or n > number_of_participants:
            print 'bad peer group value'
            return False
        p.append(n)
    #print p
    peers.append(p)
    return True


def do_mode (args):
    global mode, sdx_mininet_template, sdx_global_template
    
    if len(args) != 2:
        raise Exception('usage: mode multi-switch | multi-table')
    if mode is not None:
        raise Exception('error: mode already set')
    
    mode = args[1]
    sdx_mininet_template = os.path.join(template_dir, mode + '-sdx_mininet.py')
    sdx_global_template = os.path.join(template_dir, mode + '-sdx_global.cfg')
    if os.path.isfile(sdx_mininet_template) is False or os.path.isfile(sdx_global_template) is False:
        print 'mode ' + mode + ' is not recognized'
        return False
    
    if mode == 'multi-switch':
        for i in ['1', '2', '3', '4']:
            checkport(i)
    elif mode == 'multi-table':
        for i in ['1', '2']:
            checkport(i)
    else:
        raise Exception('unknown mode - cannot seed ovs ports')
        
    return True


def do_node (args):
    autogen = len(args) > 2 and args[1] == 'AUTOGEN'
    if autogen and len(args) < 3 or not autogen and len(args) < 4:
        raise Exception('usage: node host binding_address port ... OR node AUTOGEN port port ...')
    if autogen:
        for nn in sorted(nodes):
            n = nodes[nn]
            ports = []
            for i in range(2, len(args)):
                ports.append(args[i])
            n['ports'] = ports
            print 'auto gen node = ' + nn + ' ' + n['bind'] + ' ' + str(n['ports'])
        return
    n = nodes.get(args[1])
    if n is None:
        raise Exception('Node ' + args[1] + ' is not defined by an earlier network announcement')
    if len(n['ports']) != 0:
        raise Exception('Node ' + args[1] + ' is already defined')
    n['bind'] = args[2]
    ports = []
    for i in range(3, len(args)):
        ports.append(args[i])
    n['ports'] = ports
    return True


def do_test (args):
    if len(args) != 4:
        raise Exception('usage: test src_host dst_host dst_port')

    src = args[1]
    dst = args[2]
    dport = args[3]

    x = { }
    
    # validate that the source is a valid node - the binding address also comes from the node description
    try:
        n = nodes[src]
        x['src'] = src
        x['baddr'] = n['bind']
    except:
        raise Exception('bad source node')

    # validate the destination - the destination address also comes from the node description
    # there must be a listener for the port
    found = False
    try:
        i = 0
        for p in nodes[dst]['ports']:
            if p == dport:
                x['xdst'] = dst
                x['daddr'] = nodes[dst]['bind']
                x['dport'] = dport
                found = True
                break
            i += 1
    except:
        raise Exception('bad destination node')
    if found == False:
        raise Exception('bad destination port - no listener defined')    
    tests.append(x)
    return True

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
    if p < 1 or p > number_of_participants:
        raise Exception('Illegal AS name: ' + name)
    return str(p)


def part2as (part):
    part = int(part)    # just in case
    if part < 1 or part > number_of_participants:
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
                raise Exception('bad hostname: ' + name)
            asys += c;
            foundasys = True
        elif c in routerset:
            if not foundasys:
                raise Exception('bad hostname: ' + name)
            lookforasys = False
            r += c
    if not foundasys or r == '':
        raise Exception('bad hostname: ' + name)
    n = int(r)
    if n <= 0:
        raise Exception('bad hostname: ' + name)
    n -= 1  # routers run from 0 even though host is called a1, a2
    # is this a valid AS and router?
    p = as2part(asys)   # will raise exception if out of range
    if n >= len(participants[p]['Ports']): # number of edge-routers
        raise Exception('router does not exist for ' + name)
    return asys, str(n)
    
# convert participant + index into a1, b1, c1, c2, etc., index starts at 0
def part_router2host(part, router):
    return part2as(part) + str(router + 1)
 
# check if commands have appeared in the right order
# all predecessor commands must be seen before this cmd
# all successor cmds must not have occurred
# return True if cmd has already been seen

cmdorder = [ 'mode', 'participants', 'peers', 'participant', 'host', 'announce', 'flow', 'node', 'test']
cmdoptional = ['node', 'test']
cmdseen = {}
    
def seen (cmd):
    global cmdorder
    if cmd not in cmdorder:
        raise Exception('unknown command: ' + cmd)
    if cmd in cmdseen:
        already = True
    else:
        already = False
    cmdseen[cmd] = True
    match = False
    for i in cmdorder:
        if i == cmd:
            match = True
            continue
        if not match: # must have been seen
            if i not in cmdseen:
                raise Exception(i + ' must be specified before ' + cmd)
        else:
            if i in cmdseen:
                raise Exception(cmd + ' must be specified before ' + i)
    return already


def seenall ():
    for i in cmdorder:
        if i not in cmdseen:
            if i in cmdoptional:
                continue
            return i
    return None

checkports = {} 
  
def nextport ():
    for i in range(1, 50):
        if str(i) not in checkports:
            return str(i)
    raise Exception('out of ports')

def checkport (i):
    if i == 'PORT':
        i = nextport()
        print 'auto gen port = ' + i
    if i in checkports:
        raise Exception('port ' + i + ' is already used')
    try:
        ii = int(i)
    except:
        raise Exception(i + ' is an invalid port number')
    if ii <= 0:
        raise Exception(i + ' is an invalid port number')
    checkports[i] = True
    return i
    
def portgap ():
    gap = False
    for i in range(1, 50):
        if str(i) not in checkports:
            gap = True
        elif gap == True:
            return True
    return False

checkmacs = {} 
  
def nextmac (part, router):
    a = 0x08
    b = 0x00
    c = 0x27
    d = random.randint(0, 0xff)
    e = random.randint(0, 0xff)
    f = random.randint(0, 0xff)
    # function of particiapnt and interface - easy to find
    c = 0xBB
    d = 0xBB
    e = part
    f = router
    return '%02x:%02x:%02x:%02x:%02x:%02x' % (a, b, c, d, e, f)

# 08:00:27:54:56:ea
def checkmac (mac, part, router):
    if mac == 'MAC':
        mac = nextmac(part, router)
        print 'auto gen mac = ' + mac
    if mac in checkmacs:
        raise Exception('mac ' + mac + ' is already used')
    if len(mac) != 17:
        raise Exception('mac ' + mac + ' is poorly formatted')
    digits = mac.split(':')
    if len(digits) != 6:
        raise Exception('mac ' + mac + ' is poorly formatted')
    for pair in digits:
        if len(pair) != 2:
            raise Exception('mac ' + mac + ' is poorly formatted')
        try:
            int(pair, 16)
        except ValueError:
            raise Exception('mac ' + mac + ' is not hexadecimal')
    checkmacs[mac] = True
    return mac

def testseen ():
    global cmdseen 
    ccc = [
      ['mode', 'participants', 'peers', 'participant', 'announce', 'flow', 'node', 'test'],
      ['mode', 'participants', 'peers', 'participant', 'flow', 'node', 'test'],
      ['mode', 'participants', 'peers', 'participant', 'announce', 'announce', 'flow', 'announce', 'node', 'test'],
      ['participants', 'peers', 'participant', 'announce', 'flow', 'node', 'test'],
      ['mode', 'participants', 'peers', 'participant', 'announce', 'flow'],
      ['mode', 'participants', 'peers', 'participant', 'announce', 'flow', 'test'],
      ['mode', 'participants', 'peers', 'participant', 'announce', 'flow', 'node'],
      ]       
    print 'cmd order = ' + str(cmdorder)
    for cc in ccc:
        cmdseen = {}
        print 'sequence = ' + str(cc)
        try:
            for c in cc:
                if seen(c):
                    print c + ' already'
                else:
                    print c + ' ok'
            m = seenall()
            if m is None:
                print 'ALL OK'
            else:
                print 'missing command: ' + m
        except Exception as err:
            print err
            continue
                                       
    
if __name__ == "__main__":
    if False:
        for i in range(53):
            print str(i) + ' ' + part2as(i) + ' ' + str(as2part(part2as(i))) +' ' + part2as(as2part(part2as(i)))
        for x in ('a1', 'ab12', 'd1', '1c', 'a1b', 'a', '1', 'a0', 'l1'):
            try:
                a, r = host2as_router(x)   
                print x + ' ' + a + ' ' + r
            except Exception as err:
                print err
                continue 
        exit()
    main(sys.argv)
