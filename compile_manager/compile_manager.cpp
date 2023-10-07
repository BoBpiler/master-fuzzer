#include <iostream>
#include "compile_manager.h"
#include "pipe_manager.h"

int main() {
  pipe_manager::PipeManager gcc_compiler_manager{"/home/dong/gcc-trunk/bin/gcc-trunk"};
  bool compiler_ret = gcc_compiler_manager.start_compiler();
  if (!compiler_ret) {
    std::cout << "failed to start compiler\n";
  }
  compiler_ret = gcc_compiler_manager.write_data("/home/dong/Downloads/fork_test/profileing/BoBpiler-fuzzer/compile_manager/build/uuid0/hello.c\n");
  if(!compiler_ret) {
    std::cout << "failed to write data\n";
  }
  compiler_ret = gcc_compiler_manager.exit_compiler();
  if(!compiler_ret) {
    std::cout << "failed to exit compiler\n";
  }
}