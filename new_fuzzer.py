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

class Compilers_Manager:
    def __init__(self, lib_path='./lib/libcompile_manager.so'):
        self._compiler = ctypes.CDLL(lib_path)
        self._init_ctypes_methods()
        if not self._init_compilers():
            raise Exception("Failed to initialize compilers")
    
    def _init_ctypes_methods(self):
        self._compiler.py_compile.restype = ctypes.c_char_p
        self._compiler.py_exit_compilers.restype = ctypes.c_char_p

    def _init_compilers(self) -> bool:
        returncode = self._compiler.py_init_compilers()
        return returncode == 1
    
    @staticmethod
    def _make_cstring(py_str: str) -> ctypes.c_char_p:
        return ctypes.c_char_p(py_str.encode('utf-8'))

    @staticmethod
    def preprocess_json_string(s: str) -> str:
        s = s.replace("\'", "\"")  # 작은따옴표를 큰따옴표로 교체
        s = re.sub(r',\s*}', '}', s)  # 마지막 , 제거
        s = re.sub(r',\s*]', ']', s)  # 마지막 배열 항목 후의 , 제거
        return s
    
    def compile(self, source_code_path: str) -> str:
        c_string_path = self._make_cstring(source_code_path + "\n")
        results = self._compiler.py_compile(c_string_path).decode('utf-8')
        processed_results = self.preprocess_json_string(results)
        return json.loads(processed_results)

    
    def exit_compilers(self) -> str:
        return self._compiler.py_exit_compilers().decode('utf-8')



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
        else:
            time.sleep(10)

def fuzzer_init():
    compilers = Compilers_Manager()

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
        # if error_compilers: 
        #     for error_compiler in error_compilers:
        #         error_compiler.start()
        #     error_queue.put(code_data)
        #     continue

        result_data = (generator_name, id, results, machine_info)
        analyze_queue.put(result_data)
        iteration_count += 1
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"{iteration_count} iterations completed in {elapsed_time} seconds.")

