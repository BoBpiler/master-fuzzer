# Analyzer.py
# 테스트 케이스가 분석되면 적용해서 발전시켜보겠습니다.
from config import*
import shutil
import os
import json
import logging
logging.basicConfig(level=logging.INFO)

# compare_results 함수: 실행 결과를 비교 로직에 따라서 분석하는 함수
# argv: generator - 코드 생성기 종류/ id - 소스코드 번호/ results - 바이너리 실행 결과들/ comparison_strategy - 비교 로직
def analyze_results(generator, id, results):
    # 해당 결과들을 대상으로 비교
    try:
        if compare_execution_results(results):  # 실행 결과가 다른 경우
            print(f"Different results(checksum) detected for generator {generator}, source code ID: {id}")
            save_to_folder(generator, id, results, "checksum")
        else:
            crash_exists, crash_type = detect_crashes(results)  
            if crash_exists:                                    # 크래시가 있는 경우
                print(f"{crash_type} Crash detected for generator {generator}, source code ID: {id}")
                save_to_folder(generator, id, results, f"{crash_type.lower()}_crash")
                
            elif detect_partial_timeout(results):               # 부분적으로 타임아웃이 있는 경우 (어떻게 보면 결과가 다르다고 볼 수 있습니다.)
                print(f"Binary Execution Partial timeout detected for generator {generator}, source code ID: {id}")
                save_to_folder(generator, id, results, "partial_timeout")
            
            elif detect_abnormal_compile(results):              # 비정상적으로 컴파일이 수행되는 경우 (컴파일 타임아웃, 크래시 등...)
                print(f"Abnormal compile detected for generator {generator}, source code ID: {id}")
                save_to_folder(generator, id, results, "abnormal_compile")
    except Exception as e:
        logging.error(f"An unexpected error occurred in analyze_results for generator {generator} and task {id}: {e}")

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

    for key, result_dict in results.items():
        compile_status = result_dict['compile']['status']
        compile_error_type = result_dict['compile']['error_type']
        run_status = result_dict['run']['status']
        run_error_type = result_dict['run']['error_type']

        if compile_status == False and compile_error_type == CRASH:
            check_crash = True
            crash_type = "Compile"
            break 

        if run_status == False and run_error_type == CRASH:
            check_crash = True
            crash_type = "Binary"
            break

    return (check_crash, crash_type)


# detect_abnormal_compile 함수: 컴파일 과정에서 발생하는 에러를 탐지하는 함수 (프로세스 kill과 일반적인 컴파일 에러는 제외했습니다.)
# argv: results - 모든 결과가 담겨 있는 리스트
# return: true - 비정상 케이스가 존재함 저장해야 함/ false: 비정상 케이스 없음
def detect_abnormal_compile(results):
    for key, result_dict in results.items():
        compile_status = result_dict['compile']['status']
        return_code = result_dict['compile']['return_code']
        
        normalized_return_code = normalize_returncode(return_code)
        if not compile_status and normalized_return_code not in [0, 1, 9]:
            return True  # abnormal case 비정상 케이스 ex. 컴파일 타임아웃, 크래시 등..
    return False  # normal case 정상 케이스

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



# Analyzer 로직에 따라서 탐지된 파일을 저장하는 함수
def save_to_folder(generator, id, results, folder_name):
    id_folder_path = os.path.join(f"{CATCH_DIRS[generator]}", folder_name, str(id))
    if not os.path.exists(id_folder_path):
        os.makedirs(id_folder_path, exist_ok=True)

    if generator == 'yarpgen':
        for filename in ['driver.c', 'func.c', 'init.h']:  
            source_path = os.path.join(TEMP_DIRS[generator], str(id), filename)  
            dest_path = os.path.join(id_folder_path, filename)
            shutil.move(source_path, dest_path)
    elif generator == 'csmith':
        shutil.move(f"{TEMP_DIRS[generator]}/{id}/random_program_{id}.c", os.path.join(id_folder_path, f"random_program_{id}.c"))
    
    # 바이너리들 catch/binary 폴더에 저장
    for key in results.keys():
        if os.path.exists(key):
            binary_filename = os.path.basename(key)  
            shutil.move(key, os.path.join(id_folder_path, binary_filename))
    # 결과를 txt 파일에 저장 - 한 눈에 보기 좋습니다.
    save_results_to_file(id_folder_path, id, results)



# result_dict 딕셔너리를 가독성 좋게 txt 파일에 저장하는 함수입니다.
def save_results_to_file(id_folder_path, id, results):
    try:
        # txt 파일에 저장하는 부분
        with open(os.path.join(id_folder_path, f"{id}_result.txt"), 'w') as f:
            for Binary_Path, result_dict in results.items():
                f.write("########################################################################################\n")
                f.write(f"Binary_Path: {Binary_Path}\n")

                f.write(f"\nID: {result_dict['id']}")
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
        print(f"An error occurred while writing txt file: {e}")
    # JSON 파일에 저장하는 부분
    try:
        with open(os.path.join(id_folder_path, f"{id}_result.json"), 'w') as f:
            json.dump(results, f, indent=4) 
    except Exception as e:
        print(f"An error occurred while writing the json file: {e}")
