# fuzzer.py
# main: 퍼징을 수행하는 총괄 코드

from CsmithGenerator import generate_c_code
from Analyzer import compile_and_run
from concurrent.futures import ThreadPoolExecutor
from comparison_strategies import basic_comparison
import shutil
import os

# 함수: 결과를 비교하고 이상이 있다면 catch 디렉토리에 저장
def compare_results(id, compilers, optimization_levels, comparison_strategy):
    results = {}  # 결과를 저장하는 딕셔너리  {'compiler_opt': result_content}
    
    #하나의 소스코드에 대해서 만들어진 모든 바이너리의 실행 결과를 저장
    for compiler in compilers:
        for opt_level in optimization_levels:
            filepath = f"results/{compiler}/{id}_{compiler}_O{opt_level}.txt"

            with open(filepath, 'r') as f:
                result_content = f.read().strip()

            if result_content == "Timeout":
                continue

            results[f"{compiler}_O{opt_level}"] = result_content
    # 타임 아웃 처리
    if not results:
        print(f"No results to compare for source code ID: {id}")
        return

    # 해당 결과들을 대상으로 비교
    if comparison_strategy(results, id):
        print(f"Different results detected for source code ID: {id}")
        shutil.copy(f"RandomCodes/random_program_{id}.c", f"catch/random_program_{id}.c")

# 메인 함수
def main():
    compilers = ['gcc', 'clang']
    optimization_levels = ['0', '1', '2', '3']

    # 진행률 관련 변수
    total_tasks = 10000  # 일단 요 정도만..
    completed_tasks = 0

    # 디렉토리 초기화
    if not os.path.exists('RandomCodes'):
        os.mkdir('RandomCodes')
    
    if not os.path.exists('results'):
        os.mkdir('results')
        for compiler in compilers:
            os.mkdir(f'results/{compiler}')
    
    if not os.path.exists('temp'):
        os.mkdir('temp')
        for compiler in compilers:
            os.mkdir(f'temp/{compiler}')

    if not os.path.exists('binaries'):
        os.mkdir('binaries')
        for compiler in compilers:
            os.mkdir(f'binaries/{compiler}')
    
    if not os.path.exists('catch'):
        os.mkdir('catch')
    
    for id in range(0, 10000):  # 일단 요 정도만..
        # 소스코드 생성
        filename = generate_c_code(id)
        with ThreadPoolExecutor() as executor:
            futures = []
            # 컴파일 및 실행 (gcc, clang으로 -O0 ~ -O3 옵션 주어서 컴파일 하고 실행 결과 저장)
            for compiler in compilers:
                for opt_level in optimization_levels:
                    futures.append(executor.submit(compile_and_run, filename, id, compiler, opt_level))
                    
            for future in futures:
                future.result()
        
        # 결과 비교
        compare_results(id, compilers, optimization_levels, basic_comparison)
        
        # 진행률 업데이트 및 출력
        completed_tasks += 1
        progress = (completed_tasks / total_tasks) * 100
        print(f"Progress: {progress:.2f}% completed.")

if __name__ == "__main__":
    main()


