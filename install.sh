#!/bin/bash

# 필수 패키지 업데이트
sudo apt-get update || { echo "Failed to update packages"; exit 1; }

# GCC 설치
install_gcc() {
  git clone https://github.com/gcc-mirror/gcc.git || { echo "Failed to clone gcc"; return 1; }
  cd gcc || { echo "Failed to enter gcc directory"; return 1; }
  git checkout trunk || { echo "Failed to checkout trunk"; return 1; }
  sudo apt install gnat libmpfr-dev libmpfr-doc libgmp-dev libmpc3 libmpc-dev flex g++-multilib || { echo "Failed to install dependencies"; return 1; }
  contrib/download_prerequisites || { echo "Failed to download prerequisites"; return 1; }
  mkdir build && cd build || { echo "Failed to enter build directory"; return 1; }
  ../configure --prefix=$HOME/gcc-trunk\
               --enable-languages=c,c++ \
               --disable-multilib \
               --program-suffix=-trunk || { echo "Configure failed"; return 1; }
  make -j $(expr `nproc` / 2) || { echo "Make failed"; return 1; }
  make install
  cd ../../
}

# Clang 설치
install_clang() {
  git clone https://github.com/llvm/llvm-project.git || { echo "Failed to clone llvm-project"; return 1; }
  cd llvm-project || { echo "Failed to enter llvm-project directory"; return 1; }
  git checkout llvmorg-18-init || { echo "Failed to checkout llvmorg-18-init"; return 1; }
  mkdir build && cd build || { echo "Failed to enter build directory"; return 1; }
  cmake -DLLVM_ENABLE_PROJECTS=clang -DCMAKE_BUILD_TYPE=Release -G "Unix Makefiles" ../llvm || { echo "CMake failed"; return 1; }
  make -j $(expr `nproc` / 2) || { echo "Make failed"; return 1; }
  cd ../../
}

# 병렬로 설치 실행
install_gcc &
GCC_PID=$!

install_clang &
CLANG_PID=$!

wait $GCC_PID || { echo "GCC install failed"; exit 1; }
wait $CLANG_PID || { echo "Clang install failed"; exit 1; }

# 심볼릭 링크
ln -s $HOME/gcc-trunk/bin/gcc-trunk gcc-trunk || { echo "Failed to create symbolic link for gcc-trunk"; exit 1; }
ln -s llvm-project/build/bin/clang-18 clang-18 || { echo "Failed to create symbolic link for clang-18"; exit 1; }


# SSH 키 생성
ssh-keygen -t rsa -b 4096 -f "./BoBpiler" -N "BoBpiler BoBpiler"

# Python requests 모듈 설치
sudo apt-get install -y python3
sudo apt-get install -y python3-pip
pip3 install requests

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


# 크로스 컴파일러와 QEMU 설치 (GCC)
sudo apt-get install -y gcc-aarch64-linux-gnu
sudo apt-get install -y g++-aarch64-linux-gnu

####################################################
# 크로스 컴파일러 설치 (Clang)
#sudo apt-get install -y clang-9-aarch64-linux-gnu
#sudo apt-get install -y clang++-9-aarch64-linux-gnu
####################################################

# QEMU 설치
sudo apt-get install -y qemu-user-static
