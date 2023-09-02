#!/bin/bash

# Csmith 설치 스크립트
git clone https://github.com/csmith-project/csmith.git
cd csmith
sudo apt install -y g++ cmake m4
cmake -DCMAKE_INSTALL_PREFIX=/usr/local .
sudo make && sudo make install

