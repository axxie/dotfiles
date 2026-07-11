# Installation

```bash
sh -c "$(wget -q -O- https://raw.githubusercontent.com/axxie/dotfiles/master/bootstrap.sh)"
```


# Testing

1. Create `Vagrantfile` file with the following content:

```ruby
# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get -y install git wget pipx
    ln -s /vagrant /home/vagrant/.dotfiles
    chown vagrant:vagrant /home/vagrant/.dotfiles
  SHELL
  config.vm.synced_folder ".", "/vagrant"
  config.vm.define "server" do |ubuntu_server|
    ubuntu_server.vm.box = "cloud-image/ubuntu-26.04"
  end
  config.vm.define "desktop" do |ubuntu_desktop|
    ubuntu_desktop.vm.box = "Ubuntu26"
    ubuntu_desktop.vm.provider "virtualbox" do |vb|
      vb.gui = true
    end
  end
end
```

2. Create `password.txt` with single line with word "vagrant" in it

3. The run these commands for testing:

```shell
$ vagrant up
$ vagrant ssh server -c "cd .dotfiles && ./bootstrap.sh"
$ vagrant ssh desktop -c "cd .dotfiles && ./bootstrap.sh"
```
