from concurrent.futures import ProcessPoolExecutor
from running_system import compile_and_run, run_binary_for_wasm
from utils import get_machine_info, TIMEOUT_ERROR
import os 
import platform
import re

def check_for_duplicated_bug(compilers, results, dir_path, temp_dirs, catch_dirs, generator_config, id, logger, random_seed):
    # LL을 ULL로 변경하는 방식으로 중복된 버그인지 판단
    generator_name = generator_config["name"]
    
    is_duplicated_by_ULL = False
    is_duplicated_by_long = False
    is_duplicated_by_infinite_loop = False

    if platform.system() == 'Windows':  # Windows
        is_duplicated_by_ULL = detect_bug_type_ULL(compilers, dir_path, temp_dirs, catch_dirs, generator_config, id, logger, random_seed)
    elif platform.system() == 'Linux':  # Linux
        is_duplicated_by_long = detect_emcc_issue_type_long(compilers, dir_path, temp_dirs, catch_dirs, generator_config, id, logger, random_seed)
        is_duplicated_by_infinite_loop = detect_bug_type_infinite_loop(results)

    # TODO: 앞으로 추가될 다른 판단 로직들도 여기에서 호출
    # 예: is_duplicated_by_another_method = detect_bug_by_another_method(source_code_path, generator, id, random_seed)
    
    # 모든 판단 로직의 결과를 종합하여 중복된 버그인지 최종 판단
    # 현재는 is_duplicated_by_ULL만 있어서 일단 이렇게 사용

    is_duplicated = is_duplicated_by_ULL or is_duplicated_by_long or is_duplicated_by_infinite_loop  # 둘 중 하나라도 True이면 중복으로 판단
    
    # if is_duplicated:
    #     print(f"Bug in source code (generator: {generator_name}, source code ID: {id}) is DUPLICATED.")
    # else:
    #     print(f"Bug in source code (generator: {generator_name}, source code ID: {id}) is NOT duplicated.")
    
    return is_duplicated


def analyze_results_for_duplicate(temp_dirs, catch_dirs, generator_config, id, random_seed, results, machine_info, logger, partial_timeout=True):
    # 해당 결과들을 대상으로 비교
    from Analyzer import compare_execution_results
    generator_name = generator_config['name']
    try:
        if compare_execution_results(results):  # 실행 결과가 다른 경우
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"An unexpected error occurred in analyze_results_for_duplicate for generator {generator_name} and task {id}: {e}")


