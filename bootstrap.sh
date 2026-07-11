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

if [ -f password.txt ]; then
    # if password file is present, use it instead of asking user
    PASSWORD=$(cat password.txt)
    DEV_MODE=yes
else
    # The only cross-shell way to ask password
    echo -n "Enter password: "
    old_stty_cfg=$(stty -g)
    stty -echo ; PASSWORD=$(head -n 1) ; stty $old_stty_cfg
    echo ""
fi

# Check password and sudo
if ! printf '%s\n' "$PASSWORD" | sudo -kS true >/dev/null 2>&1 ; then
    error "'sudo' command failed with supplied password"
    exit 1
fi

if [ -f tags.txt ]; then
    TAGS=$(cat tags.txt)
    DEV_MODE=yes
else
    TAGS=all
fi

if command_exists python3; then
    PYTHON=python3
else
    PYTHON=python
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

command_exists "pipx" || {
    echo "Installing pipx"
    sudo -S apt-get install -y pipx
}

command_exists ansible || {
    pipx install ansible --include-deps
}

# If we are already in the dev dir, do not go to .dotfile and do git pull or git clone
if [ -z "${DEV_MODE}" ]; then
    if [ -d ~/.dotfiles ]; then
        cd ~/.dotfiles
        git pull
    else
        git clone https://github.com/axxie/dotfiles.git ~/.dotfiles
        cd ~/.dotfiles
    fi
fi

ansible-playbook -i hosts local_env.yml --tags "$TAGS" --extra-vars "ansible_sudo_pass=$PASSWORD ansible_python_interpreter=auto" 
