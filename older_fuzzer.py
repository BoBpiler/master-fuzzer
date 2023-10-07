# fuzzer.py
# main 입니다.

from older_config import*
# from CodeGenerator import generate_c_code
from older_Analyzer import analyze_results
from older_running_system import*
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from queue import Queue
import logging
import uuid
import argparse
from itertools import repeat

logging.basicConfig(level=logging.WARNING)
import json
import time

def load_from_json_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def process_test_codes(code_data):
    try:
        generator = code_data['generator']
        id = code_data['uuid']
        filepath = code_data['original_fuzzer_path'] 
        random_seed = None  # No random seed
        
        with ProcessPoolExecutor() as executor:
            futures = []
            results = {}
            # 컴파일 및 실행 (gcc, clang으로 -O0 ~ -O3 옵션 주어서 컴파일 하고 실행 결과 저장)
            for compiler in compilers:
                for opt_level in optimization_levels:
                    futures.append(executor.submit(compile_and_run, filepath, generator, id, compiler, opt_level, random_seed))
                            
            for future in futures:
                result = future.result()
                if result is not None:
                    key, result_dict = result
                    if key == "error":  # 에러 처리
                        continue
                    results[key] = result_dict
                
            if len(results) > 0:
                machine_info = get_machine_info()
                analyze_results(generator, id, random_seed, results, machine_info, True)  # Assuming partial_timeout as True
            else:
                logging.critical(f"CRITICAL ERROR: This is an exceptional case which means impossible and requires immediate attention.")
    except Exception as e:
        logging.error(f"An unexpected error occurred for UUID {id}: {e}")

# main 함수: 퍼징을 수행하는 총괄 코드
def main():
    codes_from_file = load_from_json_file("saved_codes.json")
    iteration_count = 0
    start_time = time.time()  # 시작 시간 기록
    for code_data in codes_from_file:
        process_test_codes(code_data)
        iteration_count += 1
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"{iteration_count} iterations completed in {elapsed_time} seconds.")

if __name__ == "__main__":
    main()


