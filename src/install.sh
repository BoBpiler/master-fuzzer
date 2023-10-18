#!/bin/sh

current_path=$PWD

# Check if script is run as root
if [ "$(id -u)" != "0" ]; then
    echo "This script requires superuser access."
    echo "Please run with 'sudo'."
    exit 1
fi

# 메뉴 선택 부분
echo "Select the packages you want to install:"
echo "0) Install all"
echo "Compilers"
echo "  1) GCC"
echo "  2) Clang"
echo "  3) RISC-V GCC"
echo "  4) Cross compilers"
echo "Code Generators"
echo "  5) Csmith"
echo "  6) YARPGEN"
echo "  7) YARPGEN_SCALAR"
echo "Wasm Dependencies"
echo "  8) Wasmer"
echo "  9) Wasmtime"
echo "  10) node"
echo "  11) emsdk"
echo "Utility"
echo "  12) QEMU"
read -p "Enter the numbers (e.g. 1 2 3 or 0 for all): " selection

# 필수 패키지 업데이트
sudo apt-get update || { echo "Failed to update packages"; exit 1; }

# 필수 패키지 설치
sudo apt-get install -y autoconf automake autotools-dev curl python3 python3-pip libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev ninja-build git cmake libglib2.0-dev || { echo "Failed to install dependencies"; exit 1; }
pip3 install requests psutil

# SSH 키 생성
ssh-keygen -t rsa -b 4096 -f "./BoBpiler" -N "BoBpiler BoBpiler"



# 함수 정의 부분
# GCC 설치
install_gcc() {
  git clone https://github.com/gcc-mirror/gcc.git || { echo "Failed to clone gcc"; return 1; }
  cd gcc || { echo "Failed to enter gcc directory"; return 1; }
  git checkout trunk || { echo "Failed to checkout trunk"; return 1; }
  sudo apt install -y gnat libmpfr-dev libmpfr-doc libgmp-dev libmpc3 libmpc-dev flex g++-multilib || { echo "Failed to install dependencies"; return 1; }
  contrib/download_prerequisites || { echo "Failed to download prerequisites"; return 1; }
  mkdir build && cd build || { echo "Failed to enter build directory"; return 1; }
  ../configure --prefix=$HOME/gcc-trunk \
               --enable-languages=c,c++ \
               --disable-multilib \
               --program-suffix=-trunk \
               --disable-bootstrap || { echo "Configure failed"; return 1; }
  make -j 4 || { echo "Make failed"; return 1; }
  make install
  cd "$current_path"
  ln -s $HOME/gcc-trunk/bin/gcc-trunk gcc-trunk || { echo "Failed to create symbolic link for gcc-trunk"; exit 1; }
  ln -s $HOME/gcc-trunk/bin/g++-trunk g++-trunk || { echo "Failed to create symbolic link for gcc-trunk"; exit 1; }
}

# Clang 설치
install_clang() {
  git clone https://github.com/llvm/llvm-project.git || { echo "Failed to clone llvm-project"; return 1; }
  cd llvm-project || { echo "Failed to enter llvm-project directory"; return 1; }
  git checkout llvmorg-18-init || { echo "Failed to checkout llvmorg-18-init"; return 1; }
  mkdir build && cd build || { echo "Failed to enter build directory"; return 1; }
  cmake -DLLVM_ENABLE_PROJECTS=clang -DCMAKE_BUILD_TYPE=Release -G "Unix Makefiles" ../llvm || { echo "CMake failed"; return 1; }
  make -j 4 || { echo "Make failed"; return 1; }
  cd "$current_path"
  ln -s llvm-project/build/bin/clang-18 clang-18 || { echo "Failed to create symbolic link for clang-18"; exit 1; }
  ln -s clang-18 clang++-18 || { echo "Failed to create symbolic link for clang++-18"; exit 1; }
}

install_riscv_gcc() {
  # 설치 디렉터리 설정
  INSTALL_DIR=$HOME/riscv

  git clone https://github.com/riscv/riscv-gnu-toolchain || { echo "Failed to clone riscv-gnu-toolchain"; return 1; }
  cd riscv-gnu-toolchain || { echo "Failed to enter riscv-gnu-toolchain directory"; return 1; }
  git submodule update --init gcc

  # 원하는 브랜치로 체크아웃
  cd gcc && git checkout trunk || { echo "Failed to checkout gcc trunk"; return 1; }
  cd "$current_path"

  cd riscv-gnu-toolchain
  mkdir gcc-build && cd gcc-build
  ../configure --prefix=$INSTALL_DIR || { echo "Configure failed"; return 1; }
  make -j 2 || { echo "Make failed"; return 1; }
  make install || { echo "Make install failed"; return 1; }
  cd "$current_path"

  # 심볼릭 링크 생성
  ln -s $INSTALL_DIR/bin/riscv64-unknown-elf-gcc $current_path/riscv64-unknown-elf-gcc || { echo "Failed to create symbolic link for RISC-V GCC"; exit 1; }
  ln -s $INSTALL_DIR/bin/riscv64-unknown-elf-g++ $current_path/riscv64-unknown-elf-g++ || { echo "Failed to create symbolic link for RISC-V G++"; exit 1; }

}

