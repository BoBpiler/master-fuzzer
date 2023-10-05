import subprocess
import concurrent.futures
import json
from config import*
from analyzer import*
from running_system import*
import logging
import uuid
import threading
import queue
import time
import signal
from forkserver_generator import generator as g
import re

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
        # 여기에서 프로세스를 시작하고 초기화 합니다.
        self.process = subprocess.Popen(
            [self.path, "bob.c"], 
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



analyze_queue = queue.Queue()

# 종료 신호를 처리하기 위한 이벤트 객체 생성
shutdown_event = threading.Event()

def signal_handler(signum, frame):
    print("Signal received, shutting down")
    shutdown_event.set()

# 시그널 핸들러 설정
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def analyze_results_thread():
    while not shutdown_event.is_set():
        if not analyze_queue.empty():
            data = analyze_queue.get()
            analyze_results(*data)
        else:
            time.sleep(5)

def generate_codes_thread(csmith_temp_path, yarpgen_temp_path):
    g.gen_main(csmith_temp_path, yarpgen_temp_path)
            

def fuzzer_init():
    gcc_compiler = Compiler(name="gcc", path="./gcc-trunk")
    clang_compiler = Compiler(name="clang", path="./clang-18")
    compilers = [gcc_compiler, clang_compiler]

    # 컴파일러를 시작
    for compiler in compilers:
        compiler.start() 
    
    csmith_temp_path = get_absolute_temp_path('csmith')
    yarpgen_temp_path = get_absolute_temp_path('yarpgen')
    setup_output_dirs(generators)
    machine_info = get_machine_info()
    analysis_thread = threading.Thread(target=analyze_results_thread, daemon=True)
    generation_thread = threading.Thread(target=generate_codes_thread, args=(csmith_temp_path, yarpgen_temp_path), daemon=True)

    generation_thread.start()
    analysis_thread.start()

    return (compilers, machine_info, analysis_thread, generation_thread)


if __name__ == "__main__":

    compilers, machine_info, analysis_thread, generation_thread =  fuzzer_init()

    while True:
        code_data = g.code_gen_queue.get()
        generator_name = code_data['generator']
        id = code_data['uuid']
        input_src = code_data['file_path']
        results = compile_and_run(compilers, id, generator_name, input_src)
        result_data = (generator_name, id, results, machine_info)
        analyze_queue.put(result_data)
    
    #analysis_thread.join()
    #generation_thread.join()