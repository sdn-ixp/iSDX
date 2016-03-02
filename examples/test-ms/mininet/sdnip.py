#!/usr/bin/python

# Libraries for creating SDN-IP networks

from mininet.topo import Topo
from mininet.node import OVSSwitch, Controller, Host
from mininet.net import Mininet
from mininet.log import info, debug
from mininet.cli import CLI
from mininet.util import netParse, ipStr
import imp, os, sys, time, socket
import imp, os, sys
from time import sleep

# Import the ONOS classes from onos.py in the ONOS repository
#if not 'ONOS_ROOT' in os.environ:
#    print 'ONOS_ROOT is not set.'
#    print 'Try running the script with \'sudo -E\' to pass your environment in.'
#    sys.exit(1)

#onos_path = os.path.join(os.path.abspath(os.environ['ONOS_ROOT']), 'tools/test/topos/onos.py')
#onos = imp.load_source('onos', onos_path)
#from onos import ONOS

class L2OVSSwitch(OVSSwitch):
    "An OVS switch that acts like a legacy L2 learning switch"

    def __init__(self, name, **params):
        OVSSwitch.__init__(self, name, failMode='standalone', **params)

    def start(self, controllers):
        # This switch should always have no controllers
        OVSSwitch.start(self, [])


class SdnipHost(Host):
    def __init__(self, name, ips, gateway, *args, **kwargs):
        super(SdnipHost, self).__init__(name, *args, **kwargs)

        self.ips = ips
        self.gateway = gateway

    def config(self, **kwargs):
        Host.config(self, **kwargs)

        debug("configuring route %s" % self.gateway)

        self.cmd('ip addr flush dev %s' % self.defaultIntf())
        for ip in self.ips:
            self.cmd('ip addr add %s dev %s' % (ip, self.defaultIntf()))

        self.cmd('ip route add default via %s' % self.gateway)

class Router(Host):
    
    def __init__(self, name, intfDict, *args, **kwargs):
        super(Router, self).__init__(name, **kwargs)

        self.intfDict = intfDict
        
    def config(self, **kwargs):
        super(Host, self).config(**kwargs)
        
        self.cmd('sysctl net.ipv4.ip_forward=1')

        for intf, configs in self.intfDict.items():
            self.cmd('ip addr flush dev %s' % intf)
            self.cmd('sysctl net.ipv4.conf.%s.rp_filter=0' % intf)
            if not isinstance(configs, list):
                configs = [configs]
                
            for attrs in configs:
                # Configure the vlan if there is one    
                if 'vlan' in attrs:
                    vlanName = '%s.%s' % (intf, attrs['vlan'])
                    self.cmd('ip link add link %s name %s type vlan id %s' % 
                             (intf, vlanName, attrs['vlan']))
                    addrIntf = vlanName
                    self.cmd('sysctl net.ipv4.conf.%s/%s.rp_filter=0' % (intf, attrs['vlan']))
                else:
                    addrIntf = intf
                    
                # Now configure the addresses on the vlan/native interface
                if 'mac' in attrs:
                    self.cmd('ip link set %s down' % addrIntf)
                    self.cmd('ip link set %s address %s' % (addrIntf, attrs['mac']))
                    self.cmd('ip link set %s up' % addrIntf)
                for addr in attrs['ipAddrs']:
                    self.cmd('ip addr add %s dev %s' % (addr, addrIntf))

