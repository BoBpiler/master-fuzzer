#include "pipe_manager.h"

namespace pipe_manager {

bool PipeManager::write_data(std::string_view data) {
  auto written_bytes = write(m_pipe_in[1], data.data(), data.length());
  if(written_bytes == -1) {
    perror("write");
    return false;
  }
  return true;
}

bool PipeManager::read_data(std::string &ret_str) {
  constexpr size_t buf_size = 1024;
  std::vector<char> buf(buf_size);

  ssize_t len = read(m_pipe_out[0], buf.data(), buf.size() - 1);

  if (len == -1) {
    return false;
  }

  if (len > 0) {
    buf[len] = '\0';
    ret_str = buf.data();
    return true;
  }
  return false;
}
bool PipeManager::start_compiler() {
  bool ret;
  ret = create_forkserver();
  if(!ret) {
    std::cout << "failed to create forkserver\n";
    return false;
  }
  ret = forkserver_handshake();
  if(!ret) {
    std::cout << "Failed to forkserver handshake()\n";
    return false;
  }
  return true;
}

PipeManager::PipeManager(std::string &&compiler_path) : m_compiler_path(compiler_path) {}

bool PipeManager::forkserver_handshake() {
  // Read fork client hello
  bool ret;
  std::string str_buf;
  ret = read_data(str_buf);
  if(!ret) {
    std::cout << "Failed to read data\n";
    return false;
  }
  if(str_buf != m_fork_client_hello_msg) {
    std::cout << "Failed to fork client hello\n";
    return false;
  }

  // Write fork server hello
  ret = write_data(m_fork_server_hello_msg);
  if(!ret) {
    std::cout << "Failed to write data" << m_fork_server_hello_msg;
    return false;
  }

  // Read Done
  ret = read_data(str_buf);
  if(!ret) {
    std::cout << "Failed to fork server hello\n";
    return false;
  }

  if(str_buf != m_fork_handshake_done_msg) {
    std::cout << "Failed to done\n";
    return false;
  }

  // Set Time Out
  ret = write_data(m_time_out_sec);
  if(!ret) {
    std::cout << "Failed to write data" << m_time_out_sec;
    return false;
  }

  // Read Done
  ret = read_data(str_buf);
  if(!ret) {
    std::cout << "Failed to set time out\n";
    return false;
  }

  std::cout << str_buf << "\n";
  return true;
}

bool PipeManager::create_forkserver() {
  if (pipe(m_pipe_in.data()) == -1 || pipe(m_pipe_out.data()) == -1) { //|| pipe(pipe_err) == -1) {
    perror("pipe");
    return false;
  }
  m_child_pid = fork();
  if (m_child_pid == -1) {
    perror("fork");
    return false;
  }

  if (m_child_pid == 0) {    // Child Process
    close(m_pipe_in[1]);
    close(m_pipe_out[0]);
    //close(pipe_err[0]);

    // Redirecting standard input, output and error
    dup2(m_pipe_in[0], STDIN_FILENO);
    dup2(m_pipe_out[1], STDOUT_FILENO);
    //dup2(pipe_err[1], STDERR_FILENO);

    close(m_pipe_in[0]);
    close(m_pipe_out[1]);
    //close(pipe_err[1]);

    char
        *argv[] = {const_cast<char *>(m_compiler_path.c_str()), const_cast<char *>(m_forkserver_flag.c_str()), nullptr};
    if (execve(argv[0], argv, ::environ) == -1) {
      perror("execve");
      exit(EXIT_FAILURE);
    }
  } else {            // Parent Process
    close(m_pipe_in[0]);
    close(m_pipe_out[1]);

    return true;
    /*
    // Write data to child's standard input

    close(pipe_err[1]);
    close(m_pipe_in[1]);
    close(m_pipe_out[0]);


    wait(nullptr);
     */
  }
}
bool PipeManager::exit_compiler() {
  bool ret = write_data(m_fork_exit_msg);
  if(!ret) {
    std::cout << "Failed to write " << m_fork_exit_msg;
    return false;
  }
  std::string str_buf;
  ret = read_data(str_buf);
  if(!ret) {
    std::cout << "Failed to read data\n";
    return false;
  }
  std::cout << str_buf << "\n";

  //close(pipe_err[1]);
  close(m_pipe_in[1]);
  close(m_pipe_out[0]);
  int status;

  auto pid = waitpid(m_child_pid, &status, 0);
  if(pid == -1) {
    perror("waitpid");
    return false;
  }
  std::cout << "pid " << pid << " status : " << status << "\n";
  return true;
}

}