# Csmith 설치 스크립트
install_csmith() {
  git clone https://github.com/csmith-project/csmith.git
  cd csmith
  sudo apt install -y g++ cmake m4
  cmake -DCMAKE_INSTALL_PREFIX=/usr/local .
  sudo make -j `nproc` && sudo make install
  cd "$current_path"
}

# YARPGEN 설치 스크립트
install_yarpgen() {
  git clone https://github.com/BoBpiler/BoBpiler_yarpgen.git
  cd BoBpiler_yarpgen
  mkdir build
  cd build
  cmake ..
  sudo make -j `nproc`
  sudo cp yarpgen /usr/local/bin/
  cd "$current_path"
}

# YARPGEN_SCALAR 설치 스크립트
install_yarpgen_scalar() {
  git clone https://github.com/intel/yarpgen.git
  cd yarpgen
  git checkout v1
  mkdir build
  cd build
  cmake ..
  sudo make -j `nproc`
  sudo cp yarpgen /usr/local/bin/yarpgen_scalar
  cd "$current_path"
}

# qemu 설치 스크립트
install_qemu() {
    sudo apt-get install -y qemu-user-static
}

# 크로스 컴파일러 설치 (GCC)
install_cross_compilers() {
  sudo apt-get install -y gcc-aarch64-linux-gnu g++-aarch64-linux-gnu
  sudo apt-get install -y gcc-mips64-linux-gnuabi64 g++-mips64-linux-gnuabi64
  sudo apt-get install -y gcc-mips64el-linux-gnuabi64 g++-mips64el-linux-gnuabi64
  sudo apt-get install -y gcc-powerpc64le-linux-gnu g++-powerpc64le-linux-gnu
  sudo apt-get install -y gcc-powerpc64-linux-gnu g++-powerpc64-linux-gnu
  sudo apt-get install -y gcc-s390x-linux-gnu g++-s390x-linux-gnu
  sudo apt-get install -y gcc-sparc64-linux-gnu g++-sparc64-linux-gnu
}

# wasmer 설치 
install_wasmer() {
    echo "Installing Wasmer..."
    curl https://get.wasmer.io -sSfL | sh

    echo "Copying Wasmer binary to /usr/bin..."
    sudo cp "$HOME/.wasmer/bin/wasmer" /usr/bin/wasmer
}

# wasmtime 설치 
install_wasmtime() {
    echo "Installing Wasmtime..."
    curl https://wasmtime.dev/install.sh -sSf | bash

    echo "Copying Wasmtime binary to /usr/bin..."
    sudo cp "$HOME/.wasmtime/bin/wasmtime" /usr/bin/wasmtime
}

# node 설치
install_node_with_nvm() {
    echo "Installing node..."
    if [ ! -d "$HOME/.nvm" ]; then
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
    else
        echo "nvm already installed!"
    fi

    # nvm 환경 설정 불러오기
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

    nvm install node  # 최신 버전 설치
    nvm use node  # 최신 버전 사용
}

# emsdk ,emscripten 설치
install_emsdk() {
    # emsdk 설치
    if [ ! -d "emsdk" ]; then
        git clone https://github.com/emscripten-core/emsdk.git
    fi
    cd emsdk

    # 최신 버전의 Emscripten 툴체인 설치 및 활성화
    ./emsdk install latest
    ./emsdk activate latest

    # 환경 설정
    EMSDK_PATH="$(pwd)/emsdk_env.sh"

    add_to_file_if_not_present() {
        local file="$1"
        local line="$2"

        # 파일이 존재하고 해당 라인이 파일에 없다면 추가
        if [ -f "$file" ] && ! grep -Fxq "$line" "$file"; then
            echo "$line" >> "$file"
        fi
    }

    # .bashrc와 .zshrc에 내용 추가
    add_to_file_if_not_present ~/.bashrc ". $EMSDK_PATH"
    add_to_file_if_not_present ~/.zshrc ". $EMSDK_PATH"

    . $EMSDK_PATH
    echo "Configuration updated!"
    cd ../
}

for choice in $selection; do
  case $choice in
  0) 
      install_gcc
      install_clang
      install_riscv_gcc
      install_cross_compilers
      install_csmith
      install_yarpgen
      install_yarpgen_scalar
      install_wasmer
      install_wasmtime
      install_node_with_nvm
      install_emsdk
      install_qemu
      break
      ;;
  1) install_gcc;;
  2) install_clang;;
  3) install_riscv_gcc;;
  4) install_cross_compilers;;
  5) install_csmith;;
  6) install_yarpgen;;
  7) install_yarpgen_scalar;;
  8) install_wasmer;;
  9) install_wasmtime;;
  10) install_node_with_nvm;;
  11) install_emsdk;;
  12) install_qemu;;
  *) echo "Invalid choice: $choice";;
  esac
done
