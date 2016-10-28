#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, OVSSwitch, Node
from sdnip import BgpRouter, SdnipHost
import sys, json, yaml
import os

ROUTE_SERVER_IP = '172.0.255.254'
ROUTE_SERVER_ASN = 65000


class SDXTopo(Topo):

    def __init__(self, *args, **kwargs):
        Topo.__init__(self, *args, **kwargs)
        # Describe Code
        # Set up data plane switch - this is the emulated router dataplane
        # Note: The controller needs to be configured with the specific driver that
        # will be attached to this switch.
        

        # IXP fabric
        main_switch = self.addSwitch('S1')
        inbound_switch = self.addSwitch('S2')
        outbound_switch = self.addSwitch('S3')
        arp_switch = self.addSwitch('S4')

        self.addLink(main_switch, inbound_switch, 1, 1)
        self.addLink(main_switch, outbound_switch, 2, 1)
        self.addLink(main_switch, arp_switch, 3, 1)
        self.addLink(outbound_switch, inbound_switch, 2, 2)

        # Add node for central Route Server"
        route_server = self.addHost('zzz1', ip='172.0.255.254/16', mac='08:00:27:89:3b:ff', inNamespace=False)
        self.addLink(main_switch, route_server, 4)
        
        # Add node for ARP Proxy"
        arp_proxy = self.addHost('zzz2', ip='172.0.255.253/16', mac='08:00:27:89:33:ff', inNamespace=False)
        self.addLink(arp_switch, arp_proxy, 2)
        
        # Add Participants to the IXP
        # Each participant consists of 1 quagga router PLUS
        # 1 host per network advertised behind quagga
        
        # host  details are now in config 
        config = args[0][0]      
        for host in sorted(config):
            self.addParticipant(fabric=main_switch,
                            name=host,
                            port=config[host]['port'],
                            mac=config[host]['mac'],
                            ip=config[host]['ip'],
                            networks=config[host]['networks'],
                            asn=config[host]['asn'],
                            netnames=config[host]['netnames'],
                            announcements=config[host]['announcements'])
           
    def addParticipant(self, fabric, name, port, mac, ip, networks, asn, netnames, announcements):
        print 'name=' + name + ' ip=' + ip + ' networks=' + str(networks)
        # Adds the interface to connect the router to the Route server
        peereth0 = [{'mac': mac, 'ipAddrs': [ip]}]
        intfs = {name+'-eth0': peereth0}

        # Adds 1 gateway interface for each network connected to the router
        for net in networks:
            eth = {'ipAddrs': [replace_ip( net, '254')]}  # ex.: 100.0.0.254
            i = len(intfs)
            intfs[name+'-eth'+str(i)] = eth
            
        # Set up the peer router
        neighbors = [{'address': ROUTE_SERVER_IP, 'as': ROUTE_SERVER_ASN}]
        peer = self.addHost(name, intfDict=intfs, asNum=asn,
                            neighbors=neighbors, routes=announcements, cls=BgpRouter)
        self.addLink(fabric, peer, port)
        
        # Adds a host connected to the router via the gateway interface
        i = 0
        for net in networks:
            i += 1
            ips = [replace_ip(net, '1')]  # ex.: 100.0.0.1/24
            hostname = 'h' + str(i) + '_' + name  # ex.: h1_a1
            hostname = netnames[i-1]
            host = self.addHost(hostname,
                                cls=SdnipHost,
                                ips=ips,
                                gateway = replace_ip( net, '254').split('/')[0])  #ex.: 100.0.0.254
            # Set up data plane connectivity
            self.addLink(peer, host)


def replace_ip(network, ip):
    net, subnet = network.split('/')
    gw = net.split('.')
    gw[3] = ip
    gw = '.'.join(gw)
    gw = '/'.join([gw,subnet])
    return gw

if __name__ == "__main__":
    setLogLevel('info')
    
    argc = len(sys.argv)
    if argc < 2 or argc > 4:
        raise Exception('usage: sdx_mininet config.json [ "path_to_tnode.py torch.cfg" [ semaphore_name ] ]')
    config_file = sys.argv[1]
    configfd = open(config_file)
    config = yaml.safe_load(configfd)
    configfd.close()
    
    if argc > 2:
        tnode_file = sys.argv[2]
    else:
        tnode_file = None
        
    topo = SDXTopo((config, ))
    
    net = Mininet(topo=topo, controller=RemoteController, switch=OVSSwitch)
    
    net.start()
    
    # start traffic nodes on all interior hosts - host names are free form, but are found in config
    
    if tnode_file is not None:
        tnodenames = []
        for h in config:
            tnodenames.append(h)                    # router
            for nn in config[h]['netnames']:
                tnodenames.append(nn)               # hosts on router
        
        for host in net.hosts:
            if host.name in tnodenames:
                host.cmd('python ' + tnode_file + ' ' + host.name + ' &')
                if 'MININET_TCPDUMP' in os.environ and host.name.find('_') == -1:
                    # tcpdump on routers, but not hosts
                    host.cmd('tcpdump -e -qnn > /tmp/' + host.name + '.tcpdump &')
    
    # if a semaphore was provided, write into it to signal the next process to start
    if argc > 3:
        semaphore_file = sys.argv[3]
        sync = open(semaphore_file, 'w')
        sync.write("MININET READY\n")
        sync.close()

    CLI(net)

    net.stop()

    info("done\n")
