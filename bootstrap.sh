#!/bin/sh -e
set -e

# make sure user-specific bin is added to path
PATH="$HOME/.local/bin:$PATH"

command_exists() {
    command -v "$@" >/dev/null 2>&1
}

error() {
    echo ${RED}"Error: $@"${RESET} >&2
}

setup_color() {
    # Only use colors if connected to a terminal
    if [ -t 1 ]; then
        RED=$(printf '\033[31m')
        GREEN=$(printf '\033[32m')
        YELLOW=$(printf '\033[33m')
        BLUE=$(printf '\033[34m')
        BOLD=$(printf '\033[1m')
        RESET=$(printf '\033[m')
    else
        RED=""
        GREEN=""
        YELLOW=""
        BLUE=""
        BOLD=""
        RESET=""
    fi
}

setup_color

# The only cross-shell way to ask password
echo -n "Enter password: "
old_stty_cfg=$(stty -g)
stty -echo ; PASSWORD=$(head -n 1) ; stty $old_stty_cfg
echo ""

# Check password and sudo
if ! printf '%s\n' "$PASSWORD" | sudo -kS true >/dev/null 2>&1 ; then
    error "'sudo' command failed with supplied password"
    exit 1
fi

OS_VERSION=$(grep -oP 'VERSION_ID="\K\d+' /etc/os-release)

if [ $OS_VERSION -lt 16 ]; then
    PYTHON=python
else
    PYTHON=python3
fi

for command in wget $PYTHON git
do
    command_exists "$command" || {
        error "Required command \"$command\" is not installed"
        missing_requirement=yes
    }
done

if [ -n "$missing_requirement" ]; then
    exit 1
fi

echo Bootstrapping...

# For Ubuntu 18 python3-distutils must be installed to be able to use pip from python3
if [ $OS_VERSION -ge 18 ]; then
    $PYTHON -c "import distutils.util" >/dev/null 2>&1 || {
        echo "Installing python3-distutils..."
        printf '%s\n' "$PASSWORD" | sudo -S apt-get install -y python3-distutils
    }
fi


$PYTHON -c "import pip" >/dev/null 2>&1 || {
    python_version=$($PYTHON -V 2>&1 | sed 's/.* \([0-9]\).\([0-9]\).*/\1\2/')
    if [ "$python_version" -lt "30" ]; then
        wget -q https://bootstrap.pypa.io/pip/2.7/get-pip.py -O- | $PYTHON - --user
    elif [ "$python_version" -lt "37" ]; then
        wget -q https://bootstrap.pypa.io/pip/3.6/get-pip.py -O- | $PYTHON - --user
    else
        wget -q https://bootstrap.pypa.io/get-pip.py -O- | $PYTHON - --user
    fi
}

command_exists ansible || {
    # install ansible
    $PYTHON -m pip install --user ansible
}


if [ -d ~/.dotfiles ]; then
    cd ~/.dotfiles
    git pull
else
    git clone https://github.com/axxie/dotfiles.git ~/.dotfiles
    cd ~/.dotfiles
fi

ansible-playbook -i hosts local_env.yml --extra-vars "ansible_sudo_pass=$PASSWORD ansible_python_interpreter=auto" 
