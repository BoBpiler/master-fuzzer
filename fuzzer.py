# fuzzer.py

from config import*
from CodeGenerator import generate_c_code
from Analyzer import compare_results
from running_system import*
from comparison_strategies import basic_comparison
from validator import validate_code
from concurrent.futures import ThreadPoolExecutor
import logging

logging.basicConfig(level=logging.WARNING)
# process_generator 함수: 생성기 별로 퍼징을 수행하는 함수
# argv: generator - 생성기 종류 (현재 csmith와 yarpgen)
# return: None 
def process_generator(generator):
    completed_tasks = 0
    for id in range(0, total_tasks):
        # 소스코드 생성
        filepath = generate_c_code(id, generator)
        # 각 컴파일러에 대한 소스코드 검증
        is_valid_for_all_compilers = True
        for compiler in compilers:
            is_valid = validate_code(filepath, generator, id, compiler)
            if not is_valid:
                is_valid_for_all_compilers = False
                break

        if not is_valid_for_all_compilers:
            logging.warning(f"Source code {filepath} failed to compile for one or more compilers. Skipping.")
            continue
        results = {}
        with ThreadPoolExecutor() as executor:
            futures = []
            # 컴파일 및 실행 (gcc, clang으로 -O0 ~ -O3 옵션 주어서 컴파일 하고 실행 결과 저장)
            for compiler in compilers:
                for opt_level in optimization_levels:
                    futures.append(executor.submit(compile_and_run, filepath, generator, id, compiler, opt_level, results))
                    
            for future in futures:
                future.result()
            
            compare_results(generator, id, results, basic_comparison)
        
        # Temp 폴더 청소
        cleanup_temp(generator)
        # 진행률 업데이트 및 출력
        completed_tasks += 1
        progress = (completed_tasks / total_tasks) * 100
        print(f"Progress for {generator}: {progress:.2f}% completed.")


# main 함수: 퍼징을 수행하는 총괄 코드
def main():
    # 디렉토리 초기화
    setup_output_dirs(generators)
    with ThreadPoolExecutor() as executor:
        executor.map(process_generator, generators)

if __name__ == "__main__":
    main()


