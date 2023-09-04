# config.py 

import os

# 컴파일러 종류
compilers = ['gcc', 'clang']
# 최적화 옵션
optimization_levels = ['0', '1', '2', '3']

# 수행 횟수
total_tasks = 10000  




# 디렉토리 설정
BASE_DIR = 'output'
RANDOM_CODES_DIR = f'{BASE_DIR}/RandomCodes'    # 생성된 C 코드 저장
RESULTS_DIR = f'{BASE_DIR}/results'             # 실행 결과 저장 (txt에 저장하는 것도 performance 영향이 있다고 생각해서 제외한 상태)
TEMP_DIR = f'{BASE_DIR}/temp'                   # validator로 컴파일 된 바이너리 저장 (validator를 현재 사용하지 않도록 한 상태)
BINARIES_DIR = f'{BASE_DIR}/binaries'           # 생성된 바이너리 저장
CATCH_DIR = f'{BASE_DIR}/catch'                 # 로직에 잡힌 소스코드 저장

# create_directory 함수: 주어진 디렉토리와 하위 디렉토리를 생성
# argv: dir_name - 생성할 디렉토리의 이름 / sub_dirs - 생성할 하위 디렉토리의 이름 목록
# return: None
def create_directory(dir_name, sub_dirs=None):
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    if sub_dirs:
        for sub_dir in sub_dirs:
            sub_dir_path = os.path.join(dir_name, sub_dir)
            if not os.path.exists(sub_dir_path):
                os.mkdir(sub_dir_path)

# setup_output_dirs 함수: 전체 디렉토리 구조 생성
# argv: compilers - 사용할 컴파일러의 목록 
# return: None
def setup_output_dirs(compilers):
    create_directory(BASE_DIR)

    directories_to_create = [
        (RANDOM_CODES_DIR, None),
        (RESULTS_DIR, compilers),
        (TEMP_DIR, compilers),
        (BINARIES_DIR, compilers),
        (CATCH_DIR, None)
    ]

    for dir_name, sub_dirs in directories_to_create:
        create_directory(dir_name, sub_dirs)