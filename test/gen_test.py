'''
Created on Jan 18, 2016

@author: Marc Pucci (Vencore Labs)
'''

'''
Convert simple description into json policy definitions

participants are labeled from 'a' ... and correspond to 1 ...
ports (C1, C2) correspond to 0, 1, ... are router connections from name C1

create file with name 'participant_#.py where number runs from 1 to n (a - z)
'''

import sys
import json
import os
import shutil
import collections

import genlib         # iSDX parser

noisy = False                   # print extra output for debugging
policies = {}                   # details on participant policies (flow rules)
participants = {}               # details on each participant
outdir = 'output'               # base directory for results, will have XXXXX from XXXXX.spec added to it
template_dir = 'templates'      # directory for templates for configurations
genmini = False                 # don't generate mininet sub directories for quagga
config = None                   # parsed configuration
torch = {}                      # torch file for testing
ph_socket = 5551                # first socket for dynamic policy server

def main (argv):
    global outdir, ph_socket
    
    if len(argv) < 2:
        print 'usage: gen_test specification_file'
        exit()
    
    cfile = argv[1]

    try:
        config = genlib.parser(cfile)
    except Exception, e:
        print 'Configuration error: ' + cfile + ': ' + repr(e)
        exit()
        
    if config.portgap():
        print '\n\nWARNING: There is a gap in the port numbering - this is known to break things\n\n'
    
    participants = config.participants
    policies = config.policies
    sdx_mininet_template = os.path.join(template_dir, config.mode + '-sdx_mininet.py')
    sdx_global_template = os.path.join(template_dir, config.mode + '-sdx_global.cfg')
        
    # inbound and outbound rules are checked in global, not in policy files    
    for part in sorted(participants):
        p = participants.get(part)
        if len(policies[part]['inbound']) != 0:
            p['Inbound Rules'] = True
        else:
            p['Inbound Rules'] = False
        if len(policies[part]['outbound']) != 0:
            p['Outbound Rules'] = True
        else:
            p['Outbound Rules'] = False
        p['PH_SOCKET'] = [ "localhost", ph_socket]
        ph_socket += 1
        
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
    
    # config.spec file
    
    dst_file = 'config.spec'
    dst_file = os.path.join(config_dir, dst_file)
    print 'copying ' + cfile + ' to ' + dst_file
    shutil.copy(cfile, dst_file)
    
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
    for p in sorted(participants):
        part = participants[p]
        part['Flanc Key'] = 'Part' + p + 'Key'
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
            q['networks'] = participants[p]['networks']
            q['announcements'] = participants[p]['announcements']
            
            netnames = []
            for netnumb in range(len(q['networks'])):
                netnames.append(config.genname(netnumb, q['networks'][netnumb], genlib.part2as(p), r['index']))
            q['netnames'] = netnames
            
            q['asn'] = participants[p]['ASN']
            # convert participant + index into a1, b1, c1, c2, etc.
            hostname = genlib.part_router2host(p, r['index'])
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
    
    torch_file = 'torch.cfg'
    torch_file = os.path.join(config_dir, torch_file)
    print 'generating torch configuration file ' + torch_file  
         
    fout = open(torch_file, 'w')
    fout.write('\n\n')

    fout.write('bgprouters {\n')
    for bgpr in sorted(quagga):
        fout.write('\t' + bgpr + ' /tmp/' + bgpr + '\n')
    fout.write('}\n\n')
    
    fout.write('hosts {\n')
    for host in sorted(config.listeners):
        h = config.listeners[host]
        fout.write('\t' + host + ' /tmp/' + host + ' ' + h['bind'])
        for i in h['ports']:
            fout.write(' ' + i)
        fout.write('\n')
    fout.write('}\n\n')
    
    fout.write('participants {\n')
    for part in sorted(participants):
        p = participants[part]
        n = genlib.part2as(part)
        fout.write('\t' + n + ' ' + p['PH_SOCKET'][0] + ':' + str(p['PH_SOCKET'][1]) + '\n')
    fout.write('}\n\n')
    
    for test in config.tests:
        fout.write('test ' + test + ' {\n')
        t = config.tests[test]
        for c in t:
            fout.write('\t' + c + '\n')
        fout.write('}\n\n')
            
    fout.close()
    
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
    
    
if __name__ == "__main__":
    main(sys.argv)
