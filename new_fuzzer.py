import subprocess
import concurrent.futures
import json
from new_config import*
from new_analyzer import*
from new_running_system import*
import logging
import uuid
import threading
import multiprocessing
import time
import signal
import re
import sys
import time



def preprocess_json_string(s):
    s = s.replace("\'", "\"")  # 작은따옴표를 큰따옴표로 교체
    s = re.sub(r',\s*}', '}', s)  # 마지막 , 제거
    return s

class Compiler:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.process = None
        self.compile_time_out = "5\n"
    
    def sync_write_data(self, data:str) :
        self.process.stdin.write(data)
        self.process.stdin.flush()

    def start(self):
        self.process = subprocess.Popen(
            [self.path, "bob.c"], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            text=True
        )
        success = self.fork_handshake()
        if not success:
            print("Handshake failed!")
            exit()

    def compile(self, source_code):
        self.sync_write_data(source_code + "\n")
        line = self.process.stdout.readline()
        processed_line = preprocess_json_string(line)
        return json.loads(processed_line)
    
    def fork_handshake(self) -> bool:
        ret = self.process.stdout.readline()
        if ret not in "fork client hello\n" : 
            print("fork client hello failed")
            return False
        self.sync_write_data("fork server hello\n")
        ret = self.process.stdout.readline()
        if ret not in "done\n" :
            print("fork server hello failed\n")
            return False
        # set timeout
        self.sync_write_data(self.compile_time_out)
        ret = self.process.stdout.readline()
        if "time_out_set" not in ret:
            print("failed to set time out\n")
            return False 
        return True



analyze_queue = multiprocessing.Queue()
error_queue = multiprocessing.Queue()

shutdown_event = threading.Event()

def signal_handler(signum, frame):
    print("Signal received, shutting down")
    shutdown_event.set()
    exit(0)

# 시그널 핸들러 설정
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def analyze_results_thread():
    while not shutdown_event.is_set():
        if not analyze_queue.empty():
            data = analyze_queue.get()
            analyze_results(*data)
        #else:
        #    time.sleep(10)

def fuzzer_init():
    gcc_compiler = Compiler(name="gcc", path="./gcc-trunk")
    clang_compiler = Compiler(name="clang", path="./clang-18")
    compilers = [gcc_compiler, clang_compiler]

    # 컴파일러를 시작
    for compiler in compilers:
        compiler.start() 

    machine_info = get_machine_info()
    analysis_thread = threading.Thread(target=analyze_results_thread, daemon=True)

    analysis_thread.start()

    return (compilers, machine_info, analysis_thread)#, generation_thread)

def save_to_json_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)

def load_from_json_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)
    
if __name__ == "__main__":

    compilers, machine_info, analysis_thread =  fuzzer_init()

    iteration_count = 0  # 반복 횟수를 카운트하기 위한 변수
    codes_to_save = []
    codes_from_file = load_from_json_file("saved_codes.json")

    start_time = time.time()  # 시작 시간 기록
    for code in codes_from_file:
        code_data = code
        generator_name = code_data['generator']
        id = code_data['uuid']
        input_src = code_data['file_path']

        results, error_compilers = compile_and_run(compilers, id, generator_name, input_src)
        if error_compilers: 
            for error_compiler in error_compilers:
                error_compiler.start()
            error_queue.put(code_data)
            continue

        result_data = (generator_name, id, results, machine_info)
        analyze_queue.put(result_data)
        iteration_count += 1
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"{iteration_count} iterations completed in {elapsed_time} seconds.")

