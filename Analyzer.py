# Analyzer.py
# 테스트 케이스가 분석되면 적용해서 발전시켜보겠습니다.
from config import*
import shutil
import os
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
        
        elif detect_crashes(results):  # 크래시가 있는 경우
            print(f"Crash detected for generator {generator}, source code ID: {id}")
            save_to_folder(generator, id, results, "crash")
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

    for key, result_dict in results.items():
        compile_status = result_dict['compile']['status']
        compile_error_type = result_dict['compile']['error_type']
        run_status = result_dict['run']['status']
        run_error_type = result_dict['run']['error_type']

        if compile_status == False and compile_error_type == SEGFAULT:
            check_crash = True
            break 

        if run_status == False and run_error_type == SEGFAULT:
            check_crash = True
            break

    return check_crash



# 체크섬이나 크래시 폴더에 파일을 저장하는 함수
def save_to_folder(generator, id, results, folder_name):
    id_folder_path = os.path.join(f"{CATCH_DIRS[generator]}", folder_name, str(id))
    if not os.path.exists(id_folder_path):
        os.makedirs(id_folder_path, exist_ok=True)

    if generator == 'yarpgen':
        for filename in ['driver.c', 'func.c', 'init.h']:  
            source_path = os.path.join(TEMP_DIRS[generator], filename)  
            dest_path = os.path.join(id_folder_path, filename)
            shutil.move(source_path, dest_path)
    elif generator == 'csmith':
        shutil.move(f"{TEMP_DIRS[generator]}/random_program_{id}.c", os.path.join(id_folder_path, f"random_program_{id}.c"))
    
    # 바이너리들 catch/binary 폴더에 저장
    for key in results.keys():
        if os.path.exists(key):
            binary_filename = os.path.basename(key)  
            shutil.move(key, os.path.join(id_folder_path, binary_filename))
    
    with open(os.path.join(id_folder_path, f"{id}_result.txt"), 'w') as f:
        for key, value in results.items():
            f.write(f"{key}: {value}\n")