class BgpRouter(Router):
    
    binDir = '/usr/lib/quagga'
    
    def __init__(self, name, intfDict,
                 asNum, neighbors, routes=[],
                 quaggaConfFile=None,
                 zebraConfFile=None,
                 runDir='/var/run/quagga', *args, **kwargs):
        super(BgpRouter, self).__init__(name, intfDict, **kwargs)
        
        self.runDir = runDir
        self.routes = routes
        
        if quaggaConfFile is not None:
            self.quaggaConfFile = quaggaConfFile
            self.zebraConfFile = zebraConfFile
        else:
            self.quaggaConfFile = '%s/quagga%s.conf' % (runDir, name)
            self.zebraConfFile = '%s/zebra%s.conf' % (runDir, name)
            
            self.asNum = asNum
            self.neighbors = neighbors
            
            self.generateConfig()
            
        self.socket = '%s/zebra%s.api' % (self.runDir, self.name)
        self.quaggaPidFile = '%s/quagga%s.pid' % (self.runDir, self.name)
        self.zebraPidFile = '%s/zebra%s.pid' % (self.runDir, self.name)

    def config(self, **kwargs):
        super(BgpRouter, self).config(**kwargs)

        self.cmd('%s/zebra -d -f %s -z %s -i %s'
                 % (BgpRouter.binDir, self.zebraConfFile, self.socket, self.zebraPidFile))
        while True:
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) # @UndefinedVariable
                s.connect(self.socket)
                #print 'connected - breaking'
                break
            except Exception, e:
                #print' ERROR: ' + repr(e)
                time.sleep(.1)
        #print 'zebra ready'
        self.cmd('%s/bgpd -d -f %s -z %s -i %s'
                 % (BgpRouter.binDir, self.quaggaConfFile, self.socket, self.quaggaPidFile))

    def generateConfig(self):
        self.generateQuagga()
        self.generateZebra()
        
    def generateQuagga(self):
        configFile = open(self.quaggaConfFile, 'w+')
        
        def writeLine(indent, line):
            intentStr = ''
            for _ in range(0, indent):
                intentStr += '  '
            configFile.write('%s%s\n' % (intentStr, line))
            
        def getRouterId(interfaces):
            for intfAttributesList in interfaces.itervalues():
                if not isinstance(intfAttributesList, list):
                    continue
                # Try use the first set of attributes, but if using vlans they might not have addresses
                intfAttributes = intfAttributesList[1] if not intfAttributesList[0]['ipAddrs'] else intfAttributesList[0]
                return intfAttributes['ipAddrs'][0].split('/')[0]

        #print("FDP %s" % getRouterId(self.intfDict))
        #print("  FDP %s" % str(self.intfDict))
        writeLine(0, 'hostname %s' % self.name);
        writeLine(0, 'password %s' % 'sdnip')
        writeLine(0, 'log file /var/run/quagga/q_%s' % self.asNum)
        writeLine(0, 'debug bgp')
        writeLine(0, '!')
        writeLine(0, 'router bgp %s' % self.asNum)
        writeLine(1, 'bgp router-id %s' % getRouterId(self.intfDict))
        writeLine(1, 'timers bgp %s' % '3 9')
        writeLine(1, '!')
        
        for neighbor in self.neighbors:
            writeLine(1, 'neighbor %s remote-as %s' % (neighbor['address'], neighbor['as']))
            writeLine(1, 'neighbor %s ebgp-multihop' % neighbor['address'])
            writeLine(1, 'neighbor %s timers connect %s' % (neighbor['address'], '5'))
            writeLine(1, 'neighbor %s advertisement-interval %s' % (neighbor['address'], '1'))
            if 'port' in neighbor:
                writeLine(1, 'neighbor %s port %s' % (neighbor['address'], neighbor['port']))
            writeLine(1, '!')
            
        for route in self.routes:
            writeLine(1, 'network %s' % route)
        
        configFile.close()
    
    def generateZebra(self):
        configFile = open(self.zebraConfFile, 'w+')
        configFile.write('hostname %s\n' % self.name)
        configFile.write('password %s\n' % 'sdnip')
        configFile.write('log file /var/run/quagga/z_%s debugging\n' % self.asNum)
        configFile.close()

    def terminate(self):
        self.cmd("ps ax | grep '%s' | awk '{print $1}' | xargs kill" 
                 % (self.socket))

        super(BgpRouter, self).terminate()

if __name__ == '__main__':
    info("Testing SDN-IP libraries\n")
    topo = TestTopo()
    net = Mininet(topo=topo, controller=None, switch=OVSSwitchONOS)
    net.addController(ONOSCluster(net.hosts))

    net.start()

    CLI(net)

    net.stop();
