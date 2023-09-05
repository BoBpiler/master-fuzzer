# Analyzer.py

from config import TEMP_DIRS, CATCH_DIRS, CATCH_SUB_DIRS
import shutil
import os
import logging
logging.basicConfig(level=logging.INFO)

# compare_results 함수: 실행 결과를 비교 로직에 따라서 분석하는 함수
# argv: generator - 코드 생성기 종류/ id - 소스코드 번호/ results - 바이너리 실행 결과들/ comparison_strategy - 비교 로직
def compare_results(generator, id, results, comparison_strategy):
    # 해당 결과들을 대상으로 비교
    try:
        if comparison_strategy(results, id):
            print(f"Different results detected for generator {generator}, source code ID: {id}")
            # 소스코드 catch/source 폴더에 저장
            if generator == 'csmith':
                shutil.move(f"{TEMP_DIRS[generator]}/random_program_{id}.c", f"{CATCH_DIRS[generator]}/{CATCH_SUB_DIRS[0]}/random_program_{id}.c")
            elif generator == 'yarpgen':
                # yarpgen 소스코드 이름이 동일해서 구분을 위한 id 폴더 생성 
                id_folder_path = os.path.join(CATCH_DIRS[generator], CATCH_SUB_DIRS[0], str(id))
                if not os.path.exists(id_folder_path):
                    os.makedirs(id_folder_path, exist_ok=True)
                    #print(f"folder made {id_folder_path}")
                
                for filename in ['driver.c', 'func.c', 'init.h']:
                    source_path = os.path.join(TEMP_DIRS[generator], filename)
                    dest_path = os.path.join(id_folder_path, filename)
                    shutil.move(source_path, dest_path)     
            
            # 바이너리들 catch/binary 폴더에 저장
            for key in results.keys():  
                binary_filename = os.path.basename(key)  
                shutil.move(key, os.path.join(CATCH_DIRS[generator], CATCH_SUB_DIRS[1], binary_filename))

            # 결과 catch/result 폴더에 저장
            with open(os.path.join(CATCH_DIRS[generator], CATCH_SUB_DIRS[2], f"{id}_result.txt"), 'w') as f:
                for key, value in results.items():
                    f.write(f"{key}: {value}\n")
    except Exception as e:
        logging.error(f"An unexpected error occurred in compare_results for generator {generator} and task {id}: {e}")