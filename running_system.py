from config import *
import concurrent.futures
import logging
import signal
def compile_and_run(compiler, id, generator_name, input_src):
    result_dict = {
            'id': str(id),
            'compiler': compiler.name,
            'optimization_level': compiler.optimization_option,
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
    
    compile_result = compiler.compile(input_src)
    if "exit_code" in compile_result:
        result_dict['compile']['status'] = False
        result_dict['compile']['return_code'] = compile_result['exit_code']
        result_dict['compile']['error_type'] = "CompilerError"
        result_dict['compile']['error_message'] = compile_result['error_message']
        return compile_result['binary_base'], result_dict, compiler
    
    for opt_level, status in compile_result["result"].items():
        result_dict['compile']['status'] = True
        result_dict['compile']['return_code'] = status
        binary_path = compile_result['binary_base']        
        binary_path, result_dict = run_binary(binary_path, result_dict)
    return (binary_path, result_dict, None)


def init_result(binary_base, id, generator_name, compiler_name, optimization_level):

    binary_path = f"{binary_base}{optimization_level}"
    result_dict = {
        'id': str(id),
        'compiler': compiler_name,
        'optimization_level': optimization_level,
        'generator': generator_name,
        'compile': {'status': None, 'return_code': None, 'error_type': None, 'error_message': None},
        'run': {'status': None, 'return_code': None, 'error_type': None, 'error_message': None, 'result': None}
    }

    return binary_path, result_dict


def run_binary(binary_path, result_dict):
    run_result = {
        'status': None,
        'return_code': None,
        'error_type': None,
        'error_message': None,
        'result': None
    }

    try:
        command = f'{binary_path}'
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        stdout, stderr = proc.communicate(timeout=binary_time_out)
        returncode = proc.returncode
        # return code를 확인합니다.
        run_result['return_code'] = returncode
        if returncode != 0:
            run_result['status'] = False
            run_result['error_type'] = analyze_returncode(returncode, "execution")
            run_result['error_message'] = stderr.decode('utf-8')
        else:
            run_result['status'] = True
            run_result['result'] = stdout.decode('utf-8')
            print(f"{binary_path} Result obtained: {stdout.decode('utf-8')}")
        
        result_dict['run'] = run_result
        return (binary_path, result_dict)
    except subprocess.TimeoutExpired as e:
        # TimeoutExpired: 프로세스가 지정된 시간 내에 완료되지 않았을 때 발생
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        result_dict['run'] = handle_exception(e, TIMEOUT_ERROR, run_result, binary_path)
        return (binary_path, result_dict)
    except subprocess.CalledProcessError as e:
        # CalledProcessError: 명령어가 0이 아닌 상태 코드를 반환했을 때 발생 이 부분은 앞의 returncode랑 동일하지 않을까 싶습니다.
        result_dict['run'] = handle_exception(e, CALLED_PROCESS_ERROR, run_result, binary_path)
        return (binary_path, result_dict)
    except FileNotFoundError as e:
        # FileNotFoundError: 바이너리 파일을 찾을 수 없을 때 발생
        result_dict['run'] = handle_exception(e, FILE_NOT_FOUND_ERROR, run_result, binary_path)
        return (binary_path, result_dict)
    except PermissionError as e:
        # PermissionError: 바이너리 파일을 실행할 권한이 없을 때 발생
        result_dict['run'] = handle_exception(e, PERMISSION_ERROR, run_result, binary_path)
        return (binary_path, result_dict)
    except UnicodeDecodeError as e:
        # UnicodeDecodeError: 출력을 UTF-8 텍스트로 디코딩할 수 없을 때 발생
        result_dict['run'] = handle_exception(e, UNICODE_DECODE_ERROR, run_result, binary_path)
        return (binary_path, result_dict)
    except OSError as e:
        # OSError: 운영체제 수준에서 발생하는 일반적인 오류를 처리
        result_dict['run'] = handle_exception(e, OS_ERROR, run_result, binary_path)
        return (binary_path, result_dict)
    except subprocess.SubprocessError as e:
        # SubprocessError: subprocess 모듈에서 발생할 수 있는 모든 예외의 상위 클래스로
        # 이 핸들러는 TimeoutExpired나 CalledProcessError와 같은 구체적인 예외가 먼저 처리되지 않은 경우에
        # 다른 모든 subprocess 관련 예외를 처리하기 위해서 추가했습니다.
        result_dict['run'] = handle_exception(e, UNKNOWN_SUBPROCESS_ERROR, run_result, binary_path)
        return (binary_path, result_dict)


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
