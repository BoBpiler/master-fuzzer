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
import re
import sys
import multiprocessing

sys.path.append('./forkserver_generator')  # 경로 추가
from forkserver_generator import generator as gen_obj


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



analyze_queue = multiprocessing.Queue()
error_queue = multiprocessing.Queue()

# 종료 신호를 처리하기 위한 이벤트 객체 생성
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
        else:
            time.sleep(5)

def generate_codes_thread(csmith_temp_path, yarpgen_temp_path):
    gen_obj.gen_main(csmith_temp_path, yarpgen_temp_path)
            


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
        code_data = gen_obj.code_gen_queue.get()
        generator_name = code_data['generator']
        id = code_data['uuid']
        input_src = code_data['file_path']

        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = []
            results = {}
            error_compilers = []
            for compiler in compilers:
                futures.append(executor.submit(compile_and_run, compiler, id, generator_name, input_src))

            for future in futures:
                binary_path, result_dict, error_compiler = future.result()
                if binary_path:
                    results[binary_path] = result_dict
                if error_compiler:
                    error_compilers.append(error_compiler)
        
        if error_compilers:
            for error_compiler_name in error_compilers:
                # 컴파일러 객체 목록에서 해당 이름을 가진 컴파일러 객체 찾기
                error_compiler_obj = next((compiler for compiler in compilers if compiler.name == error_compiler_name), None)
                if error_compiler_obj:
                    error_compiler_obj.start()
    
        result_data = (generator_name, id, results, machine_info)
        analyze_queue.put(result_data)
    
    #analysis_thread.join()
    #generation_thread.join()