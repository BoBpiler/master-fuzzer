#!/bin/bash

# GCC를 업데이트하는 함수
update_gcc() {
  cd gcc || { echo "Failed to change directory to gcc. Exiting."; exit 1; }

  git pull origin trunk || { echo "Failed to pull from GCC repository. Exiting."; exit 1; }

  cd build || { echo "Failed to change directory to gcc/build. Exiting."; exit 1; }

  make -j $(expr `nproc` / 2) || { echo "Failed to build GCC. Exiting."; exit 1; }

  make install

  cd ../..
}

# Clang을 업데이트하는 함수
update_clang() {
  cd llvm-project || { echo "Failed to change directory to llvm-project. Exiting."; exit 1; }

  git pull origin llvmorg-18-init || { echo "Failed to pull from LLVM repository. Exiting."; exit 1; }

  cd build || { echo "Failed to change directory to llvm-project/build. Exiting."; exit 1; }

  make -j $(expr `nproc` / 2) || { echo "Failed to build Clang. Exiting."; exit 1; }

  cd ../..
}

# 병렬로 업데이트 실행
update_gcc &
GCC_PID=$!

update_clang &
CLANG_PID=$!

# 두 업데이트 작업이 완료될 때까지 대기
wait $GCC_PID $CLANG_PID

# 병렬 실행이 끝난 후 기존의 심볼릭 링크를 삭제하고 새로 만듦
rm -f gcc-trunk
ln -s $HOME/gcc-trunk/bin/gcc-trunk gcc-trunk

rm -f clang-18
ln -s llvm-project/build/bin/clang-18 clang-18

# fuzzer 실행
python3 fuzzer.py



