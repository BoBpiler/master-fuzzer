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
    cd "$current_path/gcc" && git stash && git checkout trunk && git pull || { echo "Failed to update GCC"; return 1; }
    if [ -d build ]; then
      sudo rm -rf build || { echo "Failed to delete existing GCC build directory"; return 1; }
    fi
    if [ -d $HOME/gcc-trunk ]; then
      sudo rm -rf $HOME/gcc-trunk || { echo "Failed to delete existing GCC installation directory"; return 1; }
    fi
    mkdir build && cd build || { echo "Failed to enter build directory"; return 1; }
    ../configure --prefix=$HOME/gcc-trunk \
                 --enable-languages=c,c++ \
                 --disable-multilib \
                 --program-suffix=-trunk \
                 --disable-bootstrap || { echo "Configure failed"; return 1; }
    sudo make -j $(nproc) || { echo "Make failed"; return 1; }
    sudo make install || { echo "Make install failed"; return 1; }
    cd "$current_path"
    [ -L gcc-trunk ] && rm gcc-trunk
    [ -L g++-trunk ] && rm g++-trunk
    ln -s $HOME/gcc-trunk/bin/gcc-trunk gcc-trunk || { echo "Failed to create symbolic link for gcc-trunk"; return 1; }
    ln -s $HOME/gcc-trunk/bin/g++-trunk g++-trunk || { echo "Failed to create symbolic link for g++-trunk"; return 1; }
    echo "GCC successfully updated and rebuilt."
  else
    echo "GCC directory does not exist."
    return 1
  fi
}


# Update and Rebuild RISC-V GCC
update_and_rebuild_riscv_gcc() {
  echo "Updating and rebuilding RISC-V GCC..."
  INSTALL_DIR=$HOME/riscv
  if [ -d "$current_path/riscv-gnu-toolchain" ]; then
    cd "$current_path/riscv-gnu-toolchain" && git stash && git submodule update --init gcc && git pull || { echo "Failed to update RISC-V GCC"; return 1; }
    cd gcc && git stash && git checkout trunk && git pull || { echo "Failed to update RISC-V GCC"; return 1; }
    cd ..
    if [ -d gcc-build ]; then
      sudo rm -rf gcc-build || { echo "Failed to delete existing RISC-V GCC build directory"; return 1; }
    fi

    if [ -d $INSTALL_DIR ]; then
      sudo rm -rf $INSTALL_DIR || { echo "Failed to delete existing RISC-V GCC installation directory"; return 1; }
    fi

    mkdir gcc-build && cd gcc-build || { echo "Failed to enter gcc-build directory"; return 1; }
    ../configure --prefix=$INSTALL_DIR || { echo "Configure failed"; return 1; }
    sudo make -j $(nproc) || { echo "Make failed"; return 1; }
    sudo make install || { echo "Make install failed"; return 1; }
    cd "$current_path"
    [ -L riscv64-unknown-elf-gcc ] && rm riscv64-unknown-elf-gcc
    [ -L riscv64-unknown-elf-g++ ] && rm riscv64-unknown-elf-g++
    ln -s $INSTALL_DIR/bin/riscv64-unknown-elf-gcc riscv64-unknown-elf-gcc || { echo "Failed to create symbolic link for RISC-V GCC"; return 1; }
    ln -s $INSTALL_DIR/bin/riscv64-unknown-elf-g++ riscv64-unknown-elf-g++ || { echo "Failed to create symbolic link for RISC-V G++"; return 1; }
    echo "RISC-V GCC successfully updated and rebuilt."
  else
    echo "RISC-V GCC directory does not exist."
    return 1
  fi
}


# Update and Rebuild LLVM
update_and_rebuild_llvm() {
  echo "Updating and rebuilding LLVM..."
  if [ -d "$current_path/llvm-project" ]; then
    cd "$current_path/llvm-project" && git stash && git checkout main && git pull || { echo "Failed to update LLVM"; return 1; }
    if [ -d build ]; then
      sudo rm -rf build || { echo "Failed to delete existing LLVM build directory"; return 1; }
    fi
    mkdir build && cd build || { echo "Failed to enter build directory"; return 1; }
    cmake -DLLVM_ENABLE_PROJECTS=clang -DCMAKE_BUILD_TYPE=Release -G "Unix Makefiles" ../llvm || { echo "CMake failed"; return 1; }
    sudo make -j $(nproc) || { echo "Make failed"; return 1; }
    cd "$current_path"
    [ -L clang-18 ] && rm clang-18
    [ -L clang++-18 ] && rm clang++-18
    ln -s llvm-project/build/bin/clang-18 clang-18 || { echo "Failed to create symbolic link for clang-18"; return 1; }
    ln -s clang-18 clang++-18 || { echo "Failed to create symbolic link for clang++-18"; return 1; }
    echo "LLVM successfully updated and rebuilt."
  else
    echo "LLVM directory does not exist."
    return 1
  fi
}


# Process user selection and collect results
success_list=""
failure_list=""

for choice in $selection; do
  case $choice in
    1) if update_and_rebuild_gcc; then
         success_list="$success_list GCC"
       else
         failure_list="$failure_list GCC"
       fi
       ;;
    2) if update_and_rebuild_riscv_gcc; then
         success_list="$success_list RISC-V_GCC"
       else
         failure_list="$failure_list RISC-V_GCC"
       fi
       ;;
    3) if update_and_rebuild_llvm; then
         success_list="$success_list LLVM"
       else
         failure_list="$failure_list LLVM"
       fi
       ;;
    *) echo "Invalid choice: $choice";;
  esac
done

# Print summary of results
echo "Update Summary:"
if [ -n "$success_list" ]; then
  # Replace spaces with commas for a cleaner list
  success_list_formatted=$(echo $success_list | sed 's/ /, /g')
  echo "Successfully updated: $success_list_formatted"
fi
if [ -n "$failure_list" ]; then
  # Replace spaces with commas for a cleaner list
  failure_list_formatted=$(echo $failure_list | sed 's/ /, /g')
  echo "Failed to update: $failure_list_formatted"
fi
