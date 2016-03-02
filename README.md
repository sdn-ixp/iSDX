# Industry Scale SDX Controller (iSDX)

## Installation: Vagrant Setup

###Prerequisite

To get started install these softwares on your ```host``` machine:

1. Install ***Vagrant***, it is a wrapper around virtualization softwares like VirtualBox, VMWare etc.: http://www.vagrantup.com/downloads

2. Install ***VirtualBox***, this would be your VM provider: https://www.virtualbox.org/wiki/Downloads

3. Install ***Git***, it is a distributed version control system: https://git-scm.com/downloads

4. Install X Server and SSH capable terminal
    * For Windows install [Xming](http://sourceforge.net/project/downloading.php?group_id=156984&filename=Xming-6-9-0-31-setup.exe) and [Putty](http://the.earth.li/~sgtatham/putty/latest/x86/putty.exe).
    * For MAC OS install [XQuartz](http://xquartz.macosforge.org/trac/wiki) and Terminal.app (builtin)
    * Linux comes pre-installed with X server and Gnome terminal + SSH (buitlin)   

###Basics

* Clone the ```iSDX``` repository from Github:
```bash 
$ git clone https://github.com/sdn-ixp/iSDX.git
```

* Change the directory to ```iSDX```:
```bash
$ cd iSDX
```

* Now run the vagrant up command. This will read the Vagrantfile from the current directory and provision the VM accordingly:
```bash
$ vagrant up
```

The provisioning scripts will install all the required software (and their dependencies) to run the SDX demo. Specifically it will install:
* [Ryu](http://osrg.github.io/ryu/)
* [Quagga](http://www.nongnu.org/quagga/)
* [Mininet](http://mininet.org/)
* [Exabgp](https://github.com/Exa-Networks/exabgp)

## Usage
Run the different setups provided in the examples directory. Check out the [`test-ms`](https://github.com/sdn-ixp/iSDX/tree/master/examples/test-ms) example for a simple case with three IXP participants.
