# config.py 

import os

# 코드 생성기 종류
generators = ['csmith', 'yarpgen']
# 컴파일러 종류
compilers = ['gcc', 'clang', 'aarch64-linux-gnu-gcc']
# 최적화 옵션
optimization_levels = ['0', '1', '2', '3']
# 수행 횟수 및 타임아웃
total_tasks = 10000  
time_out = 30
# csmith include 경로
csmith_include = "/usr/local/include/"

# 디렉토리 설정 (상수로 경로 설정)
BASE_DIR = 'output'
GENERATOR_DIRS = {gen: os.path.join(BASE_DIR, gen) for gen in generators}
CATCH_DIRS = {gen: os.path.join(GENERATOR_DIRS[gen], 'catch') for gen in generators}
TEMP_DIRS = {gen: os.path.join(GENERATOR_DIRS[gen], 'temp') for gen in generators}
CATCH_SUB_DIRS = ['source', 'binary', 'result']
#TEMP_SUB_DIRS = ['source', 'binary']

# create_directory 함수: 주어진 디렉토리와 하위 디렉토리를 생성
# argv: dir_name - 생성할 디렉토리의 이름 / sub_dirs - 생성할 하위 디렉토리의 이름 목록
# return: None
def create_directory(dir_name, sub_dirs=None):
    try:
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
            #print(f"Directory {dir_name} created successfully.")
    except (FileExistsError, PermissionError, FileNotFoundError) as e:
        print(f"An error occurred while creating {dir_name}: {e}")
        
    if sub_dirs:
        for sub_dir in sub_dirs:
            sub_dir_path = os.path.join(dir_name, sub_dir)
            try:
                if not os.path.exists(sub_dir_path):
                    os.mkdir(sub_dir_path)
                    #print(f"Sub-directory {sub_dir_path} created successfully.")
            except (FileExistsError, PermissionError, FileNotFoundError) as e:
                print(f"An error occurred while creating sub-directory {sub_dir_path}: {e}")

# setup_output_dirs 함수: 전체 디렉토리 구조 생성
# argv: compilers - 사용할 컴파일러의 목록 
# return: None
def setup_output_dirs(generators):
    create_directory(BASE_DIR)

    for generator in generators:
        create_directory(GENERATOR_DIRS[generator])
        create_directory(CATCH_DIRS[generator], CATCH_SUB_DIRS)
        create_directory(TEMP_DIRS[generator])

# cleanup_temp 함수: temp 내부 파일들을 삭제하는 함수
# argv: generator - 어떤 생성기의 temp 폴더일지 판단하기 위함
# return: None
def cleanup_temp(generator):
    try:
        for filename in os.listdir(TEMP_DIRS[generator]):
            full_path = os.path.join(TEMP_DIRS[generator], filename)
            os.remove(full_path)
            #print(f"Successfully deleted {full_path}.")
    except (FileNotFoundError, PermissionError, OSError) as e:
        print(f"An error occurred while deleting {full_path}: {e}")