# running_system.py 
# 컴파일하고 바이너리를 실행하는 함수들이 담겨 있습니다. :)

from utils import*
import os
import subprocess
import signal

# compile_and_run 함수: compile 함수와  run_binary 함수를 통해서 특정 컴파일러와 옵션으로 컴파일 후에 실행 결과를 저장
# argv: filepath - 소스 코드 경로/ id - 소스코드 번호/ compiler - 컴파일러/ optimization_level - 최적화 옵션/ results - 실행 결과 저장할 딕셔너리(map)
# return: 사실상 results_queue에 저장됩니다.
def compile_and_run(dir_path, temp_dirs, generator_config, id, compiler_info, optimization_level, logger, random_seed=None):
    # key는 바이너리 경로이자 이름으로 result_dict를 구분하는 요소로 사용합니다.
    generator_name = generator_config["name"]
    binary_name = os.path.join(temp_dirs, f'{id}', f"{compiler_info['file_name']}_{optimization_level[1:]}")
    
    result_dict = {
        'id': str(id),
        'random_Seed': str(random_seed),
        'compiler': compiler_info['name'],
        'optimization_level': optimization_level,
        'generator': generator_name,
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
        compile_result = compile(binary_name, dir_path, generator_config, id, compiler_info, optimization_level, logger)
        
        # 발생할 수 있는 잠재적인 컴파일 실패 체크
        if not compile_result['status']:
            #logging.warning("Compilation failed. Skipping run.")
            result_dict['compile'] = compile_result
            return (binary_name, result_dict)
        
        result_dict['compile'] = compile_result
        
        #map 방식으로 해당 바이너리 이름과 실행 결과를 result_queue에 저장
        run_result = run_binary(binary_name, generator_config, compiler_info, logger)
        result_dict['run'] = run_result

        # 큐에 결과를 저장
        return (binary_name, result_dict)
        
    except Exception as e:
        logger.error(f"Unexpected error in compile_and_run for {dir_path}: {e}")
        return ("error", None)


# compile 함수: 인자로 받은 조건으로 컴파일을 수행
# argv: binary_name - 바이너리 파일의 이름 및 경로/ path - 소스 코드 경로/ generator - 생성기 종류/ id - 소스코드 번호/ compiler - 컴파일러/ optimization_level - 최적화 옵션
# return: compile_result - 컴파일 결과 딕셔너리 반환 
def compile(binary_name, dir_path, generator_config, id, compiler_info, optimization_level, logger):
    # 컴파일 결과를 저장할 딕셔너리 초기화
    compile_result = {
        'status': None,
        'return_code': None,
        'error_type': None,
        'error_message': None
    }
    try:
        # 바이너리 파일의 이름 
        src_files = [file.format(path=dir_path, id=id) for file in generator_config['src_files']]
        include_dir = generator_config['include_dir'].format(path=dir_path, id=id)
        optimization_option = optimization_level
        compiler_path = compiler_info['language'][generator_config['language']]['binary_path']
        
        additional_info = {}
        if 'prepare_command' in compiler_info:
            obj_path = compiler_info['prepare_command'](dir_path, optimization_level)
            additional_info['obj_path'] = obj_path

        command = compiler_info['output_format'].format(
            compiler_path=compiler_path,
            optimization=optimization_option,
            include_dir=include_dir,
            src_files=" ".join(src_files),
            obj_path=additional_info.get('obj_path', ""),
            exe_path=binary_name
        )
        if platform.system() == 'Linux':
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid, text=True)
        else:
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        stdout, stderr = proc.communicate(timeout=compile_time_out)
        returncode = proc.returncode
        # 컴파일 실패시 넘어가기 
        if returncode != 0:
            compile_result['status'] = False
            compile_result['return_code'] = returncode
            compile_result['error_type'] = analyze_returncode(returncode, "compilation")
            compile_result['error_message'] = stdout + stderr
            logger.warning(f"Compilation failed for {dir_path} with return code {returncode}")
            return compile_result
        
        compile_result['status'] = True
        compile_result['return_code'] = returncode
        return compile_result
    
    except subprocess.TimeoutExpired as e:
        terminate_process_and_children(proc.pid)
        if platform.system() == 'Linux':
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)  # 타임아웃 발생 시, 프로세스 종료
        else:
            proc.terminate()
        return handle_exception(e, TIMEOUT_ERROR, compile_result, binary_name, logger)
    except subprocess.SubprocessError as e:
        return handle_exception(e, UNKNOWN_SUBPROCESS_ERROR, compile_result, binary_name, logger)


