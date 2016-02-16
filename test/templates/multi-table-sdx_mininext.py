#!/usr/bin/python

"Create SDX topology Quagga edge routers defined by mininext.cfg"

import inspect, os, sys, atexit, json
# Import topo from Mininext
from mininext.topo import Topo
# Import quagga service from examples
from mininext.services.quagga import QuaggaService
# Other Mininext specific imports
from mininext.net import MiniNExT as Mininext
from mininext.cli import CLI
import mininext.util
# Imports from Mininet
import mininet.util
mininet.util.isShellBuiltin = mininext.util.isShellBuiltin
sys.modules['mininet.util'] = mininet.util

from mininet.util import dumpNodeConnections
from mininet.node import RemoteController
from mininet.node import Node
from mininet.link import Link
from mininet.log import setLogLevel, info
from collections import namedtuple
#from mininet.term import makeTerm, cleanUpScreens
QuaggaHost = namedtuple("QuaggaHost", "name ip mac port")
net = None
sentsync = False
config = {}

class QuaggaTopo( Topo ):
    "Quagga topology example."

    def __init__( self ):
        global config
        "Initialize topology"
        Topo.__init__( self )

        # location of config dir
        configdir = os.path.abspath(sys.argv[1])

        "Initialize a service helper for Quagga with default options"
        quaggaSvc = QuaggaService(autoStop=False)

        "Path configurations for mounts"
        quaggaBaseConfigPath = configdir

        "List of Quagga host configs"
        config_file = open('mininext.cfg')
        config = json.load(config_file)
        config_file.close()
        
        quaggaHosts = []
      
        for host in sorted(config):
            fooip = config[host]['ip'] + '/16'
            foomac = config[host]['mac']
            fooport = config[host]['port']
            host = str(host)            # json gives unicode - confuses quagga
            #print 'adding: ' + host + ' ' + fooip + ' ' + foomac + ' ' + str(fooport)
            quaggaHosts.append(QuaggaHost(name = host, ip = fooip, mac = foomac, port = fooport))

        "Add switch for IXP fabric"
        main_switch = self.addSwitch( 's1' )
        arp_switch = self.addSwitch( 's2' )
        self.addLink(main_switch, arp_switch, 1, 1)


        # Add node for central Route Server"
        route_server = self.addHost('x1', ip = '172.0.255.254/16', mac='08:00:27:89:3b:ff', inNamespace = False)
        self.addLink(main_switch, route_server, 2)

        # Add node for ARP Proxy"
        arp_proxy = self.addHost('x2', ip = '172.0.255.253/16', mac='08:00:27:89:33:ff', inNamespace = False)
        self.addLink(arp_switch, arp_proxy, 2)

        "Setup each legacy router, add a link between it and the IXP fabric"
        for host in quaggaHosts:
            "Set Quagga service configuration for this node"
            quaggaSvcConfig = \
            { 'quaggaConfigPath' : os.path.join(configdir, host.name) }

            quaggaContainer = self.addHost( name=host.name,
                                            ip=host.ip,
                                            mac=host.mac,
                                            privateLogDir=True,
                                            privateRunDir=True,
                                            inMountNamespace=True,
                                            inPIDNamespace=True)
            self.addNodeService(node=host.name, service=quaggaSvc,
                                nodeConfig=quaggaSvcConfig)
            "Attach the quaggaContainer to the IXP Fabric Switch"
            self.addLink( quaggaContainer, main_switch , port2=host.port)
            print 'connecting ' + str(host.name) + ' to main ' + str(host.port)

def addInterfacesForSDXNetwork( net ):
    # location of tnode relative to location of this script file
    # this assumes this directory is in a relative position to the examples directory
    # if not, add or remove a ..
    scriptdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../test/tnode.py'))
    hosts=net.hosts
    for host in hosts:
        #print "Host name: ", host.name
        if host.name in config:
            for cmd in config[host.name]['cmds']:
                host.cmd(cmd)
            host.cmd('sudo python '+scriptdir+' '+host.name+' &')

    
def startNetwork():
    info( '** Creating Quagga network topology\n' )
    topo = QuaggaTopo()
    global net, sentsync
    net = Mininext(topo=topo, 
            controller=lambda name: RemoteController( name, ip='127.0.0.1' ))

    info( '** Starting the network\n' )
    net.start()
        
    info( '**Adding Network Interfaces for SDX Setup\n' )    
    addInterfacesForSDXNetwork(net)
    
    # if a fifo was given, write into it to indicate ready
    if len(sys.argv) >= 3:
        sync = open(sys.argv[2], 'w')
        sync.write("MININEXT READY\n")
        sync.close()
        sentsync = True
    CLI( net )

def stopNetwork():
    if net is not None:
        info( '** Tearing down Quagga network\n' )
        net.stop()
    if len(sys.argv) >= 3 and sentsync is False:
        sync = open(sys.argv[2], 'w')
        sync.write("MININEXT DIED\n")
        sync.close()

if __name__ == '__main__':
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stopNetwork)

    # Tell mininet to print useful information
    setLogLevel('info')
    startNetwork()
