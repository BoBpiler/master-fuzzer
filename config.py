# config.py 
# 컴파일러, 생성기, 옵션을 설정할 수 있습니다.

import os
import shutil
import platform
import hashlib
import socket
import subprocess
import sys
import requests
from datetime import datetime
import random
import zipfile


# 텔레그램 Chat ID 와 Token 값으로 직접 넣어주어야 합니다!
CHAT_ID = ""
HIGH_SEVERITY_CHAT_ID = ""
TOKEN = ""

def zip_src_files(filenames, output_filename):
    with zipfile.ZipFile(output_filename, 'w') as zipf:
        for file in filenames:
            zipf.write(file, os.path.basename(file))

# send_telegram_message 함수: 버그를 탐지하고 텔레그램 봇에게 알림을 보내는 함수
# argv: machine_info - 머신 정보를 담은 딕셔너리/ generator - 생성기 종류/ id - 소스코드 uuid/ bug_type - 버그 타입/ detail - 버그 상세 내용/src_file_path - 소스코드 경로 /result_file_path - 결과 txt 경로/ severity - 중요도 정보
# return: response.json() - http post 요청 응답 정보
def send_telegram_message(machine_info, generator_config, id, random_seed, bug_type, detail, dir_path, severity="low"):
    files_to_send = [filepath.format(path=dir_path, id=id) for filepath in generator_config['src_files_to_send']]
    
    result_files = get_result_file_names(id)
    result_file_path = os.path.join(dir_path, result_files["txt"])
    
    if generator_config['zip_required']:
        zip_path = os.path.join(dir_path, generator_config['zip_name'].format(id=str(id)))
        zip_src_files(files_to_send, zip_path)
        files_to_send = [zip_path]

    # 중요도에 따른 이모지 선택
    severity_emoji = {
        "low": "ℹ️",
        "medium": "⚠️",
        "high": "🚨"
    }.get(severity, "ℹ️")  # 만약 알려지지 않은 severity가 들어오면 "ℹ️"를 기본값으로 사용 
    
    # 메시지 포맷
    formatted_message = f"""Fuzzing Alert {severity_emoji} ({severity.upper()}):

Machine Info:
- OS: {machine_info.get('os', 'None')}
- Hostname: {machine_info.get('hostname', 'None')}
- IP: {machine_info.get('ip', 'None')}
- Whoami: {machine_info.get('whoami', 'None')}
- SSH Public Key Hash: {machine_info.get('ssh_pub_key_hash', 'None')}

Bug Info:
- Generator: {generator_config['name']}
- UUID: {id}
- Random Seed: {random_seed}
- Bug Type: {bug_type}
- Bug detail: {detail}
"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendmessage"
    data = {
        "chat_id": CHAT_ID,
        "text": formatted_message
    }
    response = requests.post(url, data=data)

    # 성공적으로 메시지를 보냈다면, 이제 결과 파일 보내기
    if response.json().get("ok"):
        url_doc = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
        files = {'document': open(result_file_path, 'rb')}
        data_doc = {'chat_id': CHAT_ID}
        response_doc = requests.post(url_doc, files=files, data=data_doc)
        
        if response_doc.json().get("ok") and severity == "high":
            for file_path in files_to_send:
                files = {'document': open(file_path, 'rb')}
                response = requests.post(url_doc, files=files, data=data_doc)

            # high인 경우 high만 알람이 오는 방에 추가적으로 보냅니다.
            data['chat_id'] = HIGH_SEVERITY_CHAT_ID
            data_doc['chat_id'] = HIGH_SEVERITY_CHAT_ID
            requests.post(url, data=data)
            requests.post(url_doc, files={'document': open(result_file_path, 'rb')}, data=data_doc)
            for file_path in files_to_send:
                files = {'document': open(file_path, 'rb')}
                requests.post(url_doc, files=files, data=data_doc)

        return response.json()
    else:
        return {"status": "failed", "reason": "Could not send the message"}

def get_result_file_names(id):
    return {
        "txt": f"{id}_result.txt",
        "json": f"{id}_result.json"
    }


generators_config = {
    'csmith': {
        'name': 'csmith',
        'options': [
            "--max-array-dim 3", 
            "--max-array-len-per-dim 10",
            "--max-block-depth 3",
            "--max-block-size 5",
            "--max-expr-complexity 10",
            "--max-funcs 4",
            "--max-pointer-depth 3",
            "--max-struct-fields 10",
            "--max-union-fields 10",
            "--muls",
            "--safe-math",
            "--no-packed-struct",
            "--pointers",
            "--structs",
            "--unions",
            "--volatiles",
            "--volatile-pointers",
            "--const-pointers",
            "--global-variables",
            "--no-builtins",
            "--inline-function",
            "--inline-function-prob 50"
        ],
        'output_format': '{generator} {options} -o {filepath} --seed {random_seed}',
        'src_files': ['{path}/random_program_{id}.c'],
        'src_files_to_send': ['{path}/random_program_{id}.c'],
        'zip_required': False,
        'zip_name': None,
        'include_dir': '/usr/local/include/',
        'path_type': 'filepath'
    },
    'yarpgen': {
        'name': 'yarpgen',
        'options': [
            "--std=c",
            "--mutate=all"
        ],
        'output_format': '{generator} {options} -o {dir_path} --seed={random_seed} --mutation-seed={random_seed}',
        'src_files': ['{path}/driver.c', '{path}/func.c'],
        'src_files_to_send': ['{path}/driver.c', '{path}/func.c', '{path}/init.h'],
        'zip_required': True,
        'zip_name': "yarpgen_{id}.zip",
        'include_dir': '{path}',
        'path_type': 'dirpath'
    },
    'yarpgen_scalar': {
        'name': 'yarpgen_scalar',
        'options': [
            "--std=c99"
        ],
        'output_format': '{generator} {options} -d {dir_path} --seed={random_seed}',
        'src_files': ['{path}/driver.c', '{path}/func.c'],
        'src_files_to_send': ['{path}/driver.c', '{path}/func.c', '{path}/init.h'],
        'zip_required': True,
        'zip_name': "yarpgen_scalar_{id}.zip",
        'include_dir': '{path}',
        'path_type': 'dirpath'
    }
}

# 컴파일러 종류
compilers = [
    {'name': './gcc-trunk', 'type': 'base', 'folder_name': 'gcc', 'execute': '{binary}'},
    {'name': './clang-18', 'type': 'base', 'folder_name': 'clang', 'execute': '{binary}'},
    {'name': 'aarch64-linux-gnu-gcc', 'type': 'cross-aarch64', 'folder_name': 'gcc-aarch64', 'execute': 'qemu-aarch64-static -L /usr/aarch64-linux-gnu {binary}'},
    {'name': './clang-18 --target=aarch64-linux-gnu', 'type': 'cross-aarch64', 'folder_name': 'clang-aarch64', 'execute': 'qemu-aarch64-static -L /usr/aarch64-linux-gnu {binary}'},
    {'name': 'mips64-linux-gnuabi64-gcc', 'type': 'cross-mips64', 'folder_name': 'gcc-mips64', 'execute': 'qemu-mips64-static -L /usr/mips64-linux-gnuabi64 {binary}'},
    {'name': './clang-18 --target=mips64-linux-gnuabi64', 'type': 'cross-mips64', 'folder_name': 'clang-mips64', 'execute': 'qemu-mips64-static -L /usr/mips64-linux-gnuabi64 {binary}'},
    {'name': './riscv64-unknown-elf-gcc', 'type': 'cross-riscv64', 'folder_name': 'gcc-riscv64', 'execute': 'qemu-riscv64-static {binary}'},
    {'name': './clang-18 --sysroot=$HOME/riscv/riscv64-unknown-elf --gcc-toolchain=$HOME/riscv --target=riscv64-unknown-elf -march=rv64gc', 'type': 'cross-riscv64', 'folder_name': 'clang-riscv64', 'execute': 'qemu-riscv64-static {binary}'}
]


# 최적화 옵션
optimization_levels = ['0', '1', '2', '3']

# gcc_O3_flags
gcc_O3_flags = ['-fgcse-after-reload', '-fipa-cp-clone', '-floop-interchange', '-floop-unroll-and-jam', 
                '-fpeel-loops', '-fpredictive-commoning', '-fsplit-loops', '-fsplit-paths', '-ftree-loop-distribution', 
                '-ftree-loop-vectorize', '-ftree-partial-pre', '-ftree-slp-vectorize', '-funswitch-loops', '-fvect-cost-model', 
                '-fvect-cost-model=dynami', '-fversion-loops-for-strides']

def select_random_flags(flags, num):
    return random.sample(flags, num)

# 수행 횟수 및 타임아웃
total_tasks = 100 
generator_time_out = 30
compile_time_out = 30
binary_time_out = 30

# yarpgen 옵션
yarpgen_options = [
    "--std=c",
    "--mutate=all"
]

yarpgen_scalar_options = [
    "--std=c99"
]


# csmith include 경로
csmith_include = "/usr/local/include/"

# csmith 옵션
csmith_options = "--max-array-dim 3 \
--max-array-len-per-dim 10 \
--max-block-depth 3 \
--max-block-size 5 \
--max-expr-complexity 10 \
--max-funcs 4 \
--max-pointer-depth 3 \
--max-struct-fields 10 \
--max-union-fields 10 \
--muls \
--safe-math \
--no-packed-struct \
--pointers \
--structs \
--unions \
--volatiles \
--volatile-pointers \
--const-pointers \
--global-variables \
--no-builtins \
--inline-function \
--inline-function-prob 50"

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
def analyze_returncode(returncode, context):
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
# 디렉토리 설정 (상수로 경로 설정)
BASE_DIR = f'output_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}'
GENERATOR_DIRS = {key: os.path.join(BASE_DIR, config['name']) for key, config in generators_config.items()}
CATCH_DIRS = {key: os.path.join(GENERATOR_DIRS[key], 'catch') for key in generators_config.keys()}
TEMP_DIRS = {key: os.path.join(GENERATOR_DIRS[key], 'temp') for key in generators_config.keys()}

#CATCH_SUB_DIRS = ['source', 'binary', 'result']
#TEMP_SUB_DIRS = ['source', 'binary']

# create_directory 함수: 주어진 디렉토리와 하위 디렉토리를 생성
# argv: dir_name - 생성할 디렉토리의 이름 / sub_dirs - 생성할 하위 디렉토리의 이름 목록
# return: None
def create_directory(dir_name, sub_dirs=None):
    try:
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        else:
            shutil.rmtree(dir_name)
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
def setup_output_dirs():
    create_directory(BASE_DIR)

    for generator_key in generators_config.keys():
        create_directory(GENERATOR_DIRS[generator_key])
        create_directory(CATCH_DIRS[generator_key])  
        create_directory(TEMP_DIRS[generator_key])

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


# get_machine_info 함수: 해당 머신의 정보를 가져오는 함수
# argv: None
# return: info_dict - OS, hostname, IP, whoami, ssh pub key hash 값을 담고 있음
def get_machine_info():
    info_dict = {}
    
    # os, hostname 저장
    try:
        info_dict['os'] = platform.system()
        info_dict['hostname'] = socket.gethostname()
    except Exception as e:
        print(f"Error getting OS or hostname: {e}")
        sys.exit(1)
    
    # IP 주소 저장
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        info_dict['ip'] = s.getsockname()[0]
        s.close()
    except Exception as e:
        print(f"Error getting IP address: {e}")
        sys.exit(1)  # IP 주소를 가져오는 데 실패하면 프로그램을 종료합니다.

    if platform.system() == 'Linux':
        # Linux
        try:
            info_dict['whoami'] = subprocess.getoutput("whoami")
            with open("BoBpiler.pub", "r") as f:
                ssh_key = f.read().strip()
            info_dict['ssh_pub_key_hash'] = hashlib.sha256(ssh_key.encode()).hexdigest()    # 해싱

        except Exception as e:
            print(f"Error in Linux: {e}")

    elif platform.system() == 'Windows':
        # Windows
        try:
            info_dict['whoami'] = subprocess.getoutput("whoami")
            # ssh pub key 위치는 ../ 라고 가정
            with open("../BoBpiler.pub", "r") as f:
                ssh_key = f.read().strip()
            info_dict['ssh_pub_key_hash'] = hashlib.sha256(ssh_key.encode()).hexdigest()    # 해싱
        except Exception as e:
            print(f"Error in Windows: {e}")

    return info_dict
