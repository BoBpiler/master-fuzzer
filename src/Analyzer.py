# Analyzer.py
# 테스트 케이스가 분석되면 적용해서 발전시켜보겠습니다.
from utils import*
from validator import check_for_duplicated_bug
from fuzzer_display import*
import shutil
import os
import json

# compare_results 함수: 실행 결과를 비교 로직에 따라서 분석하는 함수
# argv: generator - 코드 생성기 종류/ id - 소스코드 번호/ results - 바이너리 실행 결과들/ comparison_strategy - 비교 로직
def analyze_results(compilers, dir_path, temp_dirs, catch_dirs, generator_config, id, random_seed, results, machine_info, status_info, status_lock, logger, partial_timeout=True):
    # 해당 결과들을 대상으로 비교
    generator_name = generator_config['name']
    try:
        if compare_execution_results(results):  # 실행 결과가 다른 경우
            if check_for_duplicated_bug(compilers, dir_path, temp_dirs, catch_dirs, generator_config, id, logger, random_seed):
                with status_lock:
                    temp_status = dict(status_info)
                    temp_status[generator_name]["duplicated_counts"] += 1
                    temp_status["total"]["duplicated_counts"] += 1
                    status_info.update(temp_status)
                return False
            msg = f"Different results(checksum) detected for generator {generator_name}, source code ID: {id}"
            #print(msg)
            id_folder_path = save_to_folder(temp_dirs, catch_dirs, generator_name, id, results, "checksum", logger)
            send_telegram_message(machine_info, generator_config, id, random_seed, "Different Checksum", msg, id_folder_path, "high")
            with status_lock:
                temp_status = dict(status_info)
                temp_status[generator_name]["different_checksums"] += 1
                temp_status["total"]["different_checksums"] += 1
                temp_status[generator_name]["High"] += 1
                temp_status["total"]["High"] += 1
                status_info.update(temp_status)
            return True
        else:
            crash_exists, crash_type = detect_crashes(results)  
            if crash_exists:                                    # 크래시가 있는 경우
                msg = f"{crash_type} Crash detected for generator {generator_name}, source code ID: {id}"
                #print(msg)
                id_folder_path = save_to_folder(temp_dirs, catch_dirs, generator_name, id, results, f"{crash_type.lower()}_crash", logger)
                send_telegram_message(machine_info, generator_config, id, random_seed, f"{crash_type} Crash", msg, id_folder_path, "medium")
                with status_lock:
                    temp_status = dict(status_info)
                    temp_status[generator_name][f"{crash_type.lower()}_crashes"] += 1
                    temp_status["total"][f"{crash_type.lower()}_crashes"] += 1
                    temp_status[generator_name]["Medium"] += 1
                    temp_status["total"]["Medium"] += 1
                    status_info.update(temp_status)
                return True

            elif partial_timeout and detect_partial_timeout(results):               # 부분적으로 타임아웃이 있는 경우 (어떻게 보면 결과가 다르다고 볼 수 있습니다.)
                #print(f"Binary Execution Partial timeout detected for generator {generator_name}, source code ID: {id}")
                save_to_folder(temp_dirs, catch_dirs, generator_name, id, results, "partial_timeout", logger)
                with status_lock:
                    temp_status = dict(status_info)
                    temp_status[generator_name]["partial_timeouts"] += 1
                    temp_status["total"]["partial_timeouts"] += 1
                    temp_status[generator_name]["Low"] += 1
                    temp_status["total"]["Low"] += 1
                    status_info.update(temp_status)
                return True
            
            elif detect_abnormal_compile(results):              # 비정상적으로 컴파일이 수행되는 경우 (컴파일 타임아웃, 크래시 등...)
                msg = f"Abnormal compile detected for generator {generator_name}, source code ID: {id}"
                #print(msg)
                id_folder_path = save_to_folder(temp_dirs, catch_dirs, generator_name, id, results, "abnormal_compile", logger)
                send_telegram_message(machine_info, generator_config, id, random_seed, "Abnormal Compile", msg, id_folder_path)
                with status_lock:
                    temp_status = dict(status_info)
                    temp_status[generator_name]["abnormal_compiles"] += 1
                    temp_status["total"]["abnormal_compiles"] += 1
                    temp_status[generator_name]["Low"] += 1
                    temp_status["total"]["Low"] += 1
                    status_info.update(temp_status)
                return True
            
            elif detect_abnormal_binary(results):  # 바이너리 returncode가 0이 아닌 경우가 하나라도 있는 경우 
                msg = f"Abnormal binary detected for generator {generator_name}, source code ID: {id}"
                #print(msg)
                id_folder_path = save_to_folder(temp_dirs, catch_dirs, generator_name, id, results, "abnormal_binary", logger)
                send_telegram_message(machine_info, generator_config, id, random_seed, "Abnormal Binary", msg, id_folder_path)
                with status_lock:
                    temp_status = dict(status_info)
                    temp_status[generator_name]["abnormal_binaries"] += 1
                    temp_status["total"]["abnormal_binaries"] += 1
                    temp_status[generator_name]["Low"] += 1
                    temp_status["total"]["Low"] += 1
                    status_info.update(temp_status)
                return True
            else:
                return False

    except Exception as e:
        logger.error(f"An unexpected error occurred in analyze_results for generator {generator_name} and task {id}: {e}")

