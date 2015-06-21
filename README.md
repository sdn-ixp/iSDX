# Ryu based SDX Controller

## Installation: Vagrant Setup


####Prerequisite

To get started install these softwares on your ```host``` machine:

1. Install ***Vagrant***, it is a wrapper around virtualization softwares like VirtualBox, VMWare etc.: http://www.vagrantup.com/downloads

2. Install ***VirtualBox***, this would be your VM provider: https://www.virtualbox.org/wiki/Downloads

3. Install ***Git***, it is a distributed version control system: https://git-scm.com/downloads

4. Install X Server and SSH capable terminal
    * For Windows install [Xming](http://sourceforge.net/project/downloading.php?group_id=156984&filename=Xming-6-9-0-31-setup.exe) and [Putty](http://the.earth.li/~sgtatham/putty/latest/x86/putty.exe).
    * For MAC OS install [XQuartz](http://xquartz.macosforge.org/trac/wiki) and Terminal.app (builtin)
    * Linux comes pre-installed with X server and Gnome terminal + SSH (buitlin)   

####Basics

* Clone the ```sdx-ryu``` repository from Github:
```bash 
$ git clone https://github.com/sdn-ixp/sdx-ryu.git
```

* Change the directory to ```sdx-ryu```:
```bash
$ cd sdx-ryu
```

* Now run the vagrant up command. This will read the Vagrantfile from the current directory and provision the VM accordingly:
```bash
$ vagrant up
```

The provisioning scripts will install all the required software (and their dependencies) to run the SDX demo. Specifically it will install:
* [Ryu](http://osrg.github.io/ryu/)
* [Quagga](http://www.nongnu.org/quagga/)
* [MiniNExT](https://github.com/USC-NSL/miniNExT.git miniNExT/)
* [Exabgp](https://github.com/Exa-Networks/exabgp)

## Usage
__Mininet__ 

    $ cd ~/sdx-ryu/examples/simple/mininet  
    $ sudo ./sdx_mininext.py  

Make OVS use OpenFlow 1.3  

    $ sudo ovs-vsctl set bridge s1 protocols=OpenFlow13

Start __Ryu__ - The Controller  

    $ ryu-manager ~/sdx-ryu/ctrl/asdx.py --asdx-dir simple

Start the __Route Server__  

    $ cd ~/sdx-ryu/xrs
    $ sudo ./route_server.py simple

Start __ExaBGP__  

    $ exabgp ~/sdx-ryu/examples/simple/controller/sdx_config/bgp.conf

After using it, make sure to __remove__ old RIBs  

    $ sudo rm ~/sdx-ryu/xrs/ribs/172.0.0.* 
    
## Run the "simple" Example
Check if the route server has correctly advertised the routes  

    mininext> a1 route -n  
    Kernel IP routing table  
    Destination     Gateway         Genmask         Flags Metric Ref    Use Iface  
    140.0.0.0       172.0.1.3       255.255.255.0   UG    0      0        0 a1-eth0  
    150.0.0.0       172.0.1.4       255.255.255.0   UG    0      0        0 a1-eth0  
    172.0.0.0       0.0.0.0         255.255.0.0     U     0      0        0 a1-eth0  

Testing the Policies

The participants have specified the following policies:  

_Participant A - outbound:_

    matcht(dstport=80) >> fwd(B) + match(dstport=4321/4322) >> fwd(C)

_Participant C - inbound:_

    match(dstport = 4321) >>  fwd(C1) + match(dstport=4322) >> fwd(C2)

Starting the  `iperf` servers:  

    mininext> b1 iperf -s -B 140.0.0.1 -p 80 &  
    mininext> c1 iperf -s -B 140.0.0.1 -p 4321 &  
    mininext> c2 iperf -s -B 140.0.0.1 -p 4322 &  

Starting the  `iperf` clients:  

    mininext> a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 80 -t 2  
    mininext> a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4321 -t 2  
    mininext> a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4322 -t 2  

Successful `iperf` connections should look like this:  

    mininext> c2 iperf -s -B 140.0.0.1 -p 4322 &  
    mininext> a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4322 -t 2  
    ------------------------------------------------------------  
    Client connecting to 140.0.0.1, TCP port 4322  
    Binding to local address 100.0.0.1  
    TCP window size: 85.3 KByte (default)  
    ------------------------------------------------------------  
    [  3] local 100.0.0.1 port 4322 connected with 140.0.0.1 port 4322  
    [ ID] Interval       Transfer     Bandwidth  
    [  3]  0.0- 2.0 sec  1.53 GBytes  6.59 Gbits/sec  

In case the `iperf` connection is not successful, you should see the message, `connect failed: Connection refused.`