def fuzz(compilers, dir_path, temp_dirs, catch_dirs, generator_config, id, logger, random_seed, partial_timeout=True):
    machine_info = get_machine_info(logger)
    generator_name = generator_config["name"]
    with ProcessPoolExecutor() as executor:
        futures = []
        results = {}
        for compiler_info in compilers.values():
            for opt_level in compiler_info['options']:
                if 'runners' not in compiler_info['language'][generator_config['language']]: # 일반 컴파일러의 경우
                    futures.append(executor.submit(compile_and_run, dir_path, temp_dirs, generator_config, id, compiler_info, opt_level, logger, random_seed))
                else:
                    binary_name = os.path.join(temp_dirs, f'{id}', f"{compiler_info['file_name']}_{opt_level[1:]}")
                    compile_result = compile(binary_name, dir_path, generator_config, id, compiler_info, opt_level, logger)
                    if compile_result['status']: # 컴파일이 성공한 경우에만 실행
                        for runner_name, runner_command in compiler_info['language'][generator_config['language']]['runners'].items():
                            futures.append(executor.submit(run_binary_for_wasm, runner_name, runner_command, compile_result, binary_name, generator_config, id, compiler_info, opt_level, logger, random_seed))
                    else:
                        result_dict = {
                            'id': str(id),
                            'random_Seed': str(random_seed),
                            'compiler': compiler_info['name'],
                            'optimization_level': opt_level,
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
                        result_dict['compile'] = compile_result
                        futures.append((binary_name, result_dict))  # 컴파일 실패 결과를 futures에 추가
        
        for future in futures:
            if isinstance(future, tuple):
                key, result_dict = future
            else:
                result = future.result()
                if result is not None:
                    key, result_dict = result
            if key == "error": # 에러 처리
                continue
            results[key] = result_dict
    
    if len(results) > 0: 
        result = analyze_results_for_duplicate(temp_dirs, catch_dirs, generator_config, id, random_seed, results, machine_info, logger, partial_timeout)
    else:
        logger.critical(f"CRITICAL ERROR: This is an exceptional case which means impossible and requires immediate attention.")
    return result


def modify_source_LL_to_ULL(source_code_path):
    """ 소스코드 파일에서 LL을 ULL로 변경합니다. """
    directory = os.path.dirname(source_code_path)
    base_name = os.path.basename(source_code_path)
    new_name = os.path.splitext(base_name)[0] + "_LL" + os.path.splitext(base_name)[1]
    new_path = os.path.join(directory, new_name)
    os.rename(source_code_path, new_path)

    with open(new_path, 'r') as file:
        text = file.read()
    modified_text = re.sub(r'(0x[0-9a-fA-F]+)LL', r'\1ULL', text)

    with open(source_code_path, 'w') as file:
        file.write(modified_text)
    return source_code_path

# emcc에서 발생하는 long 타입에 대해 4바이트로 판단하는 경우를 long long으로 바꾸는 함수
def modify_source_long_to_longlong(source_code_path):
    """ 소스코드 파일에서 long을 long long으로 변경하고, unsigned long을 unsigned long long으로 변경합니다. """

    # 백업 파일명 생성
    directory = os.path.dirname(source_code_path)
    base_name = os.path.basename(source_code_path)
    new_name = os.path.splitext(base_name)[0] + "_long_to_longlong" + os.path.splitext(base_name)[1]
    new_path = os.path.join(directory, new_name)
    os.rename(source_code_path, new_path)

    with open(new_path, 'r') as file:
        text = file.read()
    
    # unsigned long을 unsigned long long으로 변경
    text = re.sub(r'\bunsigned long\b(?! long)', 'unsigned long long', text)
    
    # long을 long long으로 변경
    text = re.sub(r'(?<!long\s)\blong\b(?! long)', 'long long', text)

    with open(source_code_path, 'w') as file:
        file.write(text)
    
    return source_code_path

# long에서 발생하는 emcc issue 중복 validate 함수 (long -> long long 변환 후 다시 테스트)
def detect_emcc_issue_type_long(compilers, dir_path, temp_dirs, catch_dirs, generator_config, id, logger, random_seed):
    generator_name = generator_config["name"]
    src_files = [file.format(path=dir_path, id=id) for file in generator_config['src_files_to_send']]
    
    for src_file in src_files:
        modify_source_long_to_longlong(src_file)  # long을 long long으로 변환하는 함수를 사용

    result = fuzz(compilers, dir_path, temp_dirs, catch_dirs, generator_config, id, logger, random_seed)
    if result:
        # True인 경우 중복된 버그가 아님
        # print(f"`long` type related emcc issue NOT found in modified source code (generator: {generator_name}, source code ID: {id}).")
        return False
    else:
        # False인 경우 중복된 버그로 판단
        # print(f"`long` type related emcc issue found: Mistakenly recognizing `long` as a different size in source code (generator: {generator_name}, source code ID: {id}).")
        return True


# cl에서 발생하는 LL 처리에 대한 버그 중복 validate 함수 LL -> ULL 로 변환 후 다시 테스트 
def detect_bug_type_ULL(compilers, dir_path, temp_dirs, catch_dirs, generator_config, id, logger, random_seed):
    generator_name = generator_config["name"]
    src_files = [file.format(path=dir_path, id=id) for file in generator_config['src_files_to_send']]
    
    for src_file in src_files:
        modify_source_LL_to_ULL(src_file)

    result = fuzz(compilers, dir_path, temp_dirs, catch_dirs, generator_config, id, logger, random_seed)
    if result:
        # True인 경우 중복된 버그가 아님
        # print(f"Unsigned long long (ULL) related bug NOT found in modified source code (generator: {generator_name}, source code ID: {id}).")
        return False
    else:
        # False인 경우 중복된 버그로 판단
        # print(f"Unsigned long long (ULL) related bug found: Mistakenly recognizing unsigned as signed in source code (generator: {generator_name}, source code ID: {id}).")
        return True

def detect_bug_type_infinite_loop(results):
    O0_timeout = False
    other_level_issues = False

    for key, result_dict in results.items():
        compile_status = result_dict['compile']['status']
        run_status = result_dict['run']['status']
        run_error_type = result_dict['run']['error_type']
        optimization_level = result_dict['optimization_level']
        run_result = result_dict['run']['result']
        
        # 컴파일이 성공한 경우만 확인
        if compile_status:
            # -O0에서 타임아웃 발생 확인 (ground truth)
            if optimization_level == "-O0" and run_status == False and run_error_type == TIMEOUT_ERROR:
                O0_timeout = True

            # -O0 이외의 최적화 레벨에서 체크섬 값의 존재나 다른 에러 존재
            elif optimization_level != "-O0":
                if run_result or run_error_type != TIMEOUT_ERROR:
                    other_level_issues = True

    # -O0에서 타임아웃 발생과 다른 최적화 레벨에서의 문제가 모두 발견된 경우만 True 반환 
    return O0_timeout and other_level_issues
