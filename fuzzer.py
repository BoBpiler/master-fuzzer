# fuzzer.py

from config import*
from CsmithGenerator import generate_c_code
from Analyzer import compare_results
from running_system import*
from comparison_strategies import basic_comparison
from concurrent.futures import ThreadPoolExecutor



# main 함수: 퍼징을 수행하는 총괄 코드
def main():
    # 디렉토리 초기화
    setup_output_dirs(compilers)
    completed_tasks = 0
    for id in range(0, total_tasks):  # 일단 요 정도만..
        # 소스코드 생성
        filepath = generate_c_code(id)
        results = {}
        with ThreadPoolExecutor() as executor:
            futures = []
            # 컴파일 및 실행 (gcc, clang으로 -O0 ~ -O3 옵션 주어서 컴파일 하고 실행 결과 저장)
            for compiler in compilers:
                for opt_level in optimization_levels:
                    futures.append(executor.submit(compile_and_run, filepath, id, compiler, opt_level, results))
                    
            for future in futures:
                future.result()
            
            compare_results(id, results, basic_comparison)
        
        # 진행률 업데이트 및 출력
        completed_tasks += 1
        progress = (completed_tasks / total_tasks) * 100
        print(f"Progress: {progress:.2f}% completed.")

if __name__ == "__main__":
    main()


