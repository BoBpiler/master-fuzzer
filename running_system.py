# running_system.py 
# 컴파일하고 바이너리를 실행하는 함수들이 담겨 있습니다.

from config import TEMP_DIRS, csmith_include
import os
import subprocess

# compile_and_run 함수: compile 함수와  run_binary 함수를 통해서 특정 컴파일러와 옵션으로 컴파일 후에 실행 결과를 저장
# argv: filepath - 소스 코드 경로/ id - 소스코드 번호/ compiler - 컴파일러/ optimization_level - 최적화 옵션/ results - 실행 결과 저장할 딕셔너리(map)
# return: 사실상 results에 저장됩니다.
def compile_and_run(filepath, generator, id, compiler, optimization_level, results):
    binary_name = compile(filepath, generator, id, compiler, optimization_level)
    
    #map 방식으로 해당 바이너리 이름과 실행 결과를 results에 저장
    results[binary_name] = run_binary(binary_name)

    return None # 결과는 results에 저장됨


# compile 함수: 인자로 받은 조건으로 컴파일을 수행
# argv: path - 소스 코드 경로/ generator - 생성기 종류/ id - 소스코드 번호/ compiler - 컴파일러/ optimization_level - 최적화 옵션
# return: binary_name - 바이너리 파일의 이름 및 경로 
def compile(path, generator, id, compiler, optimization_level):
    # 바이너리 파일의 이름
    binary_name = f"{TEMP_DIRS[generator]}/{id}_{compiler}_O{optimization_level}"

    # validator 과정에서 만들어졌다면, 넘어가기
    if os.path.exists(binary_name):
        return binary_name
    
    if generator == 'yarpgen':
        # yarpgen 경우, 디렉터리 내의 모든 .c 파일을 컴파일
        c_files = [os.path.join(path, f) for f in ['driver.c', 'func.c']]
        subprocess.run([compiler, *c_files, '-o', binary_name, f'-O{optimization_level}', f'-I{path}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    elif generator == 'csmith':
        # csmith의 경우
        subprocess.run([compiler, path, '-o', binary_name, f'-O{optimization_level}', f'-I{csmith_include}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    
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
        result = subprocess.run([f'./{binary_name}'], capture_output=True, text=True, timeout=30).stdout
    except subprocess.TimeoutExpired:
        # TimeoutExpired: 프로세스가 지정된 시간 내에 완료되지 않았을 때 발생
        print(f"TimeoutExpired occurred in {binary_name}")
        result = "Timeout"
    except subprocess.CalledProcessError:
        # CalledProcessError: 명령어가 0이 아닌 상태 코드를 반환했을 때 발생
        print(f"CalledProcessError occurred in {binary_name}")
        result = "Error"
    except FileNotFoundError:
        # FileNotFoundError: 바이너리 파일을 찾을 수 없을 때 발생
        print(f"FileNotFoundError occurred for {binary_name}")
        result = "File not found"
    except PermissionError:
        # PermissionError: 바이너리 파일을 실행할 권한이 없을 때 발생
        print(f"PermissionError occurred for {binary_name}")
        result = "Permission denied"
    except UnicodeDecodeError:
        # UnicodeDecodeError: 출력을 UTF-8 텍스트로 디코딩할 수 없을 때 발생
        print(f"UnicodeDecodeError occurred for {binary_name}")
        result = "Decode Error"
    except OSError as e:
        # OSError: 운영체제 수준에서 발생하는 일반적인 오류를 처리
        print(f"OSError occurred for {binary_name}: {e}")
        result = "OS Error"
    except subprocess.SubprocessError:
        # SubprocessError: subprocess 모듈에서 발생할 수 있는 모든 예외의 상위 클래스로
        # 이 핸들러는 TimeoutExpired나 CalledProcessError와 같은 구체적인 예외가 먼저 처리되지 않은 경우에
        # 다른 모든 subprocess 관련 예외를 처리하기 위해서 추가했습니다.
        print(f"Unknown subprocess error occurred for {binary_name}: {e}")
        result = f"Unknown Error: {e}"
    return result
    