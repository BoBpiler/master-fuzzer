# CsmithGenerator.py

from config import RANDOM_CODES_DIR
import os
import subprocess

# generate_c_code 함수: Csmith를 통해서 C 코드를 랜덤으로 생성
# argv: id - 소스코드 번호
# return: filepath - 생성된 파일 이름 및 경로
def generate_c_code(id):
    filepath = f'{RANDOM_CODES_DIR}/random_program_{id}.c'
    csmith_env = os.environ.copy()
    csmith_env["PATH"] = f"{csmith_env['PATH']}:{os.path.expanduser('~')}/csmith/bin"
    #csmith_include = f"{os.path.expanduser('~')}/csmith/include"

    # C 코드 생성
    subprocess.run(['csmith', '-o', filepath], env=csmith_env, timeout=60)
    return filepath

