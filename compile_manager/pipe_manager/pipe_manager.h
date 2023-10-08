#pragma once
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>
#include <array>
#include <cstring>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <sstream>

namespace pipe_manager {
extern char** environ;
class PipeManager {
 private:
  pid_t m_child_pid = 0;
  const std::string m_fork_client_hello_msg = "fork client hello\n";
  const std::string m_fork_server_hello_msg = "fork server hello\n";
  const std::string m_fork_handshake_done_msg = "done\n";
  const std::string m_fork_exit_msg = "exit\n";
  const std::string m_forkserver_flag = "bob.c";
  std::string m_time_out_sec = "10\n";
  std::string m_compiler_path;
  std::string m_compiler_name;
  std::array<int,2> m_pipe_in, m_pipe_out, m_pipe_err;
  bool forkserver_handshake();
  bool create_forkserver();


 public:
  std::string get_compiler_name() const;
  /**
 * forkserver compiler 경로를 설정합니다.
 * @param compiler_path
 */
  explicit PipeManager(std::string compiler_name, std::string compiler_path);

  /**
   * 지정한 forkserver compiler를 실행합니다.
   * @return
   */
  bool start_compiler();

  std::optional<std::string> exit_compiler();

  bool write_data(std::string_view data);
  bool read_data(std::string& ret_str);


};
}