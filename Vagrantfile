## This is the base Vagrantfile used to create the sdx-ryu box.

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/trusty64"
  #config.vm.box = "ubuntu/trusty32"

  config.vm.provider "virtualbox" do |v|
      v.customize ["modifyvm", :id, "--cpuexecutioncap", "80"]
      v.customize ["modifyvm", :id, "--memory", "2048"]
  end

  ## Guest Config
  config.vm.hostname = "sdx-ryu"
  config.vm.network :private_network, ip: "192.168.0.300"
  config.vm.network :forwarded_port, guest:6633, host:6637 # forwarding of port

  ## Provisioning
  #config.vm.provision :shell, privileged: false, :path => "setup/basic-setup.sh"
  #config.vm.provision :shell, privileged: false, :path => "setup/ovs-setup.sh"
  #config.vm.provision :shell, privileged: false, :path => "setup/mininet-setup.sh"
  #config.vm.provision :shell, privileged: false, :path => "setup/ryu-setup.sh"
  #config.vm.provision :shell, privileged: false, :path => "setup/sdx-setup.sh"

  ## SSH config
  config.ssh.forward_x11 = true


  config.vm.synced_folder ".", "/home/vagrant/sdx-ryu", type: "rsync",
    rsync__exclude: ".git/"

end
