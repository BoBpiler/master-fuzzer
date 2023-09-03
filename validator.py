# validator.py
# 함수: 생성된 소스코드가 컴파일이 잘 되는지 확인하는 함수
# return: true, false - 컴파일 성공시 true, 컴파일 실패 시 false
# argv: filename, compiler

import os
import subprocess

def validator(filename, id, compiler):
    # csmith의 include 경로
    csmith_include = f"{os.path.expanduser('~')}/csmith/include"
    
    # 바이너리 이름 
    binary_name = f"temp/{compiler}/{id}_{compiler}"


    # 컴파일 과정
    result = subprocess.run([compiler, filename, '-o', binary_name, f'-I{csmith_include}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 컴파일 결과 return
    if result.returncode == 1:
        return False
    else:
        return True
    