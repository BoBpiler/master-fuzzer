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

echo "Cloning Emscripten..."
git clone https://github.com/emscripten-core/emscripten.git

cd emscripten
emsdk install latest
emsdk activate latest

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

echo "Configuration updated!"
cd ../
