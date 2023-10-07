from config import *
import concurrent.futures
import logging

def compile_and_run(compilers, id, generator_name, input_src):
    results = {} # 모든 결과를 기록함
    run_tasks = []  # 바이너리 병렬 실행을 위한 작업 목록

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(compiler.compile, input_src) for compiler in compilers]
        compile_results = {compilers[i].name: future.result() for i, future in enumerate(futures)}

    error_compilers = []

    for compiler_name, compile_result in compile_results.items():
        if "exit_code" in compile_result:
            error_compilers.append(compiler_name)
            continue
        else:
            for optimization_level, status in compile_result["result"].items():
                binary_path, result_dict = init_result(compile_result['binary_base'], id, generator_name, compiler_name, optimization_level)
                
                # 컴파일 결과를 result_dict에 저장
                if status == "0":
                    result_dict['compile']['status'] = True
                    result_dict['compile']['return_code'] = status
                    run_tasks.append((binary_path, result_dict))
                else:
                    result_dict['compile']['return_code'] = status
                    result_dict['compile']['status'] = False
                    # results에 결과 저장
                    results[binary_path] = result_dict
    if error_compilers:
        return (None, error_compilers)
    else:
        # binary run 
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = []
            for binary_path, result_dict in run_tasks:
                futures.append(executor.submit(run_binary, binary_path, result_dict))

            # 작업 완료 및 결과 저장
            for future in futures:
                binary_path, result_dict = future.result()
                results[binary_path] = result_dict
        return (results, [])



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
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        proc.kill()
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

