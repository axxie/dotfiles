#!/bin/sh

echo Bootstrapping...

# install pip
wget -q https://bootstrap.pypa.io/get-pip.py -O get-pip.py
python get-pip.py --user

# make sure user-specific bin is added to path
. ~/.profile

# install ansible
pip install --user ansible
