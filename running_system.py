# running_system.py 
# 컴파일하고 바이너리를 실행하는 함수들이 담겨 있습니다. :)

from config import *
from queue import Queue
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO)

# compile_and_run 함수: compile 함수와  run_binary 함수를 통해서 특정 컴파일러와 옵션으로 컴파일 후에 실행 결과를 저장
# argv: filepath - 소스 코드 경로/ id - 소스코드 번호/ compiler - 컴파일러/ optimization_level - 최적화 옵션/ results - 실행 결과 저장할 딕셔너리(map)
# return: 사실상 results_queue에 저장됩니다.
def compile_and_run(filepath, generator, id, compiler, optimization_level, result_queue):
    # key는 바이너리 경로이자 이름으로 result_dict를 구분하는 요소로 사용합니다.
    # clang의 크로스 컴파일의 경우 옵션을 주어야 해서 해당 compiler 이름으로 경로 만들면 띄어쓰기 문제가 있어서 해당 if 문 추가 
    if compiler == 'clang --target=aarch64-linux-gnu':                
        key = f"{TEMP_DIRS[generator]}/{id}/clang--target=aarch64-linux-gnu_O{optimization_level}"
    else:
        key = f"{TEMP_DIRS[generator]}/{id}/{compiler}_O{optimization_level}"
    
    result_dict = {
        'id': id,
        'compiler': compiler,
        'optimization_level': optimization_level,
        'generator': generator,
        'compile': {
            'status': None,
            'return_code': None,
            'error_type': None,
            'error_message': None
        },
        'run': {
            'status': None,
            'return_code': None,
            'error_type': None,
            'error_message': None,
            'result': None
        }
    }
    try:
        #logging.info(f"Starting compile_and_run for {filepath} with {compiler} and optimization level {optimization_level}")
        compile_result = compile(key, filepath, generator, id, compiler, optimization_level)
        
        # 발생할 수 있는 잠재적인 컴파일 실패 체크
        if not compile_result['status']:
            logging.warning("Compilation failed. Skipping run.")
            result_dict['compile'] = compile_result
            result_queue.put((key, result_dict))
            return
        
        result_dict['compile'] = compile_result
        
        #map 방식으로 해당 바이너리 이름과 실행 결과를 result_queue에 저장
        run_result = run_binary(key, compiler)
        result_dict['run'] = run_result

        # 큐에 결과를 저장
        result_queue.put((key, result_dict))
        
    except Exception as e:
        logging.error(f"Unexpected error in compile_and_run for {filepath}: {e}")


