import subprocess
import concurrent.futures
import json
from new_config import*
from new_analyzer import*
from new_running_system import*
import logging
import uuid
import threading
import queue
import time
import signal
import re
import sys
import time
import multiprocessing
import ctypes

def preprocess_json_string(s):
    s = s.replace("\'", "\"")  # 작은따옴표를 큰따옴표로 교체
    s = re.sub(r',\s*}', '}', s)  # 마지막 , 제거
    return s

class Compiler:
    def __init__(self, name, path, optimization_option):
        self.name = name
        self.path = path
        self.optimization_option = optimization_option
        self.process = None
        self.compile_time_out = "5\n"
    
    def sync_write_data(self, data:str) :
        self.process.stdin.write(data)
        self.process.stdin.flush()

    def start(self):
        # 여기에서 프로세스를 시작하고 초기화 합니다.
        self.process = subprocess.Popen(
            [self.path, "bob.c", self.optimization_option], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            #stderr=subprocess.PIPE,  # 컴파일 과정에서의 출력 무시
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
        #print("success set time out!")
        return True

optimization_options = ["-O0", "-O1", "-O2", "-O3"] 

def fuzzer_init():
    compilers = [
        Compiler(name=f"gcc_{opt}", path="./gcc-trunk", optimization_option=opt) 
        for opt in optimization_options
    ] + [
        Compiler(name=f"clang_{opt}", path="./clang-18", optimization_option=opt) 
        for opt in optimization_options
    ]

    # 컴파일러를 시작
    for compiler in compilers:
        compiler.start() 

    machine_info = get_machine_info()

    return (compilers, machine_info)#, analysis_thread)#, generation_thread)

def save_to_json_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)

def load_from_json_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)
    
if __name__ == "__main__":

    compilers, machine_info  =  fuzzer_init()

    iteration_count = 0  # 반복 횟수를 카운트하기 위한 변수
    codes_to_save = []
    codes_from_file = load_from_json_file("saved_codes.json")

    start_time = time.time()  # 시작 시간 기록
    for code in codes_from_file:
        code_data = code
        generator_name = code_data['generator']
        id = code_data['uuid']
        input_src = code_data['file_path']
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            results = {}
            error_compilers = []
            for compiler in compilers:
                futures.append(executor.submit(compiler.compile,input_src))

            for future in futures:
                ret = future.result()
                print(ret)
        iteration_count += 1
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"{iteration_count} iterations completed in {elapsed_time} seconds.")

