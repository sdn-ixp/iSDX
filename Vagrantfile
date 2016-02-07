# This is the base Vagrantfile used to create the iSDX box.

#Vagrant.configure("1") do |config|
  #config.vm.boot_mode = :gui
#end

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/trusty64"
  #config.vm.box = "ubuntu/trusty32"

  config.vm.provider "virtualbox" do |v|
      v.customize ["modifyvm", :id, "--cpuexecutioncap", "80"]
      v.customize ["modifyvm", :id, "--memory", "2048"]
  end

  ## Guest Config
  config.vm.hostname = "iSDX"
  config.vm.network :private_network, ip: "172.28.128.3"
  #config.vm.network :private_network, type: "dhcp"
  #config.vm.network :private_network, ip: "192.168.0.300"
  config.vm.network :forwarded_port, guest:6633, host:6637 # forwarding of port
  config.vm.network :public_network, ip: "10.0.0.100", :bridge => 'sdn-cntr-br'
  config.vm.network :public_network, :bridge => 'p1p1' # ARP
  config.vm.network :public_network, ip: "172.0.255.254/16", :bridge => 'p1p2' # BGP

  ## Provisioning
  config.vm.provision :shell, privileged: false, :path => "setup/basic-setup.sh"
  config.vm.provision :shell, privileged: false, :path => "setup/ovs-setup.sh"
  config.vm.provision :shell, privileged: false, :path => "setup/mininet-setup.sh"
  config.vm.provision :shell, privileged: false, :path => "setup/ryu-setup.sh"
  config.vm.provision :shell, privileged: false, :path => "setup/sdx-setup.sh"

  ## SSH config
  config.ssh.forward_x11 = true


  #config.vm.synced_folder ".", "/home/vagrant/iSDX", type: "rsync",
    #rsync__exclude: ".git/"
  config.vm.synced_folder ".", "/home/vagrant/iSDX"
  #config.vm.synced_folder ".", "/home/vagrant/iSDX", owner: "quagga", group: "quaggavty"

end
