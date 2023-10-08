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
import ctypes

sys.path.append('./forkserver_generator')  # 경로 추가
from forkserver_generator import generator as gen_obj


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
        c_string_path = self._make_cstring(source_code_path)
        results = self._compiler.py_compile(c_string_path).decode('utf-8')
        processed_results = self.preprocess_json_string(results)
        return json.loads(processed_results)

    
    def exit_compilers(self) -> str:
        return self._compiler.py_exit_compilers().decode('utf-8')



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
            

def fuzzer_init():
    compilers = Compilers_Manager()
    
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

        results, error_compilers = compile_and_run(compilers, id, generator_name, input_src)
        # if error_compilers: 
        #     for error_compiler in error_compilers:
        #         error_compiler.start()
        #     error_queue.put(code_data)
        #     continue

        result_data = (generator_name, id, results, machine_info)
        analyze_queue.put(result_data)
    
    #analysis_thread.join()
    #generation_thread.join()