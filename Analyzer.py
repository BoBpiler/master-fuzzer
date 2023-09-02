# Analyzer.py
# 함수: 파일을 컴파일하고 실행 결과를 저장하는 함수

import os
import subprocess

def compile_and_run(filename, id, compiler, optimization_level):
    # 출력 파일과 바이너리 파일의 이름을 설정
    output_filename = f"results/{compiler}/{id}_{compiler}_O{optimization_level}.txt"
    binary_name = f"temp/{compiler}/{id}_{compiler}_O{optimization_level}"

    # csmith의 include 경로
    csmith_include = f"{os.path.expanduser('~')}/csmith/include"
    
    # 컴파일 과정
    subprocess.run([compiler, filename, '-o', binary_name, f'-O{optimization_level}', f'-I{csmith_include}'], stderr=subprocess.DEVNULL, timeout=60)

    try:
        # 실행 결과
        result = subprocess.run([f'./{binary_name}'], capture_output=True, text=True, timeout=60).stdout
    except subprocess.TimeoutExpired:
        # 타임아웃이 발생한 경우
        print(f"TimeoutExpired occurred in {binary_name}")
        result = "Timeout"  # 이 값을 어떻게 할까

    # 실행 결과를 파일에 저장
    with open(output_filename, 'w') as f:
        f.write(result)

    return result

