# CsmithGenerator.py
# 함수: C 코드를 랜덤으로 생성

import os
import subprocess

def generate_c_code(id):
    filename = f'RandomCodes/random_program_{id}.c'
    csmith_env = os.environ.copy()
    csmith_env["PATH"] = f"{csmith_env['PATH']}:{os.path.expanduser('~')}/csmith/bin"
    #csmith_include = f"{os.path.expanduser('~')}/csmith/include"

    # C 코드 생성
    subprocess.run(['csmith', '-o', filename], env=csmith_env, timeout=60)
    return filename

