import json
from generate_config import*
import threading
import multiprocessing
import sys
import os
import signal
import shutil

sys.path.append('./forkserver_generator')  # 경로 추가
from forkserver_generator import generator as gen_obj

def copy_directory(src, dst):
    """
    src 디렉토리의 내용을 dst 디렉토리에 복사합니다.
    """
    # 이미 존재하는 경우 목적지 디렉토리 삭제
    if os.path.exists(dst):
        shutil.rmtree(dst)
        
    # 디렉토리 복사
    shutil.copytree(src, dst)


def generate_codes_process(csmith_temp_path, yarpgen_temp_path):
    gen_obj.gen_main(csmith_temp_path, yarpgen_temp_path)

def fuzzer_init():
    csmith_temp_path = get_absolute_temp_path('csmith')
    yarpgen_temp_path = get_absolute_temp_path('yarpgen')
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
    generation_process =  fuzzer_init()

    iteration_count = 0  # 반복 횟수를 카운트하기 위한 변수
    codes_to_save = []

    while True:
        code_data = gen_obj.code_gen_queue.get()
        generator_name = code_data['generator']
        id = code_data['uuid']
        input_src = code_data['file_path']

        # original_fuzzer_path 추가
        if generator_name == "yarpgen":
            path1 = code_data['file_path'].split('|')[0]  # 첫 번째 경로
            directory = os.path.dirname(path1)  # 경로에서 디렉토리만 추출
            code_data['original_fuzzer_path'] = directory
        else:
            code_data['original_fuzzer_path'] = input_src
            
        codes_to_save.append(code_data)
        # 반복 횟수 업데이트 및 체크
        iteration_count += 1
        if iteration_count >= 100:
            # 1000개 데이터를 JSON 파일로 저장
            save_to_json_file(codes_to_save, "saved_codes.json")
            os.killpg(generation_process.pid, signal.SIGKILL)
            generation_process.join()

            # BASE_DIR의 내용을 새로운 디렉토리로 복사
            copy_directory(BASE_DIR, "new_fuzzer_output")
            copy_directory(BASE_DIR, "older_fuzzer_output")

            print(f"{iteration_count} code generated: {BASE_DIR}")
            break