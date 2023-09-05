# fuzzer.py

from config import*
from CodeGenerator import generate_c_code
from Analyzer import compare_results
from running_system import*
from comparison_strategies import basic_comparison
from validator import validate_code
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import logging

logging.basicConfig(level=logging.WARNING)
# process_generator 함수: 생성기 별로 퍼징을 수행하는 함수
# argv: generator - 생성기 종류 (현재 csmith와 yarpgen)
# return: None 
def process_generator(generator):
    completed_tasks = 0
    skipped_tasks = 0
    result_queue = Queue()  # 스레드 안전한 큐 생성
    try:
        for id in range(0, total_tasks):
            # 소스코드 생성
            print(f"****************************************generated by {generator}: {id} task started*********************************************")
            filepath = generate_c_code(id, generator)
            #logging.info(f"Source code generated for task {id} using {generator}: {filepath}")
            #logging.info(f"Submitting tasks for compilation and execution for task {id}")
            with ThreadPoolExecutor() as executor:
                futures = []
                # 컴파일 및 실행 (gcc, clang으로 -O0 ~ -O3 옵션 주어서 컴파일 하고 실행 결과 저장)
                for compiler in compilers:
                    for opt_level in optimization_levels:
                        futures.append(executor.submit(compile_and_run, filepath, generator, id, compiler, opt_level, result_queue))
                        
                for future in futures:
                    future.result()
            
            # 큐에서 결과를 수집하여 results 딕셔너리에 저장
            #logging.info(f"Results fetched for task {id} from result_queue")
            if not result_queue.empty():  # 큐가 비어 있지 않을 경우에만 실행
                results = {}
                while not result_queue.empty():
                    key, result = result_queue.get()
                    results[key] = result
                compare_results(generator, id, results, basic_comparison)
            else:
                # 큐가 비어 있는 경우에 대한 처리 - 모든 컴파일이 실패 되었음
                logging.warning(f"All compilation failed for task {id} using {generator}")
            
            # Temp 폴더 청소
            #logging.info(f"Temp files cleaned for task {id}")
            cleanup_temp(generator)
            # 진행률 업데이트 및 출력
            completed_tasks += 1
            progress = (completed_tasks / total_tasks) * 100
            print(f"Progress for {generator}: {progress:.2f}% completed. skipped count: {skipped_tasks}")
            print(f"****************************************generated by {generator}: {id} task finished*********************************************")
    except Exception as e:
        logging.error(f"An unexpected error occurred in process_generator for generator {generator} and task {id}: {e}")


# main 함수: 퍼징을 수행하는 총괄 코드
def main():
    # 디렉토리 초기화
    setup_output_dirs(generators)
    with ThreadPoolExecutor() as executor:
        executor.map(process_generator, generators)

if __name__ == "__main__":
    main()


