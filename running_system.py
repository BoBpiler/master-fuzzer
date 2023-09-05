# running_system.py 
# 컴파일하고 바이너리를 실행하는 함수들이 담겨 있습니다.

from config import TEMP_DIRS, csmith_include, time_out
from queue import Queue
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO)

# compile_and_run 함수: compile 함수와  run_binary 함수를 통해서 특정 컴파일러와 옵션으로 컴파일 후에 실행 결과를 저장
# argv: filepath - 소스 코드 경로/ id - 소스코드 번호/ compiler - 컴파일러/ optimization_level - 최적화 옵션/ results - 실행 결과 저장할 딕셔너리(map)
# return: 사실상 results에 저장됩니다.
def compile_and_run(filepath, generator, id, compiler, optimization_level, result_queue):
    try:
        #logging.info(f"Starting compile_and_run for {filepath} with {compiler} and optimization level {optimization_level}")
        binary_name = compile(filepath, generator, id, compiler, optimization_level)
        
        # yarpgen에서 발생할 수 있는 잠재적인 컴파일 실패 체크
        if binary_name is None:
            logging.warning("Compilation failed. Skipping run.")
            return
        
        #map 방식으로 해당 바이너리 이름과 실행 결과를 results에 저장
        result = run_binary(binary_name, compiler)
        
        # 큐에 결과를 저장
        result_queue.put((binary_name, result))
        
        #logging.info(f"Ending compile_and_run for {filepath}")
        #return None # 결과는 results에 저장됨
    except Exception as e:
        logging.error(f"Unexpected error in compile_and_run for {filepath}: {e}")


# compile 함수: 인자로 받은 조건으로 컴파일을 수행
# argv: path - 소스 코드 경로/ generator - 생성기 종류/ id - 소스코드 번호/ compiler - 컴파일러/ optimization_level - 최적화 옵션
# return: binary_name - 바이너리 파일의 이름 및 경로 
def compile(path, generator, id, compiler, optimization_level):
    try:
        #logging.info(f"Starting compile for {path} with {compiler} and optimization level {optimization_level}")
        # 바이너리 파일의 이름
        binary_name = f"{TEMP_DIRS[generator]}/{id}_{compiler}_O{optimization_level}"

        if generator == 'yarpgen':
            # yarpgen 경우, 디렉터리 내의 모든 .c 파일을 컴파일
            c_files = [os.path.join(path, f) for f in ['driver.c', 'func.c']]
            result = subprocess.run([compiler, *c_files, '-o', binary_name, f'-O{optimization_level}', f'-I{path}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=time_out)
            # 컴파일 실패시 넘어가기 
            if result.returncode != 0:
                logging.warning(f"Compilation failed for {path} with return code {result.returncode}")
                return None
        elif generator == 'csmith':
            # csmith의 경우
            result = subprocess.run([compiler, path, '-o', binary_name, f'-O{optimization_level}', f'-I{csmith_include}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=time_out)
            # 컴파일 실패시 넘어가기 
            if result.returncode != 0:
                logging.warning(f"Compilation failed for {path} with return code {result.returncode}")
                return None
        return binary_name
    except subprocess.TimeoutExpired:
        logging.warning(f"Compilation timed out for {path}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in compile for {path}: {e}")
        return None


# run_binary 함수: 바이너리를 실행하고, 실행 결과를 반환
# argv: binary_name - 바이너리 파일 이름 및 경로/ compiler - 크로스 컴파일 확인을 위함
# return: result - 실행 결과(ex. checksum 값)
def run_binary(binary_name, compiler):
    #output_filename = f"results/{compiler}/{id}_{compiler}_O{optimization_level}.txt"
    try:
        #logging.info(f"Starting run_binary for {binary_name}") 
        if compiler == 'aarch64-linux-gnu-gcc':
            result = subprocess.run(['qemu-aarch64-static', '-L', '/usr/aarch64-linux-gnu', f'./{binary_name}'], capture_output=True, timeout=time_out)
            print(f"{binary_name} Result obtained: {result.stdout.decode('utf-8')}")
            result = result.stdout.decode('utf-8')
        else:
            result = subprocess.run([f'./{binary_name}'], capture_output=True, timeout=time_out)
            print(f"{binary_name} Result obtained: {result.stdout.decode('utf-8')}")
            result = result.stdout.decode('utf-8')
    except subprocess.TimeoutExpired:
        # TimeoutExpired: 프로세스가 지정된 시간 내에 완료되지 않았을 때 발생
        logging.warning(f"TimeoutExpired occurred in {binary_name}")
        result = "Timeout"
    except subprocess.CalledProcessError as e:
        # CalledProcessError: 명령어가 0이 아닌 상태 코드를 반환했을 때 발생
        logging.error(f"CalledProcessError occurred in {binary_name}: {e}")
        result = "Error"
    except FileNotFoundError as e:
        # FileNotFoundError: 바이너리 파일을 찾을 수 없을 때 발생
        logging.error(f"FileNotFoundError occurred for {binary_name}: {e}")
        result = "File not found"
    except PermissionError as e:
        # PermissionError: 바이너리 파일을 실행할 권한이 없을 때 발생
        logging.error(f"PermissionError occurred for {binary_name}: {e}")
        result = "Permission denied"
    except UnicodeDecodeError as e:
        # UnicodeDecodeError: 출력을 UTF-8 텍스트로 디코딩할 수 없을 때 발생
        logging.error(f"UnicodeDecodeError occurred for {binary_name}: {e}")
        result = "Decode Error"
    except OSError as e:
        # OSError: 운영체제 수준에서 발생하는 일반적인 오류를 처리
        logging.error(f"OSError occurred for {binary_name}: {e}")
        result = "OS Error"
    except subprocess.SubprocessError as e:
        # SubprocessError: subprocess 모듈에서 발생할 수 있는 모든 예외의 상위 클래스로
        # 이 핸들러는 TimeoutExpired나 CalledProcessError와 같은 구체적인 예외가 먼저 처리되지 않은 경우에
        # 다른 모든 subprocess 관련 예외를 처리하기 위해서 추가했습니다.
        logging.error(f"Unknown subprocess error occurred for {binary_name}: {e}")
        result = f"Unknown Error: {e}"
    return result
    