# compile 함수: 인자로 받은 조건으로 컴파일을 수행
# argv: binary_name - 바이너리 파일의 이름 및 경로/ path - 소스 코드 경로/ generator - 생성기 종류/ id - 소스코드 번호/ compiler - 컴파일러/ optimization_level - 최적화 옵션
# return: compile_result - 컴파일 결과 딕셔너리 반환 
def compile(binary_name, path, generator, id, compiler, optimization_level):
    # 컴파일 결과를 저장할 딕셔너리 초기화
    compile_result = {
        'status': None,
        'return_code': None,
        'error_type': None,
        'error_message': None
    }

    try:
        #logging.info(f"Starting compile for {path} with {compiler} and optimization level {optimization_level}")
        # 바이너리 파일의 이름 

        if generator == 'yarpgen':
            # yarpgen 경우, 디렉터리 내의 모든 .c 파일을 컴파일 [compiler, *c_files, '-o', binary_name, f'-O{optimization_level}', f'-I{path}']
            c_files = [os.path.join(path, f) for f in ['driver.c', 'func.c']]
            result = subprocess.run( f'{compiler} {c_files[0]} {c_files[1]} -o {binary_name} -O{optimization_level} -I{path}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=compile_time_out)
            # 컴파일 실패시 넘어가기 
            if result.returncode != 0:
                compile_result['status'] = False
                compile_result['return_code'] = result.returncode
                compile_result['error_type'] = analyze_returncode(result.returncode, result.stderr.decode('utf-8'), "compilation")
                compile_result['error_message'] = result.stderr.decode('utf-8')
                logging.warning(f"Compilation failed for {path} with return code {result.returncode}")
                return compile_result
        elif generator == 'csmith':
            # csmith의 경우 [compiler, path, '-o', binary_name, f'-O{optimization_level}', f'-I{csmith_include}']
            result = subprocess.run( f'{compiler} {path} -o {binary_name} -O{optimization_level} -I{csmith_include}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=compile_time_out)
            # 컴파일 실패시 넘어가기 
            if result.returncode != 0:
                compile_result['status'] = False
                compile_result['return_code'] = result.returncode
                compile_result['error_type'] = analyze_returncode(result.returncode, result.stderr.decode('utf-8'), "compilation")
                compile_result['error_message'] = result.stderr.decode('utf-8')
                logging.warning(f"Compilation failed for {path} with return code {result.returncode}")
                return compile_result
        compile_result['status'] = True
        compile_result['return_code'] = result.returncode
        return compile_result
    except subprocess.TimeoutExpired:
        compile_result['status'] = False
        compile_result['error_type'] = TIMEOUT_ERROR
        compile_result['error_message'] = 'Compilation timed out'
        logging.warning(f"Compilation timed out for {path}")
        return compile_result
    except subprocess.SubprocessError as e:
        compile_result['status'] = False
        compile_result['error_type'] = UNKNOWN_SUBPROCESS_ERROR
        compile_result['error_message'] = str(e)
        logging.error(f"Unexpected error in subprocess compile for {path}: {e}")
        return compile_result


# run_binary 함수: 바이너리를 실행하고, 실행 결과를 반환
# argv: binary_name - 바이너리 파일 이름 및 경로/ compiler - 크로스 컴파일 확인을 위함
# return: run_result - 바이너리 실행 결과를 담은 딕셔너리 반환
def run_binary(binary_name, compiler):
    run_result = {
        'status': None,
        'return_code': None,
        'error_type': None,
        'error_message': None,
        'result': None
    }
    #output_filename = f"results/{compiler}/{id}_{compiler}_O{optimization_level}.txt"
    try:
        #logging.info(f"Starting run_binary for {binary_name}")  ['qemu-aarch64-static', '-L', '/usr/aarch64-linux-gnu', f'./{binary_name}']
        binary_name_only = os.path.basename(binary_name)
        if compiler == 'aarch64-linux-gnu-gcc' or compiler == 'clang --target=aarch64-linux-gnu':
            result = subprocess.run(f'qemu-aarch64-static -L /usr/aarch64-linux-gnu ./{binary_name}', shell=True, capture_output=True, timeout=binary_time_out)
            print(f"{binary_name_only} Result obtained: {result.stdout.decode('utf-8')}")
        else:
            result = subprocess.run(f'./{binary_name}', shell=True, capture_output=True, timeout=binary_time_out)
            print(f"{binary_name_only} Result obtained: {result.stdout.decode('utf-8')}")
        
        # return code를 확인합니다.
        run_result['return_code'] = result.returncode
        if result.returncode != 0:
            run_result['status'] = False
            run_result['error_type'] = analyze_returncode(result.returncode, result.stdout.decode('utf-8'), "execution")
            run_result['error_message'] = result.stderr.decode('utf-8')
        else:
            run_result['status'] = True
            run_result['result'] = result.stdout.decode('utf-8')
        return run_result
    except subprocess.TimeoutExpired:
        # TimeoutExpired: 프로세스가 지정된 시간 내에 완료되지 않았을 때 발생
        run_result['status'] = False
        run_result['error_type'] = TIMEOUT_ERROR
        run_result['error_message'] = "TimeoutExpired occurred in {binary_name}"
        logging.warning(f"TimeoutExpired occurred in {binary_name}")
        return run_result
    #except subprocess.CalledProcessError as e:
        # CalledProcessError: 명령어가 0이 아닌 상태 코드를 반환했을 때 발생 이 부분은 앞의 returncode랑 동일하지 않을까 싶습니다.
        run_result['status'] = False
        run_result['error_type'] = CALLED_PROCESS_ERROR
        run_result['return_code'] = e.returncode
        run_result['error_message'] = e.stderr.decode('utf-8')
        logging.error(f"CalledProcessError occurred in {binary_name}: {e}")
        return run_result
    except FileNotFoundError as e:
        # FileNotFoundError: 바이너리 파일을 찾을 수 없을 때 발생
        run_result['status'] = False
        run_result['error_type'] = FILE_NOT_FOUND_ERROR
        run_result['error_message'] = str(e)
        logging.error(f"FileNotFoundError occurred for {binary_name}: {e}")
        return run_result
    except PermissionError as e:
        # PermissionError: 바이너리 파일을 실행할 권한이 없을 때 발생
        run_result['status'] = False
        run_result['error_type'] = PERMISSION_ERROR
        run_result['error_message'] = str(e)
        logging.error(f"PermissionError occurred for {binary_name}: {e}")
        return run_result
    except UnicodeDecodeError as e:
        # UnicodeDecodeError: 출력을 UTF-8 텍스트로 디코딩할 수 없을 때 발생
        run_result['status'] = False
        run_result['error_type'] = UNICODE_DECODE_ERROR
        run_result['error_message'] = str(e)
        logging.error(f"UnicodeDecodeError occurred for {binary_name}: {e}")
        return run_result
    except OSError as e:
        # OSError: 운영체제 수준에서 발생하는 일반적인 오류를 처리
        run_result['status'] = False
        run_result['error_type'] = OS_ERROR
        run_result['error_message'] = str(e)
        logging.error(f"OSError occurred for {binary_name}: {e}")
        return run_result
    except subprocess.SubprocessError as e:
        # SubprocessError: subprocess 모듈에서 발생할 수 있는 모든 예외의 상위 클래스로
        # 이 핸들러는 TimeoutExpired나 CalledProcessError와 같은 구체적인 예외가 먼저 처리되지 않은 경우에
        # 다른 모든 subprocess 관련 예외를 처리하기 위해서 추가했습니다.
        run_result['status'] = False
        run_result['error_type'] = UNKNOWN_SUBPROCESS_ERROR
        run_result['error_message'] = str(e)
        logging.error(f"Unknown subprocess error occurred for {binary_name}: {e}")
        return run_result
    