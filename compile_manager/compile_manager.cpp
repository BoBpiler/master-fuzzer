#include <iostream>
#include "compile_manager.h"

std::optional<std::string> CompilerManager::write_data_thread(const std::shared_ptr<pipe_manager::PipeManager> &compiler_manager_ptr,
                                                              std::string source_code_path) {
  std::stringstream compiler_name_json;
  bool ret;
  ret = compiler_manager_ptr->write_data(std::move(source_code_path));
  if (!ret) {
    std::cout << "failed to write data\n";
    return {};
  }
  std::string str_buf;
  ret = compiler_manager_ptr->read_data(str_buf);
  if (!ret) {
    std::cout << "Failed to read data\n";
    return {};
  }
  compiler_name_json << "{ ";
  compiler_name_json << "\"compiler\" : " << "\"" << std::move(compiler_manager_ptr->get_compiler_name()) << "\",";
  return compiler_name_json.str() + str_buf + " }";
}

void CompilerManager::set_compilers(std::vector<std::tuple<std::string, std::string>> compilers) {
  for (auto &compiler_data : compilers) {
    m_compilers.push_back(std::make_shared<pipe_manager::PipeManager>(
        std::get<0>(compiler_data)/*compiler_name*/,
        std::get<1>(compiler_data))/*compiler_path*/);
  }
}

bool CompilerManager::start_compilers() {
  bool compiler_ret;
  for (auto &compiler : m_compilers) {
    compiler_ret = compiler->start_compiler();
    if (!compiler_ret) {
      std::cout << "failed to start compiler" << compiler->get_compiler_name() << "\n";
      return false;
    }
  }
  return true;
}

std::vector<std::string> CompilerManager::compile(std::string source_code) {
  for (const auto &compiler : m_compilers) {
    m_futures.push_back(std::async(std::launch::async,
                                   &CompilerManager::write_data_thread, // 멤버 함수 참조
                                   this,                                // 현재 객체의 포인터
                                   compiler,
                                   source_code));
  }

  std::vector<std::string> results;
  for (auto &future : m_futures) {
    auto result = future.get();  // 비동기 작업의 결과를 가져옴
    if (!result.has_value()) {
      std::cout << "failed to get value\n";
      continue;
    }
    results.push_back(*result);
  }
  m_futures.clear(); // clear futures
  return results;
}

std::optional<std::vector<std::string>> CompilerManager::exit_compilers() {
  std::vector<std::string> results;
  for (auto &compiler : m_compilers) {
    auto compiler_ret = compiler->exit_compiler();
    if (!compiler_ret.has_value()) {
      std::cout << "failed to exit compiler" << compiler->get_compiler_name() << "\n";
      return {};
    }
    std::stringstream json_str;
    json_str << "{ \"compiler\" : " << "\"" << compiler->get_compiler_name() << "\", " << *compiler_ret << "}";
    results.push_back(json_str.str());
  }
  return results;
}

//
extern "C" {

int py_init_compilers() {
  if (CompilerManager::is_init) {
    return false;
  }
  char *compiler_names[] = {"gcc", "clang"};
  char *paths[] = {"./gcc-trunk",
                   "./clang-18"};
  char **compilers_param[] = {compiler_names, paths};
  int length = sizeof(compiler_names) / sizeof(compiler_names[0]);

  std::vector<std::tuple<std::string, std::string>> compilers;
  for (int i = 0; i < length; i++) {
    compilers.push_back(std::make_tuple(compilers_param[0][i], compilers_param[1][i]));
  }

  compiler_manager.set_compilers(compilers);
  CompilerManager::is_init = true;
  return compiler_manager.start_compilers();
}

const char *py_compile(const char *source_code) {
  static std::string result;
  result.clear();
  std::stringstream json_str; //정적 지역 변수
  json_str.clear();
  json_str << "[";
  auto ret = compiler_manager.compile(source_code);

  for (auto &d : ret) {
    result += d;
    result += ",\n";
  }
  json_str << result << "]";
  result = json_str.str();
  return result.c_str();
}

const char *py_exit_compilers() {
  static std::string result;
  result.clear();
  std::stringstream json_str; //정적 지역 변수
  json_str.clear();
  json_str << "[";

  auto str = compiler_manager.exit_compilers();

  if (!str.has_value()) {
    result = "forkserver Internal Error";
    std::cout << result << "\n";
    return result.c_str();
  }

  for (auto &s : *str) {
    result += s;
    result += ",\n";
  }
  json_str << result << "]";
  result = json_str.str();
  return result.c_str();
}

}

//int main() {
//  char *compiler_names[] = {"gcc", "clang"};
//  char *paths[] = {"/home/dong/gcc-trunk/bin/gcc-trunk",
//                   "/home/dongFiles/compiler_trunk/llvm-project/build/bin/clang-18"};  // "path"는 실제 경로로 대체해야 합니다.
//  char **compilers[] = {compiler_names, paths};
//  auto ret1 = py_init_compilers();
//  if(!ret1) {
//    std::cout << "error\n";
//  }
//  std::cout << "success\n";
//  auto ret = py_compile("/home/dong/Downloads/fork_test/profileing/BoBpiler-fuzzer/compile_manager/uuid0/hello0.c\n");
//  std::cout << ret << "\n";
//
//  auto ret2 = py_compile("/home/dong/Downloads/fork_test/profileing/BoBpiler-fuzzer/compile_manager/uuid1/hello1.c\n");
//  std::cout << ret2 << "\n";
//  auto ret3 = py_exit_compilers();
//  std::cout << ret3 << "\n";
//}