# run_binary 함수: 바이너리를 실행하고, 실행 결과를 반환
# argv: binary_name - 바이너리 파일 이름 및 경로/ compiler - 크로스 컴파일 확인을 위함
# return: run_result - 바이너리 실행 결과를 담은 딕셔너리 반환
def run_binary(binary_name, generator_config, compiler_info, logger):
    run_result = {
        'status': None,
        'return_code': None,
        'error_type': None,
        'error_message': None,
        'result': None
    }
    
    try:
        binary_name_only = os.path.basename(binary_name)
        command = compiler_info['language'][generator_config['language']]['execute'].format(exe_path=binary_name)
        try:
            if platform.system() == 'Linux':
                proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid, text=True)
            else:
                proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            stdout, stderr = proc.communicate(timeout=binary_time_out)
            returncode = proc.returncode
            
            # return code를 확인합니다.
            run_result['return_code'] = returncode
            if returncode != 0:
                run_result['status'] = False
                run_result['error_type'] = analyze_returncode(returncode, "execution")
                run_result['error_message'] = stdout + stderr
            else:
                run_result['status'] = True
                run_result['result'] = stdout
                #print(f"{binary_name_only} Result obtained: {stdout}")
            return run_result
        except subprocess.TimeoutExpired as e:
            # TimeoutExpired: 프로세스가 지정된 시간 내에 완료되지 않았을 때 발생
            terminate_process_and_children(proc.pid)
            if platform.system() == 'Linux':
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            else:
                proc.terminate()
            return handle_exception(e, TIMEOUT_ERROR, run_result, binary_name, logger)
        except subprocess.CalledProcessError as e:
            # CalledProcessError: 명령어가 0이 아닌 상태 코드를 반환했을 때 발생 이 부분은 앞의 returncode랑 동일하지 않을까 싶습니다.
            return handle_exception(e, CALLED_PROCESS_ERROR, run_result, binary_name, logger)
    except FileNotFoundError as e:
        # FileNotFoundError: 바이너리 파일을 찾을 수 없을 때 발생
        return handle_exception(e, FILE_NOT_FOUND_ERROR, run_result, binary_name, logger)
    except PermissionError as e:
        # PermissionError: 바이너리 파일을 실행할 권한이 없을 때 발생
        return handle_exception(e, PERMISSION_ERROR, run_result, binary_name, logger)
    except UnicodeDecodeError as e:
        # UnicodeDecodeError: 출력을 UTF-8 텍스트로 디코딩할 수 없을 때 발생
        return handle_exception(e, UNICODE_DECODE_ERROR, run_result, binary_name, logger)
    except OSError as e:
        # OSError: 운영체제 수준에서 발생하는 일반적인 오류를 처리
        return handle_exception(e, OS_ERROR, run_result, binary_name, logger)
    except subprocess.SubprocessError as e:
        # SubprocessError: subprocess 모듈에서 발생할 수 있는 모든 예외의 상위 클래스로
        # 이 핸들러는 TimeoutExpired나 CalledProcessError와 같은 구체적인 예외가 먼저 처리되지 않은 경우에
        # 다른 모든 subprocess 관련 예외를 처리하기 위해서 추가했습니다.
        return handle_exception(e, UNKNOWN_SUBPROCESS_ERROR, run_result, binary_name, logger)
    
