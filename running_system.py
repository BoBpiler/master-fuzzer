# running_system.py 
# 컴파일하고 바이너리를 실행하는 함수들이 담겨 있습니다.

from config import BINARIES_DIR
import os
import subprocess

# compile_and_run 함수: compile 함수와  run_binary 함수를 통해서 특정 컴파일러와 옵션으로 컴파일 후에 실행 결과를 저장
# argv: filepath - 소스 코드 경로/ id - 소스코드 번호/ compiler - 컴파일러/ optimization_level - 최적화 옵션/ results - 실행 결과 저장할 딕셔너리(map)
# return: 사실상 results에 저장됩니다.
def compile_and_run(filepath, id, compiler, optimization_level, results):
    binary_name = compile(filepath, id, compiler, optimization_level)
    
    #map 방식으로 해당 바이너리 이름과 실행 결과를 results에 저장
    key = f"{compiler}/{id}_{compiler}_O{optimization_level}"
    results[key] = run_binary(binary_name)

    return None # 결과는 results에 저장됨


# compile 함수: 인자로 받은 조건으로 컴파일을 수행
# argv: filepath - 소스 코드 경로/ id - 소스코드 번호/ compiler - 컴파일러/ optimization_level - 최적화 옵션
# return: binary_name - 바이너리 파일의 이름 및 경로 
def compile(filepath, id, compiler, optimization_level):
    # 바이너리 파일의 이름
    binary_name = f"{BINARIES_DIR}/{compiler}/{id}_{compiler}_O{optimization_level}"
    
    # csmith의 include 경로
    csmith_include = f"{os.path.expanduser('~')}/csmith/include"
    
    # 컴파일 과정
    subprocess.run([compiler, filepath, '-o', binary_name, f'-O{optimization_level}', f'-I{csmith_include}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    
    return binary_name


# run_binary 함수: 바이너리를 실행하고, 실행 결과를 반환
# argv: binary_name - 바이너리 파일 이름 및 경로
# return: result - 실행 결과(ex. checksum 값)
def run_binary(binary_name):
    #output_filename = f"results/{compiler}/{id}_{compiler}_O{optimization_level}.txt"
    # 실행 결과를 파일에 저장
    #with open(output_filename, 'w') as f:
    #    f.write(result)
    try:
        # 실행 결과
        result = subprocess.run([f'./{binary_name}'], capture_output=True, text=True, timeout=30).stdout
    except subprocess.TimeoutExpired:
        # 타임아웃이 발생한 경우
        print(f"TimeoutExpired occurred in {binary_name}")
        result = "Timeout"  # 이 값을 어떻게 할까
    return result
    
    