#!/bin/sh

current_path=$PWD

# Check if script is run as root
if [ "$(id -u)" != "0" ]; then
    echo "This script requires superuser access."
    echo "Please run with 'sudo'."
    exit 1
fi

if [ ! -z "$SUDO_USER" ]; then
    # SUDO_USER가 설정되어 있으면, 원래 사용자의 홈 디렉토리를 찾습니다.
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    # SUDO_USER가 설정되어 있지 않으면, 현재 환경의 HOME을 사용합니다.
    USER_HOME=$HOME
fi


# 메뉴 선택 부분
echo "Select the packages you want to install:"
echo "0) Install all"
echo "Compilers"
echo "  1) GCC"
echo "  2) Clang"
echo "  3) RISC-V GCC"
echo "  4) Mac OsxCross (darling and osxcross)"
echo "  5) Cross compilers"
echo "Code Generators"
echo "  6) Csmith"
echo "  7) YARPGEN"
echo "  8) YARPGEN_SCALAR"
echo "Wasm Dependencies"
echo "  9) Wasmer"
echo "  10) Wasmtime"
echo "  11) node"
echo "  12) emsdk"
echo "  13) wasienv"
echo "Utility"
echo "  14) QEMU"
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
  ../configure --prefix=$USER_HOME/gcc-trunk \
               --enable-languages=c,c++ \
               --disable-multilib \
               --program-suffix=-trunk \
               --disable-bootstrap || { echo "Configure failed"; return 1; }
  make -j 4 || { echo "Make failed"; return 1; }
  make install
  cd "$current_path"
  ln -s $USER_HOME/gcc-trunk/bin/gcc-trunk gcc-trunk || { echo "Failed to create symbolic link for gcc-trunk"; exit 1; }
  ln -s $USER_HOME/gcc-trunk/bin/g++-trunk g++-trunk || { echo "Failed to create symbolic link for gcc-trunk"; exit 1; }
}

# Clang 설치
install_clang() {
  git clone https://github.com/llvm/llvm-project.git || { echo "Failed to clone llvm-project"; return 1; }
  cd llvm-project || { echo "Failed to enter llvm-project directory"; return 1; }
  git checkout main || { echo "Failed to checkout main"; return 1; }
  mkdir build && cd build || { echo "Failed to enter build directory"; return 1; }
  cmake -DLLVM_ENABLE_PROJECTS=clang -DCMAKE_BUILD_TYPE=Release -G "Unix Makefiles" ../llvm || { echo "CMake failed"; return 1; }
  make -j 4 || { echo "Make failed"; return 1; }
  cd "$current_path"
  ln -s llvm-project/build/bin/clang-18 clang-18 || { echo "Failed to create symbolic link for clang-18"; exit 1; }
  ln -s clang-18 clang++-18 || { echo "Failed to create symbolic link for clang++-18"; exit 1; }
}

