# config.py 
# 컴파일러, 생성기, 옵션을 설정할 수 있습니다.

import os
import shutil

# 코드 생성기 종류
generators = ['csmith', 'yarpgen']
# 컴파일러 종류
compilers = ['gcc', 'clang', 'aarch64-linux-gnu-gcc', 'clang --target=aarch64-linux-gnu']
# 최적화 옵션
optimization_levels = ['0', '1', '2', '3']
# 수행 횟수 및 타임아웃
total_tasks = 10000  
generator_time_out = 30
compile_time_out = 30
binary_time_out = 30
# csmith include 경로
csmith_include = "/usr/local/include/"

# csmith 옵션
csmith_options = "--max-array-dim 3 \
--max-array-len-per-dim 10 \
--max-block-depth 2 \
--max-block-size 4 \
--max-expr-complexity 4 \
--max-funcs 10 \
--max-pointer-depth 2 \
--max-struct-fields 4 \
--max-union-fields 4 \
--muls \
--safe-math \
--no-packed-struct \
--paranoid \
--pointers \
--structs \
--unions \
--volatiles \
--volatile-pointers \
--const-pointers \
--global-variables \
--no-builtins"

##################################################################################################
# 결과 저장을 위한 configuration
# 일반적으로 프로세스가 성공적으로 종료하면 returncode는 0, 에러로 종료하면 양의 정수, 
# 시그널에 의해 종료되면 해당 시그널 번호의 음의 정수를 출력한다고 합니다.

# Error Type
CRASH = "Crash"
COMPILE_ERROR = "CompileError"
SEGFAULT = "Segmentation Fault"
SYNTAX_ERROR = "Syntax Error"
LINKER_ERROR = "Linker Error"
UNKNOWN_ERROR = "Unknown Error"
TIMEOUT_ERROR = 'Timeout'
CALLED_PROCESS_ERROR = 'CalledProcessError'
FILE_NOT_FOUND_ERROR = 'FileNotFoundError'
PERMISSION_ERROR = 'PermissionError'
UNICODE_DECODE_ERROR = 'UnicodeDecodeError'
OS_ERROR = 'OSError'
UNKNOWN_SUBPROCESS_ERROR = 'UnknownSubprocessError'
PROCESS_KILLED = "ProcessKilled"


# 정의한 크래시 시그널들
CRASH_SIGNALS = {4, 6, 7, 8, 11}  # SIGILL, SIGABRT, SIGBUS, SIGFPE, SIGSEGV

# returncode를 정규화하는 함수
def normalize_returncode(returncode):
    if returncode < 0:
        return -returncode
    elif returncode >= 128:
        return returncode - 128
    else:
        return returncode
    
# return code 분석 함수
def analyze_returncode(returncode, stderr_output, context):
    # 신호값이 음수로 들어오거나 128이 더해진 경우를 처리
    code = normalize_returncode(returncode)
    
    if code == 0:
        return "Success"

    if code in CRASH_SIGNALS:
        return CRASH

    if code == 13:
        return PERMISSION_ERROR

    if code == 9:  # SIGKILL
        return PROCESS_KILLED
    
    if code == 124:
        return TIMEOUT_ERROR
    
    if context == "compilation":
        if code == 1:
            return COMPILE_ERROR
    return UNKNOWN_ERROR


##################################################################################################
# 디렉토리 설정 (상수로 경로 설정)
BASE_DIR = 'output'
GENERATOR_DIRS = {gen: os.path.join(BASE_DIR, gen) for gen in generators}
CATCH_DIRS = {gen: os.path.join(GENERATOR_DIRS[gen], 'catch') for gen in generators}
TEMP_DIRS = {gen: os.path.join(GENERATOR_DIRS[gen], 'temp') for gen in generators}
#CATCH_SUB_DIRS = ['source', 'binary', 'result']
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
        create_directory(CATCH_DIRS[generator])#, CATCH_SUB_DIRS)
        create_directory(TEMP_DIRS[generator])

# cleanup_temp 함수: temp 내부 파일들을 삭제하는 함수
# argv: generator - 어떤 생성기의 temp 폴더일지 판단하기 위함
# return: None
def cleanup_temp(generator):
    try:
        for filename in os.listdir(TEMP_DIRS[generator]):
            full_path = os.path.join(TEMP_DIRS[generator], filename)

            # 파일이면 os.remove, 디렉토리면 shutil.rmtree 사용
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)

            #print(f"Successfully deleted {full_path}.")
    except (FileNotFoundError, PermissionError, OSError) as e:
        print(f"An error occurred while deleting {full_path}: {e}")