#!/bin/bash

echoerr() {
    >&2 echo "$@"
}

he_she_said_no() {
    [[ "$@" = "n" ]] || [[ "$@" = "N" ]]
}

root=$(dirname $(dirname $(realpath $0)))

cd $root
if [ ! -d "venv" ]; then
    read -p "Virtualenv not found, create? [Y/n] " create_venv
    if he_she_said_no $create_venv; then
        exit 0
    fi
    if ! command -v virtualenv &> /dev/null
    then
        read -p "virtualenv command missing, try to install? (debian based distros supported) [Y/n] " install_virtualenv
        if he_she_said_no $install_virtualenv; then
            exit 0
        fi
        sudo apt-get update && sudo apt-get install --no-install-recommends -y python3-virtualenv
    fi
    virtualenv -p python3 venv 1>&2
    ./venv/bin/pip3 install -r requirements.txt 1>&2
fi

echo "source $root/venv/bin/activate"