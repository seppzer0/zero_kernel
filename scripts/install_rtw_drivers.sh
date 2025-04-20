#!/bin/bash

set -e


function main() {
    mkdir -p ~/repos
    cd ~/repos
    git clone https://github.com/lwfinger/rtw88
    cd rtw88
    make
    make install
    make install_fw
}

main
