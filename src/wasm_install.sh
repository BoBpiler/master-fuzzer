#!/bin/bash

set -e

echo "Installing Wasmer..."
curl https://get.wasmer.io -sSfL | sh

echo "Copying Wasmer binary to /usr/bin..."
sudo cp /$HOME/.wasmer/bin/wasmer /usr/bin/wasmer

echo "Installing Wasmtime..."
curl https://wasmtime.dev/install.sh -sSf | bash

echo "Copying Wasmtime binary to /usr/bin..."
sudo cp /$HOME/.wasmtime/bin/wasmtime /usr/bin/wasmtime

echo "Installing node..."
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash

# nvm 환경 설정 불러오기
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

nvm install node  # 최신 버전 설치
nvm use node  # 최신 버전 사용

# emsdk 설치
git clone https://github.com/emscripten-core/emsdk.git
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
add_to_file_if_not_present ~/.bashrc "source $EMSDK_PATH"
add_to_file_if_not_present ~/.zshrc "source $EMSDK_PATH"

source $EMSDK_PATH
echo "Configuration updated!"
cd ../
