#!/usr/bin/python

"Create SDX topology with 4 Quagga edge routers"

import inspect, os, sys, atexit
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


class QuaggaTopo( Topo ):
    "Quagga topology example."

    def __init__( self ):

        "Initialize topology"
        Topo.__init__( self )

        # location of config dir
        configdir = os.path.abspath(sys.argv[1])

        "Initialize a service helper for Quagga with default options"
        quaggaSvc = QuaggaService(autoStop=False)

        "Path configurations for mounts"
        quaggaBaseConfigPath = configdir

        "List of Quagga host configs"
        quaggaHosts = []
        quaggaHosts.append(QuaggaHost(name = 'a1', ip = '172.0.0.1/16', mac = '08:00:27:89:3b:9f', port = 3))
        quaggaHosts.append(QuaggaHost(name = 'b1', ip = '172.0.0.11/16', mac ='08:00:27:92:18:1f', port = 4))
        quaggaHosts.append(QuaggaHost(name = 'c1', ip = '172.0.0.21/16', mac = '08:00:27:54:56:ea', port = 5))
        quaggaHosts.append(QuaggaHost(name = 'c2', ip = '172.0.0.22/16', mac = '08:00:27:bd:f8:b2', port = 6))


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

def addInterfacesForSDXNetwork( net ):
    # location of tnode relative to location of this script file
    scriptdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../test/tnode.py'))
    hosts=net.hosts
    print "Configuring participating ASs\n\n"
    for host in hosts:
        print "Host name: ", host.name
        if host.name=='a1':
            host.cmd('sudo ifconfig lo:1 100.0.0.1 netmask 255.255.255.0 up')
            host.cmd('sudo ifconfig lo:2 100.0.0.2 netmask 255.255.255.0 up')
            host.cmd('sudo ifconfig lo:110 110.0.0.1 netmask 255.255.255.0 up')
            host.cmd('sudo python '+scriptdir+' '+host.name+' &')
        if host.name=='b1':
            host.cmd('sudo ifconfig lo:140 140.0.0.1 netmask 255.255.255.0 up')
            host.cmd('sudo ifconfig lo:150 150.0.0.1 netmask 255.255.255.0 up')
            host.cmd('sudo python '+scriptdir+' '+host.name+' &')
        if host.name=='c1':
            host.cmd('sudo ifconfig lo:140 140.0.0.1 netmask 255.255.255.0 up')
            host.cmd('sudo ifconfig lo:150 150.0.0.1 netmask 255.255.255.0 up')
            host.cmd('sudo python '+scriptdir+' '+host.name+' &')
        if host.name=='c2':
            host.cmd('sudo ifconfig lo:140 140.0.0.1 netmask 255.255.255.0 up')
            host.cmd('sudo ifconfig lo:150 150.0.0.1 netmask 255.255.255.0 up')
            host.cmd('sudo python '+scriptdir+' '+host.name+' &')
        if host.name == "exabgp":
            host.cmd( 'route add -net 172.0.0.0/16 dev exabgp-eth0')

def startNetwork():
    info( '** Creating Quagga network topology\n' )
    topo = QuaggaTopo()
    global net
    net = Mininext(topo=topo, 
            controller=lambda name: RemoteController( name, ip='127.0.0.1' ))

    info( '** Starting the network\n' )
    net.start()
        
    info( '**Adding Network Interfaces for SDX Setup\n' )    
    addInterfacesForSDXNetwork(net)
    
    info( '** Running CLI\n' )
    CLI( net )

def stopNetwork():
    if net is not None:
        info( '** Tearing down Quagga network\n' )
        net.stop()

if __name__ == '__main__':
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stopNetwork)

    # Tell mininet to print useful information
    setLogLevel('info')
    startNetwork()
