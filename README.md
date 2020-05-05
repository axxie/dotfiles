# Installation

```bash
sh -c "$(wget -q -O- https://raw.githubusercontent.com/axxie/dotfiles/master/bootstrap.sh)"
```


# Vagrant file for testing

```ruby
# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.provider "virtualbox" do |vb|
    vb.gui = true
  end
  config.vm.provision "shell", inline: <<-SHELL
    apt-get install htop iotop
    ln -s /vagrant/dotfiles /home/vagrant/.dotfiles
    chown vagrant:vagrant /home/vagrant/.dotfiles

    systemctl stop apt-daily.service
    systemctl stop apt-daily.timer
    systemctl kill --kill-who=all apt-daily.service
    pkill -9 -f upgrade

    # wait until `apt-get updated` has been killed
    while ! (systemctl list-units --all apt-daily.service | egrep -q '(dead|failed)')
    do
        sleep 1;
    done
    pkill -9 -f upgrade
  SHELL
  config.vm.define "Ubuntu" do |ubuntu|
    ubuntu.vm.box = "Ubuntu"
  end
end
```