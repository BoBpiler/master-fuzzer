#!/bin/bash

# 필수 패키지 업데이트
sudo apt-get update

# Csmith 설치 스크립트
git clone https://github.com/csmith-project/csmith.git
cd csmith
sudo apt install -y g++ cmake m4
cmake -DCMAKE_INSTALL_PREFIX=/usr/local .
sudo make -j `nproc` && sudo make install
cd ..

# YARPGen 설치 스크립트
git clone https://github.com/intel/yarpgen.git
cd yarpgen
mkdir build
cd build
cmake ..
sudo make -j `nproc` && sudo make install
sudo cp yarpgen /usr/local/bin/
cd ../..

# GCC, Clang 및 기타 필수 패키지 설치
sudo apt install -y gcc clang

# 크로스 컴파일러와 QEMU 설치 (GCC)
sudo apt-get install -y gcc-aarch64-linux-gnu
sudo apt-get install -y g++-aarch64-linux-gnu

# 크로스 컴파일러 설치 (Clang)
#sudo apt-get install -y clang-9-aarch64-linux-gnu
#sudo apt-get install -y clang++-9-aarch64-linux-gnu

# QEMU 설치
sudo apt-get install -y qemu-user-static
