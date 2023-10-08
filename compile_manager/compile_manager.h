#pragma once
#include <future>
#include <sstream>
#include <iostream>
#include "pipe_manager.h"

extern "C" {
int py_init_compilers();
const char *py_compile(const char *source_code);
const char *py_exit_compilers();
}

class CompilerManager {
 private:
  std::vector<std::shared_ptr<pipe_manager::PipeManager>> m_compilers;
  std::vector<std::future<std::optional<std::string>>> m_futures;
 public:
  static inline bool is_init = false;
  /**
 * compiler에게 파일명을 전달하고 값을 반환하는 thread{future}
 * @param compiler_manager_ptr
 * @param source_code_path source code path
 * @return
 */
  std::optional<std::string> write_data_thread(const std::shared_ptr<pipe_manager::PipeManager> &compiler_manager_ptr,
                                               std::string source_code_path);
  void set_compilers(std::vector<std::tuple<std::string, std::string>> compilers);
  CompilerManager() = default;

  bool start_compilers();

  std::vector<std::string> compile(std::string source_code);

  std::optional<std::vector<std::string>> exit_compilers();

};

// 전역 compiler 관리 객체
CompilerManager compiler_manager{};