install_riscv_gcc() {
  # 설치 디렉터리 설정
  INSTALL_DIR=$USER_HOME/riscv

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


# 시스템 아키텍처 확인 함수
check_architecture() {
    local arch
    arch=$(uname -m)
    case $arch in
        x86_64)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Darling 설치 함수
install_darling() {
    echo "Building Darling from source for all architectures..."
    sudo apt install -y libbz2-dev cmake automake clang-15 bison flex libfuse-dev libudev-dev pkg-config libc6-dev-i386 gcc-multilib libcairo2-dev libgl1-mesa-dev curl libglu1-mesa-dev libtiff5-dev libfreetype6-dev git git-lfs libelf-dev libxml2-dev libegl1-mesa-dev libfontconfig1-dev libbsd-dev libxrandr-dev libxcursor-dev libgif-dev libavutil-dev libpulse-dev libavformat-dev libavcodec-dev libswresample-dev libdbus-1-dev libxkbfile-dev libssl-dev libstdc++-12-dev git-lfs python2 python3
    git clone --recursive https://github.com/darlinghq/darling.git
    cd darling
    git lfs install
    git pull
    git submodule update --init --recursive
    tools/uninstall
    mkdir build && cd build
    cmake ..
    make -j 8
    sudo make install
    sudo chmod +s src/startup/darling
    sudo cp src/startup/darling /usr/local/bin/
    sudo cp src/startup/darling /usr/bin/
    sudo chmod +s /usr/local/bin/darling
    sudo chmod +s /usr/bin/darling
    cd ../../
}

# Darling과 OsxCross 설치 함수
install_darling_and_osxcross() {
    # 필요한 패키지들을 업데이트하고 설치합니다.
    sudo apt-get update
    sudo apt-get install -y clang cmake git patch python3 python2 git-lfs libssl-dev lzma-dev libxml2-dev xz-utils bzip2 cpio zlib1g-dev libbz2-dev

    # Darling 설치
    # wget https://github.com/darlinghq/darling/releases/download/v0.1.20230310_update_sources_11_5/darling_0.1.20230310.jammy_amd64.deb
    # sudo apt install ./darling_0.1.20220704.focal_amd64.deb
    install_darling

    # OsxCross 저장소 클론 및 설치
    git clone https://github.com/tpoechtrager/osxcross.git
    mv MacOSX14.0.sdk.tar.xz osxcross/tarballs/MacOSX14.0.sdk.tar.xz
    cd osxcross
    # cd osxcross/tools

    # # Xcode와 필요한 SDK 다운로드 및 패키징
    # wget https://download.developer.apple.com/Developer_Tools/Xcode_15_beta_6/Xcode_15_beta_6.xip
    # ./gen_sdk_package_pbzx.sh $PWD/Xcode_15_beta_6.xip
    # cd ../

    # # 패키징된 SDK를 tarballs 디렉토리로 이동
    # mv MacOSX14.0.sdk.tar.xz tarballs/MacOSX14.0.sdk.tar.xz
    # mv MacOSX14.sdk.tar.xz tarballs/MacOSX14.sdk.tar.xz

    # SDK 버전 설정 및 OsxCross 빌드
    export SDK_VERSION=14.0
    ./build.sh

    # PATH 환경 변수에 OsxCross의 bin 디렉토리 추가
    echo "export PATH=\$PATH:$PWD/target/bin" >> ~/.bashrc
    echo "export PATH=\$PATH:$PWD/target/bin" >> ~/.zshrc

    # .bashrc 및 .zshrc 재로드
    . ~/.bashrc
    . ~/.zshrc
    cd ../
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
    sudo cp "$USER_HOME/.wasmer/bin/wasmer" /usr/bin/wasmer
}

# wasmtime 설치 
install_wasmtime() {
    echo "Installing Wasmtime..."
    curl https://wasmtime.dev/install.sh -sSf | bash

    echo "Copying Wasmtime binary to /usr/bin..."
    sudo cp "$USER_HOME/.wasmtime/bin/wasmtime" /usr/bin/wasmtime
}

# node 설치
install_node_with_nvm() {
    echo "Installing node..."
    if [ ! -d "$USER_HOME/.nvm" ]; then
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
    else
        echo "nvm already installed!"
    fi

    # nvm 환경 설정 불러오기
    export NVM_DIR="$USER_HOME/.nvm"
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
    sudo ./emsdk install latest
    sudo ./emsdk activate latest

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

# wasienv 설치
install_wasienv() {
    local WASIENV_DIR="$USER_HOME/.wasienv"

    echo "Installing wasienv..."

    if [ ! -d "$WASIENV_DIR" ]; then
        curl -L https://github.com/wasienv/wasienv/raw/master/install.sh | sh
    else
        echo "wasienv already installed!"
    fi

    # Copy binaries
    if [ -d "$WASIENV_DIR/local/bin" ]; then
        sudo cp "$WASIENV_DIR/local/bin/"* /usr/bin/
    else
        echo "Error: $WASIENV_DIR/local/bin does not exist."
        return 1
    fi

    wasienv install-sdk 7 
    wasienv install-sdk unstable
}

for choice in $selection; do
  case $choice in
  0) 
      install_gcc
      install_clang
      install_riscv_gcc
      install_darling_and_osxcross
      install_cross_compilers
      install_csmith
      install_yarpgen
      install_yarpgen_scalar
      install_wasmer
      install_wasmtime
      install_node_with_nvm
      install_emsdk
      install_wasienv
      install_qemu
      break
      ;;
  1) install_gcc;;
  2) install_clang;;
  3) install_riscv_gcc;;
  4) install_darling_and_osxcross;;
  5) install_cross_compilers;;
  6) install_csmith;;
  7) install_yarpgen;;
  8) install_yarpgen_scalar;;
  9) install_wasmer;;
  10) install_wasmtime;;
  11) install_node_with_nvm;;
  12) install_emsdk;;
  13) install_wasienv;;
  14) install_qemu;;
  *) echo "Invalid choice: $choice";;
  esac
done
