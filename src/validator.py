from concurrent.futures import ProcessPoolExecutor
from running_system import compile_and_run
from Analyzer import*
import re
import logging

def check_for_duplicated_bug(dir_path, temp_dirs, catch_dirs, generator_config, id, random_seed):
    # LL을 ULL로 변경하는 방식으로 중복된 버그인지 판단
    generator_name = generator_config["name"]
    is_duplicated_by_ULL = detect_bug_type_ULL(dir_path, temp_dirs, catch_dirs, generator_config, id, random_seed)
    
    # TODO: 앞으로 추가될 다른 판단 로직들도 여기에서 호출
    # 예: is_duplicated_by_another_method = detect_bug_by_another_method(source_code_path, generator, id, random_seed)
    
    # 모든 판단 로직의 결과를 종합하여 중복된 버그인지 최종 판단
    # 현재는 is_duplicated_by_ULL만 있어서 일단 이렇게 사용
    is_duplicated = is_duplicated_by_ULL
    
    if is_duplicated:
        print(f"Bug in source code (generator: {generator_name}, source code ID: {id}) is DUPLICATED.")
    else:
        print(f"Bug in source code (generator: {generator_name}, source code ID: {id}) is NOT duplicated.")
    
    return is_duplicated


def analyze_results_for_duplicate(temp_dirs, catch_dirs, generator_config, id, random_seed, results, machine_info, partial_timeout=True):
    # 해당 결과들을 대상으로 비교
    generator_name = generator_config['name']
    try:
        if compare_execution_results(results):  # 실행 결과가 다른 경우
            return True
        else:
            crash_exists, crash_type = detect_crashes(results)  
            if crash_exists:                                    # 크래시가 있는 경우
                msg = f"{crash_type} Crash detected for generator {generator_name}, source code ID: {id}"
                print(msg)
                id_folder_path = save_to_folder(temp_dirs, catch_dirs, generator_name, id, results, f"{crash_type.lower()}_crash")
                send_telegram_message(machine_info, generator_config, id, random_seed, f"{crash_type} Crash", msg, id_folder_path, "medium")
                return True

            elif partial_timeout and detect_partial_timeout(results):               # 부분적으로 타임아웃이 있는 경우 (어떻게 보면 결과가 다르다고 볼 수 있습니다.)
                print(f"Binary Execution Partial timeout detected for generator {generator_name}, source code ID: {id}")
                save_to_folder(temp_dirs, catch_dirs, generator_name, id, results, "partial_timeout")
                return True
            
            elif detect_abnormal_compile(results):              # 비정상적으로 컴파일이 수행되는 경우 (컴파일 타임아웃, 크래시 등...)
                msg = f"Abnormal compile detected for generator {generator_name}, source code ID: {id}"
                print(msg)
                id_folder_path = save_to_folder(temp_dirs, catch_dirs, generator_name, id, results, "abnormal_compile")
                send_telegram_message(machine_info, generator_config, id, random_seed, "Abnormal Compile", msg, id_folder_path)
                return True
            
            elif detect_abnormal_binary(results):  # 바이너리 returncode가 0이 아닌 경우가 하나라도 있는 경우 
                msg = f"Abnormal binary detected for generator {generator_name}, source code ID: {id}"
                print(msg)
                id_folder_path = save_to_folder(temp_dirs, catch_dirs, generator_name, id, results, "abnormal_binary")
                send_telegram_message(machine_info, generator_config, id, random_seed, "Abnormal Binary", msg, id_folder_path)
                return True
            else:
                return False

    except Exception as e:
        logging.error(f"An unexpected error occurred in analyze_results for generator {generator_name} and task {id}: {e}")


def fuzz(dir_path, temp_dirs, catch_dirs, generator_config, id, random_seed, partial_timeout=True):
    machine_info = get_machine_info()
    with ProcessPoolExecutor() as executor:
        futures = []
        results = {}
        for compiler_info in compilers.values():
            for opt_level in compiler_info['options']:
                futures.append(executor.submit(compile_and_run, dir_path, temp_dirs, generator_config, id, compiler_info, opt_level, random_seed))
        
        for future in futures:
            result = future.result()
            if result is not None:
                key, result_dict = result
                if key == "error": # 에러 처리
                    continue
                results[key] = result_dict
    
    if len(results) > 0: 
        result = analyze_results_for_duplicate(temp_dirs, catch_dirs, generator_config, id, random_seed, results, machine_info, partial_timeout)
    else:
        logging.critical(f"CRITICAL ERROR: This is an exceptional case which means impossible and requires immediate attention.")
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



def detect_bug_type_ULL(dir_path, temp_dirs, catch_dirs, generator_config, id, random_seed):
    generator_name = generator_config["name"]
    src_files = [file.format(path=dir_path, id=id) for file in generator_config['src_files']]
    if len(src_files) > 1:
        return False
    
    # if generator_name != "csmith":
    #     return False

    modified_path = modify_source_LL_to_ULL(src_files[0])

    result = fuzz(dir_path, temp_dirs, catch_dirs, generator_config, id, random_seed)
    if result:
        # True인 경우 중복된 버그가 아님
        print(f"Unsigned long long (ULL) related bug NOT found in modified source code (generator: {generator_name}, source code ID: {id}).")
        return False
    else:
        # False인 경우 중복된 버그로 판단
        print(f"Unsigned long long (ULL) related bug found: Mistakenly recognizing unsigned as signed in source code (generator: {generator_name}, source code ID: {id}).")
        return True
