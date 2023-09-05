# validator.py

from config import TEMP_DIRS, time_out
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO)  # 로깅 레벨 설정

# validate_code 함수: 생성된 소스코드가 컴파일이 잘 되는지 확인하는 함수
# argv: filename - 소스코드 경로/ generator - 생성기 종류/id - 소스코드 번호/ compiler - 컴파일러 종류
# return: true, false - 컴파일 성공시 true, 컴파일 실패 시 false
def validate_code(filename, generator, id, compiler):
    # csmith와 yarpgen include 경로
    csmith_include = f"{os.path.expanduser('~')}/csmith/include"
    #yarpgen_include = f"{filename}"
    # 바이너리 이름 
    binary_name = f"{TEMP_DIRS[generator]}/{id}_{compiler}_O0"

    if not os.path.exists(filename):
        print(f"Source file {filename} does not exist.")
        return False
    
    if generator == 'csmith':
        # 컴파일 과정
        result = subprocess.run([compiler, filename, '-o', binary_name, f'-I{csmith_include}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=time_out)
    elif generator == 'yarpgen':
        # yarpgen 경우, 디렉터리 내의 모든 .c 파일을 컴파일
        c_files = [os.path.join(filename, f) for f in ['driver.c', 'func.c']]
        result = subprocess.run([compiler, *c_files, '-o', binary_name, f'-I{filename}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=time_out)

    # 컴파일 결과 return
    if result.returncode != 0:
        logging.error(f"Compilation failed with error code {result.returncode}.") #Error message: {result.stderr.decode()}")
        return False
    else:
        return True
    