# compare_execution_results 함수: 컴파일 성공하고 잘 실행된 바이너리의 결과들을 비교하는 함수
# argv: results - 모든 결과가 담겨 있는 리스트
# return: true - 다른 결과가 존재함 저장해야 함/ false: 결과가 동일함
def compare_execution_results(results):
    check_diff_results = False
    temp_run_result = None
    for key, result_dict in results.items():
        compile_status = result_dict['compile']['status']
        run_status = result_dict['run']['status']
        run_result = result_dict['run']['result']

        if compile_status == True:
            if temp_run_result is None and run_status == True:
                temp_run_result = run_result

            if run_status == True and run_result != temp_run_result:
                check_diff_results = True
                break
    return check_diff_results


# detect_crashes 함수: 컴파일 과정 혹은 바이너리 실행 과정에서 crash가 발생하는 것을 탐지하는 함수
# argv: results - 모든 결과가 담겨 있는 리스트
# return: true - crash 존재함 저장해야 함/ false: crash 없음
def detect_crashes(results):
    check_crash = False
    crash_type = None

    total_binary_crashes = 0
    total_binaries = 0

    for key, result_dict in results.items():
        compile_status = result_dict['compile']['status']
        compile_error_type = result_dict['compile']['error_type']

        if compile_status == False:
            if compile_error_type == CRASH or \
               "Access Violation" in compile_error_type or \
               "Stack Overflow" in compile_error_type:
                check_crash = True
                crash_type = "Compile"
                return (check_crash, crash_type) 
        else:
            run_status = result_dict['run']['status']
            run_error_type = result_dict['run']['error_type']
            total_binaries += 1
            if run_status == False:
                if run_error_type == CRASH or \
                "Access Violation" in run_error_type or \
                "Stack Overflow" in run_error_type:
                    total_binary_crashes += 1

    if 0 < total_binary_crashes < total_binaries:
        check_crash = True
        crash_type = "Binary"

    return (check_crash, crash_type)


# detect_abnormal_compile 함수: 컴파일 과정에서 발생하는 에러를 탐지하는 함수 (프로세스 kill과 일반적인 컴파일 에러는 제외했습니다.)
# argv: results - 모든 결과가 담겨 있는 리스트
# return: true - 비정상 케이스가 존재함 저장해야 함/ false: 비정상 케이스 없음
def detect_abnormal_compile(results):
    for key, result_dict in results.items():
        compile_status = result_dict['compile']['status']
        return_code = result_dict['compile']['return_code']
        if return_code is not None:         # None인 경우도 고려
            normalized_return_code = normalize_returncode(return_code)
            if not compile_status and normalized_return_code not in [0, 1, 9]:
                return True  # abnormal case 비정상 케이스 ex. 컴파일 타임아웃, 크래시 등..
    return False  # normal case 정상 케이스


# detect_abnormal_binary 함수: 바이너리 실행이 실패했으나 returncode가 0이 아닌 경우를 탐지하는 함수
# argv: results - 모든 결과가 담겨 있는 리스트
# return: true - 조건에 맞는 경우가 하나라도 있음 저장해야 함 / false: 조건에 맞는 경우가 없음 저장 안해도 됨
def detect_abnormal_binary(results):
    abnormal_count = 0
    total_count = 0

    for key, result_dict in results.items():
        compile_status = result_dict['compile']['status']
        run_status = result_dict['run']['status']
        run_return_code = result_dict['run']['return_code']

        if compile_status:  # 컴파일이 성공한 경우만 카운트
            total_count += 1
            if run_status == False:
                if run_return_code != 0 or run_return_code is None:  # None도 고려 (time out)
                    abnormal_count += 1

    return abnormal_count > 0 and abnormal_count < total_count  # abnormal_count가 0보다 크고, 나머지 바이너리 수보다 작아야 합니다.



