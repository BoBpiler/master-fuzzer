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
def compile_and_run(filepath, generator, id, compiler_info, optimization_level, random_flags=False):
    # key는 바이너리 경로이자 이름으로 result_dict를 구분하는 요소로 사용합니다.
    compiler = compiler_info['name']
    compiler_type = compiler_info['type']
    folder_name = compiler_info['folder_name']
    selected_flags = []

    if random_flags and folder_name == 'gcc' and optimization_level == '3':
        optimization_level = '2'
        random_num = random.randint(1, len(gcc_O3_flags))
        selected_flags = select_random_flags(gcc_O3_flags, random_num)

    key = f"{TEMP_DIRS[generator]}/{id}/{folder_name}_O{optimization_level}_flags{len(selected_flags) if random_flags else 0}"
    
    result_dict = {
        'id': id,
        'compiler': compiler,
        'optimization_level': optimization_level,
        'generator': generator,
        'flags': selected_flags if random_flags else None,  # 선택된 플래그 리스트. 랜덤 플래그가 아니라면 None.
        'num_flags': len(selected_flags) if random_flags else 0,  # 선택된 플래그의 개수. 랜덤 플래그가 아니라면 0.
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
        compile_result = compile(key, filepath, generator, id, compiler, optimization_level, selected_flags)
        
        # 발생할 수 있는 잠재적인 컴파일 실패 체크
        if not compile_result['status']:
            logging.warning("Compilation failed. Skipping run.")
            result_dict['compile'] = compile_result
            return (key, result_dict)
        
        result_dict['compile'] = compile_result
        
        #map 방식으로 해당 바이너리 이름과 실행 결과를 result_queue에 저장
        run_result = run_binary(key, compiler_info)
        result_dict['run'] = run_result

        # 큐에 결과를 저장
        return (key, result_dict)
        
    except Exception as e:
        logging.error(f"Unexpected error in compile_and_run for {filepath}: {e}")
        return ("error", None)


# compile 함수: 인자로 받은 조건으로 컴파일을 수행
# argv: binary_name - 바이너리 파일의 이름 및 경로/ path - 소스 코드 경로/ generator - 생성기 종류/ id - 소스코드 번호/ compiler - 컴파일러/ optimization_level - 최적화 옵션
# return: compile_result - 컴파일 결과 딕셔너리 반환 
def compile(binary_name, path, generator, id, compiler, optimization_level, selected_flags=None):
    # 컴파일 결과를 저장할 딕셔너리 초기화
    compile_result = {
        'status': None,
        'return_code': None,
        'error_type': None,
        'error_message': None
    }
    if selected_flags is None:
        selected_flags = []
    flag_str = " ".join(selected_flags)  # 선택된 플래그를 문자열로 변환
    try:
        #logging.info(f"Starting compile for {path} with {compiler} and optimization level {optimization_level}")
        # 바이너리 파일의 이름 

        if generator == 'yarpgen':
            # yarpgen 경우, 디렉터리 내의 모든 .c 파일을 컴파일 [compiler, *c_files, '-o', binary_name, f'-O{optimization_level}', f'-I{path}']
            c_files = [os.path.join(path, f) for f in ['driver.c', 'func.c']]
            result = subprocess.run( f'{compiler} {c_files[0]} {c_files[1]} -o {binary_name} -O{optimization_level} -I{path} {flag_str}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=compile_time_out)
            
        elif generator == 'csmith':
            # csmith의 경우 [compiler, path, '-o', binary_name, f'-O{optimization_level}', f'-I{csmith_include}']
            result = subprocess.run( f'{compiler} {path} -o {binary_name} -O{optimization_level} -I{csmith_include} {flag_str}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=compile_time_out)
        
        # 컴파일 실패시 넘어가기 
        if result.returncode != 0:
            compile_result['status'] = False
            compile_result['return_code'] = result.returncode
            compile_result['error_type'] = analyze_returncode(result.returncode, "compilation")
            compile_result['error_message'] = result.stderr.decode('utf-8')
            logging.warning(f"Compilation failed for {path} with return code {result.returncode}")
            return compile_result
        
        compile_result['status'] = True
        compile_result['return_code'] = result.returncode
        return compile_result
    
    except subprocess.TimeoutExpired as e:
        return handle_exception(e, TIMEOUT_ERROR, compile_result, binary_name)
    except subprocess.SubprocessError as e:
        return handle_exception(e, UNKNOWN_SUBPROCESS_ERROR, compile_result, binary_name)


# run_binary 함수: 바이너리를 실행하고, 실행 결과를 반환
# argv: binary_name - 바이너리 파일 이름 및 경로/ compiler - 크로스 컴파일 확인을 위함
# return: run_result - 바이너리 실행 결과를 담은 딕셔너리 반환
def run_binary(binary_name, compiler_info):
    run_result = {
        'status': None,
        'return_code': None,
        'error_type': None,
        'error_message': None,
        'result': None
    }
    
    compiler_type = compiler_info['type']
    #output_filename = f"results/{compiler}/{id}_{compiler}_O{optimization_level}.txt"
    try:
        #logging.info(f"Starting run_binary for {binary_name}")  ['qemu-aarch64-static', '-L', '/usr/aarch64-linux-gnu', f'./{binary_name}']
        binary_name_only = os.path.basename(binary_name)
        if compiler_type == 'cross-aarch64':
            result = subprocess.run(f'qemu-aarch64-static -L /usr/aarch64-linux-gnu ./{binary_name}', shell=True, capture_output=True, timeout=binary_time_out)
            print(f"{binary_name_only} Result obtained: {result.stdout.decode('utf-8')}")
        elif compiler_type == 'cross-riscv64':
            result = subprocess.run(f'qemu-riscv64-static ./{binary_name}', shell=True, capture_output=True, timeout=binary_time_out)
            print(f"{binary_name_only} Result obtained: {result.stdout.decode('utf-8')}")
        else:
            result = subprocess.run(f'./{binary_name}', shell=True, capture_output=True, timeout=binary_time_out)
            print(f"{binary_name_only} Result obtained: {result.stdout.decode('utf-8')}")
        
        # return code를 확인합니다.
        run_result['return_code'] = result.returncode
        if result.returncode != 0:
            run_result['status'] = False
            run_result['error_type'] = analyze_returncode(result.returncode, "execution")
            run_result['error_message'] = result.stderr.decode('utf-8')
        else:
            run_result['status'] = True
            run_result['result'] = result.stdout.decode('utf-8')
        return run_result
    except subprocess.TimeoutExpired as e:
        # TimeoutExpired: 프로세스가 지정된 시간 내에 완료되지 않았을 때 발생
        return handle_exception(e, TIMEOUT_ERROR, run_result, binary_name)
    except subprocess.CalledProcessError as e:
        # CalledProcessError: 명령어가 0이 아닌 상태 코드를 반환했을 때 발생 이 부분은 앞의 returncode랑 동일하지 않을까 싶습니다.
        return handle_exception(e, CALLED_PROCESS_ERROR, run_result, binary_name)
    except FileNotFoundError as e:
        # FileNotFoundError: 바이너리 파일을 찾을 수 없을 때 발생
        return handle_exception(e, FILE_NOT_FOUND_ERROR, run_result, binary_name)
    except PermissionError as e:
        # PermissionError: 바이너리 파일을 실행할 권한이 없을 때 발생
        return handle_exception(e, PERMISSION_ERROR, run_result, binary_name)
    except UnicodeDecodeError as e:
        # UnicodeDecodeError: 출력을 UTF-8 텍스트로 디코딩할 수 없을 때 발생
        return handle_exception(e, UNICODE_DECODE_ERROR, run_result, binary_name)
    except OSError as e:
        # OSError: 운영체제 수준에서 발생하는 일반적인 오류를 처리
        return handle_exception(e, OS_ERROR, run_result, binary_name)
    except subprocess.SubprocessError as e:
        # SubprocessError: subprocess 모듈에서 발생할 수 있는 모든 예외의 상위 클래스로
        # 이 핸들러는 TimeoutExpired나 CalledProcessError와 같은 구체적인 예외가 먼저 처리되지 않은 경우에
        # 다른 모든 subprocess 관련 예외를 처리하기 위해서 추가했습니다.
        return handle_exception(e, UNKNOWN_SUBPROCESS_ERROR, run_result, binary_name)
    
# 예외처리 함수 
def handle_exception(e, error_type, result, path):
    result['status'] = False
    result['error_message'] = str(e)

    context = 'execution' if 'result' in result else 'compilation'
    
    if hasattr(e, 'returncode'):
        result['return_code'] = e.returncode
        if error_type == CALLED_PROCESS_ERROR:
            error_type = analyze_returncode(e.returncode, context)
    else:
        result['return_code'] = None
    
    result['error_type'] = error_type
    logging.error(f"{error_type} occurred for {path}: {e}")
    return result