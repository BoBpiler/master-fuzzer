#!/bin/sh

current_path=$PWD

# Check if script is run as root
if [ "$(id -u)" != "0" ]; then
    echo "This script requires superuser access for some operations."
    echo "Please run with 'sudo' when prompted."
fi

echo "Select the projects you want to update and rebuild:"
echo "  1) GCC"
echo "  2) RISC-V GCC"
echo "  3) LLVM"
read -p "Enter the numbers (e.g. 1 2 3): " selection

# Update and Rebuild GCC
update_and_rebuild_gcc() {
  echo "Updating and rebuilding GCC..."
  if [ -d "$current_path/gcc" ]; then
    cd "$current_path/gcc"
    git stash
    git pull || { echo "Failed to update GCC"; return 1; }
    [ -d build ] && sudo rm -rf build
    [ -d $HOME/gcc-trunk ] && sudo rm -rf $HOME/gcc-trunk
    mkdir build && cd build || { echo "Failed to enter build directory"; return 1; }
    ../configure --prefix=$HOME/gcc-trunk \
               --enable-languages=c,c++ \
               --disable-multilib \
               --program-suffix=-trunk \
               --disable-bootstrap || { echo "Configure failed"; return 1; }
    make -j $(nproc) || { echo "Make failed"; return 1; }
    sudo make install
    cd "$current_path"
    [ -L gcc-trunk ] && rm gcc-trunk
    [ -L g++-trunk ] && rm g++-trunk
    ln -s $HOME/gcc-trunk/bin/gcc-trunk gcc-trunk || { echo "Failed to create symbolic link for gcc-trunk"; exit 1; }
    ln -s $HOME/gcc-trunk/bin/g++-trunk g++-trunk || { echo "Failed to create symbolic link for g++-trunk"; exit 1; }
  else
    echo "GCC directory does not exist."
  fi
}

# Update and Rebuild RISC-V GCC
update_and_rebuild_riscv_gcc() {
  echo "Updating and rebuilding RISC-V GCC..."
  INSTALL_DIR=$HOME/riscv
  if [ -d "$current_path/riscv-gnu-toolchain" ]; then
    cd "$current_path/riscv-gnu-toolchain"
    git stash
    git submodule update --init gcc
    git pull || { echo "Failed to update RISC-V GCC"; return 1; }
    cd gcc
    git stash
    git pull || { echo "Failed to update RISC-V GCC"; return 1; }
    cd ..
    [ -d gcc-build ] && sudo rm -rf gcc-build
    [ -d $INSTALL_DIR ] && sudo rm -rf $INSTALL_DIR
    mkdir gcc-build && cd gcc-build
    ../configure --prefix=$INSTALL_DIR || { echo "Configure failed"; return 1; }
    make -j $(nproc) || { echo "Make failed"; return 1; }
    make install || { echo "Make install failed"; return 1; }
    cd "$current_path"
    [ -L riscv64-unknown-elf-gcc ] && rm riscv64-unknown-elf-gcc
    [ -L riscv64-unknown-elf-g++ ] && rm riscv64-unknown-elf-g++
    ln -s $INSTALL_DIR/bin/riscv64-unknown-elf-gcc riscv64-unknown-elf-gcc || { echo "Failed to create symbolic link for RISC-V GCC"; exit 1; }
    ln -s $INSTALL_DIR/bin/riscv64-unknown-elf-g++ riscv64-unknown-elf-g++ || { echo "Failed to create symbolic link for RISC-V G++"; exit 1; }
  else
    echo "RISC-V GCC directory does not exist."
  fi
}

# Update and Rebuild LLVM
update_and_rebuild_llvm() {
  echo "Updating and rebuilding LLVM..."
  if [ -d "$current_path/llvm-project" ]; then
    cd "$current_path/llvm-project"
    git stash
    git pull || { echo "Failed to update LLVM"; return 1; }
    [ -d build ] && sudo rm -rf build
    mkdir build && cd build || { echo "Failed to enter build directory"; return 1; }
    cmake -DLLVM_ENABLE_PROJECTS=clang -DCMAKE_BUILD_TYPE=Release -G "Unix Makefiles" ../llvm || { echo "CMake failed"; return 1; }
    make -j $(nproc) || { echo "Make failed"; return 1; }
    cd "$current_path"
    [ -L clang-18 ] && rm clang-18
    [ -L clang++-18 ] && rm clang++-18
    ln -s llvm-project/build/bin/clang-18 clang-18 || { echo "Failed to create symbolic link for clang-18"; exit 1; }
    ln -s clang-18 clang++-18 || { echo "Failed to create symbolic link for clang++-18"; exit 1; }
  else
    echo "LLVM directory does not exist."
  fi
}

# Process user selection
for choice in $selection; do
  case $choice in
  1) update_and_rebuild_gcc;;
  2) update_and_rebuild_riscv_gcc;;
  3) update_and_rebuild_llvm;;
  *) echo "Invalid choice: $choice";;
  esac
done