# detect_partial_timeout 함수: 바이너리 실행했을 때 부분적으로만 타임아웃이 발생하는 경우를 탐지하는 함수
# argv: results - 모든 결과가 담겨 있는 리스트
# return: true - 부분적으로만 타임아웃이 발생함 저장해야 함/ false: 부분적으로만 타임아웃 발생하지 않음 저장 안해도 됨
def detect_partial_timeout(results):
    timeout_count = 0
    total_count = 0

    for key, result_dict in results.items():
        compile_status = result_dict['compile']['status']
        run_status = result_dict['run']['status']
        run_error_type = result_dict['run']['error_type']

        if compile_status:  # 컴파일이 성공한 경우만 카운트
            total_count += 1
            if run_status == False and run_error_type == TIMEOUT_ERROR:
                timeout_count += 1
    return timeout_count > 0 and timeout_count < total_count    # 타임아웃이 존재하고 실행된 바이너리 수보다 타임아웃이 작아야 합니다. 즉, 부분적으로만 타임아웃 발생


import time

def retry_move(src, dest, retries=3, delay=1):
    for i in range(retries):
        try:
            shutil.move(src, dest)
            return
        except Exception as e:
            if i == retries - 1:  # 마지막 시도에서도 실패하면 오류를 발생시킵니다.
                raise e
            time.sleep(delay)  # 간단한 딜레이 후 재시도합니다.


# Analyzer 로직에 따라서 탐지된 파일을 저장하는 함수
def save_to_folder(temp_dirs, catch_dirs, generator_name, id, results, folder_name, logger):
    id_folder_path = os.path.join(catch_dirs, folder_name, str(id))
    if not os.path.exists(id_folder_path):
        os.makedirs(id_folder_path, exist_ok=True)

    # TEMP_DIRS[generator]/id/ 폴더 내의 모든 파일을 옮기기
    temp_dir_path = os.path.join(temp_dirs, str(id))
    for filename in os.listdir(temp_dir_path):
        source_path = os.path.join(temp_dir_path, filename)
        dest_path = os.path.join(id_folder_path, filename)
        try:
            retry_move(source_path, dest_path)
        except Exception as e:
            logger.error(f"Error moving {source_path} to {dest_path}. Exception: {e}")

    # 결과를 txt 파일에 저장 - 한 눈에 보기 좋습니다.
    save_results_to_file(id_folder_path, id, results, logger)
    return id_folder_path


# result_dict 딕셔너리를 가독성 좋게 txt 파일에 저장하는 함수입니다.
def save_results_to_file(id_folder_path, id, results, logger):
    try:
        # txt 파일에 저장하는 부분
        result_files = get_result_file_names(id)
        with open(os.path.join(id_folder_path, f"{result_files['txt']}"), 'w') as f:
            for Binary_Path, result_dict in results.items():
                f.write("########################################################################################\n")
                f.write(f"Binary_Path: {Binary_Path}\n")

                f.write(f"\nID: {result_dict['id']}")
                f.write(f"\nRandom Seed: {result_dict['random_Seed']}")
                f.write(f"\nCompiler: {result_dict['compiler']}")
                f.write(f"\nOptimization Level: {result_dict['optimization_level']}")
                f.write(f"\nCode Generator: {result_dict['generator']}")
                
                f.write("\n\nCompile:\n")
                for key, value in result_dict['compile'].items():
                    if key == 'error_message' and value is not None:
                        f.write("\tError Message:\n")
                        f.write("\t-----\n")
                        for line in value.split('\n'):
                            f.write(f"\t\t{line}\n")
                        f.write("\t-----\n")
                    else:
                        f.write(f"\t{key.capitalize()}: {value}\n")
                    
                f.write("\nRun:\n")
                for key, value in result_dict['run'].items():
                    if key == 'error_message' and value is not None:
                        f.write("\tError Message:\n")
                        f.write("\t-----\n")
                        for line in value.split('\n'):
                            f.write(f"\t\t{line}\n")
                        f.write("\t-----\n")
                    else:
                        f.write(f"\t{key.capitalize()}: {value}\n")
    except Exception as e:
        logger.error(f"An error occurred while writing txt file: {e}")
    # JSON 파일에 저장하는 부분
    try:
        with open(os.path.join(id_folder_path, f"{result_files['json']}"), 'w') as f:
            json.dump(results, f, indent=4, default=str)    # uuid serialized 문제 -> default = str
    except Exception as e:
        logger.error(f"An error occurred while writing the json file: {e}")
