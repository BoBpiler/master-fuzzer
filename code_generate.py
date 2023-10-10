import json
from generate_config import*
import threading
import multiprocessing
import sys
import os
import signal
import shutil
import time
sys.path.append('./forkserver_generator')  # 경로 추가
from forkserver_generator import generator as gen_obj


def generate_codes_process(csmith_temp_path, yarpgen_temp_path):
    gen_obj.gen_main(csmith_temp_path, yarpgen_temp_path)

def fuzzer_init(generator_choice):
    csmith_temp_path = None if generator_choice == 'yarpgen' else get_absolute_temp_path('csmith')
    yarpgen_temp_path = None if generator_choice == 'csmith' else get_absolute_temp_path('yarpgen')
    setup_output_dirs(generators)
    process = multiprocessing.Process(target=generate_codes_process, args=(csmith_temp_path, yarpgen_temp_path))
    process.start()
    os.setpgid(process.pid, process.pid)
    return process

def load_from_json_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)
    
def save_to_json_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)

if __name__ == "__main__":
    
    generator_choice = input("Choose the generator (csmith/yarpgen): ").strip()
    if generator_choice not in ['csmith', 'yarpgen']:
        print("Invalid choice!")
        exit(1)
    iteration_count = 0  # 반복 횟수를 카운트하기 위한 변수
    codes_to_save = []
    start_time = time.time()
    generation_process = fuzzer_init(generator_choice)
    while True:
        # Queue의 크기가 1000에 도달했는지 확인
        if gen_obj.code_gen_queue.qsize() >= 1000:
            end_time = time.time()
            os.killpg(generation_process.pid, signal.SIGKILL)
            generation_process.join()
            print(f"{gen_obj.code_gen_queue.qsize()} code generated: {BASE_DIR}")
            elapsed_time = end_time - start_time
            print(f"\nTotal time for generating {gen_obj.code_gen_queue.qsize()} codes: {elapsed_time:.2f} seconds")
            break
        
