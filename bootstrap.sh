#!/bin/sh -e

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

for command in wget python git
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

command_exists pip || {
    # install pip
    wget -q https://bootstrap.pypa.io/get-pip.py -O- | python - --user
}

command_exists ansible || {
    # install ansible
    pip install --user ansible
}