# run_binary 함수: 바이너리를 실행하고, 실행 결과를 반환
# argv: binary_name - 바이너리 파일 이름 및 경로/ compiler - 크로스 컴파일 확인을 위함
# return: run_result - 바이너리 실행 결과를 담은 딕셔너리 반환
def run_binary_for_wasm(runner_name, runner_command, compile_result, binary_name, generator_config, id, compiler_info, optimization_level, logger, random_seed):
    
    result_dict = {
        'id': str(id),
        'random_Seed': str(random_seed),
        'compiler': f"{compiler_info['name']}_{runner_name}",
        'optimization_level': optimization_level,
        'generator': generator_config["name"],
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
    result_dict['compile'] = compile_result
    run_result = {
        'status': None,
        'return_code': None,
        'error_type': None,
        'error_message': None,
        'result': None
    }
    
    try:
        key = f"{binary_name}_{runner_name}"
        binary_name_only = os.path.basename(binary_name) + f"_{runner_name}"
        command = runner_command.format(exe_path=binary_name)
        try:
            if platform.system() == 'Linux':
                proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid, text=True)
            else:
                proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            stdout, stderr = proc.communicate(timeout=binary_time_out)
            returncode = proc.returncode
            
            # return code를 확인합니다.
            run_result['return_code'] = returncode
            if returncode != 0:
                run_result['status'] = False
                run_result['error_type'] = analyze_returncode(returncode, "execution")
                run_result['error_message'] = stdout + stderr
            else:
                run_result['status'] = True
                run_result['result'] = stdout
                #print(f"{binary_name_only} Result obtained: {stdout}")
            result_dict['run'] = run_result
            
            return (key, result_dict)
        except subprocess.TimeoutExpired as e:
            # TimeoutExpired: 프로세스가 지정된 시간 내에 완료되지 않았을 때 발생
            terminate_process_and_children(proc.pid)
            if platform.system() == 'Linux':
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            else:
                proc.terminate()
            result_dict['run'] = handle_exception(e, TIMEOUT_ERROR, run_result, binary_name, logger)
            return (key, result_dict)
        except subprocess.CalledProcessError as e:
            # CalledProcessError: 명령어가 0이 아닌 상태 코드를 반환했을 때 발생 이 부분은 앞의 returncode랑 동일하지 않을까 싶습니다.
            result_dict['run'] = handle_exception(e, CALLED_PROCESS_ERROR, run_result, binary_name, logger)
            return (key, result_dict) 
    except FileNotFoundError as e:
        # FileNotFoundError: 바이너리 파일을 찾을 수 없을 때 발생
        result_dict['run'] = handle_exception(e, FILE_NOT_FOUND_ERROR, run_result, binary_name, logger)
        return (key, result_dict)
    except PermissionError as e:
        # PermissionError: 바이너리 파일을 실행할 권한이 없을 때 발생
        result_dict['run'] = handle_exception(e, PERMISSION_ERROR, run_result, binary_name, logger)
        return (key, result_dict)
    except UnicodeDecodeError as e:
        # UnicodeDecodeError: 출력을 UTF-8 텍스트로 디코딩할 수 없을 때 발생
        result_dict['run'] = handle_exception(e, UNICODE_DECODE_ERROR, run_result, binary_name, logger)
        return (key, result_dict)
    except OSError as e:
        # OSError: 운영체제 수준에서 발생하는 일반적인 오류를 처리
        result_dict['run'] = handle_exception(e, OS_ERROR, run_result, binary_name, logger)
        return (key, result_dict)
    except subprocess.SubprocessError as e:
        # SubprocessError: subprocess 모듈에서 발생할 수 있는 모든 예외의 상위 클래스로
        # 이 핸들러는 TimeoutExpired나 CalledProcessError와 같은 구체적인 예외가 먼저 처리되지 않은 경우에
        # 다른 모든 subprocess 관련 예외를 처리하기 위해서 추가했습니다.
        result_dict['run'] = handle_exception(e, UNKNOWN_SUBPROCESS_ERROR, run_result, binary_name, logger)
        return (key, result_dict)
    
# 예외처리 함수 
def handle_exception(e, error_type, result, path, logger):
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
    logger.error(f"{error_type} occurred for {path}: {e}")
    return result