#!/bin/bash

# Csmith 설치 스크립트
git clone https://github.com/csmith-project/csmith.git
cd csmith
sudo apt install -y g++ cmake m4
cmake -DCMAKE_INSTALL_PREFIX=/usr/local .
sudo make -j `nproc` && sudo make install

# YARPGen 설치 스크립트
git clone https://github.com/intel/yarpgen.git
cd yarpgen
mkdir build
cd build
cmake ..
sudo make -j `nproc` && sudo make install
sudo cp yarpgen /usr/local/bin/

