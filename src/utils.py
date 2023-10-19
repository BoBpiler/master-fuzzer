import psutil
import zipfile
import hashlib
import socket
import subprocess
import sys
import requests
import shutil
import platform
import os
from config import*
import logging
import logging.handlers
import multiprocessing

# 프로세스 종료를 위한 함수
def terminate_process_and_children(pid):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):  # 모든 하위 프로세스에 대해
            child.terminate()
        parent.terminate()
    except psutil.NoSuchProcess:
        pass

def setup_logging():
    try:
        queue = multiprocessing.Queue(-1)
        qh = logging.handlers.QueueHandler(queue)
        root = logging.getLogger()
        root.addHandler(qh)
        root.setLevel(logging.WARNING)

        # 로깅 포맷 설정
        log_format = "%(asctime)s [%(levelname)s]: %(message)s"
        formatter = logging.Formatter(log_format)

        # 로그 파일 핸들러 추가
        file_handler = logging.FileHandler(os.path.join(BASE_DIR, 'fuzzer.log'))
        file_handler.setFormatter(formatter)

        listener = logging.handlers.QueueListener(queue, file_handler)
        listener.start()

        return root, listener
    except Exception as e:
        print(f"Logging setup error occurs: {e}")
        raise

# zip 파일 압축 함수
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
##################################################################################################
# 결과 분석을 위한 configuration 
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
# Windows-specific error codes NTSTATUS
ACCESS_VIOLATION = 3221225477  # 0xC0000005
STACK_OVERFLOW = 3221225725  # 0xC00000FD

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
    if platform.system == "Windows":
        if returncode == 0:
            return "Success"
        elif returncode == ACCESS_VIOLATION:
            return "Access Violation"
        elif returncode == STACK_OVERFLOW:
            return "Stack Overflow"
        else:
            return UNKNOWN_ERROR
        # 기존 리눅스 프로토타입 부분
    else:
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
        logging.error(f"An error occurred while creating {dir_name}: {e}")
        
    if sub_dirs:
        for sub_dir in sub_dirs:
            sub_dir_path = os.path.join(dir_name, sub_dir)
            try:
                if not os.path.exists(sub_dir_path):
                    os.mkdir(sub_dir_path)
                    #print(f"Sub-directory {sub_dir_path} created successfully.")
            except (FileExistsError, PermissionError, FileNotFoundError) as e:
                logging.error(f"An error occurred while creating sub-directory {sub_dir_path}: {e}")

# setup_output_dirs 함수: 전체 디렉토리 구조 생성
# argv: None
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
def cleanup_temp(temp_dir, logger):
    try:
        for filename in os.listdir(temp_dir):
            full_path = os.path.join(temp_dir, filename)

            # 파일이면 os.remove, 디렉토리면 shutil.rmtree 사용
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)

            #print(f"Successfully deleted {full_path}.")
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.error(f"An error occurred while deleting {full_path}: {e}")


# get_machine_info 함수: 해당 머신의 정보를 가져오는 함수
# argv: None
# return: info_dict - OS, hostname, IP, whoami, ssh pub key hash 값을 담고 있음
def get_machine_info(logger):
    info_dict = {}
    
    # os, hostname 저장
    try:
        info_dict['os'] = platform.system()
        info_dict['hostname'] = socket.gethostname()
    except Exception as e:
        logger.error(f"Error getting OS or hostname: {e}")
        sys.exit(1)
    
    # IP 주소 저장
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        info_dict['ip'] = s.getsockname()[0]
        s.close()
    except Exception as e:
        logger.error(f"Error getting IP address: {e}")
        sys.exit(1)  # IP 주소를 가져오는 데 실패하면 프로그램을 종료합니다.

    if platform.system() == 'Linux':
        # Linux
        try:
            info_dict['whoami'] = subprocess.getoutput("whoami")
            with open("BoBpiler.pub", "r") as f:
                ssh_key = f.read().strip()
            info_dict['ssh_pub_key_hash'] = hashlib.sha256(ssh_key.encode()).hexdigest()    # 해싱

        except Exception as e:
            logger.error(f"Error in Linux: {e}")

    elif platform.system() == 'Windows':
        # Windows
        try:
            info_dict['whoami'] = subprocess.getoutput("whoami")
            # ssh pub key 위치는 ../ 라고 가정
            with open("../BoBpiler.pub", "r") as f:
                ssh_key = f.read().strip()
            info_dict['ssh_pub_key_hash'] = hashlib.sha256(ssh_key.encode()).hexdigest()    # 해싱
        except Exception as e:
            logger.error(f"Error in Windows: {e}")

    return info_dict
