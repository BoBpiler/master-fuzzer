from CsmithGenerator import generate_c_code
from Analyzer import compile_and_run
from concurrent.futures import ThreadPoolExecutor
import os

def main():
    compilers = ['gcc', 'clang']
    optimization_levels = ['0', '1', '2', '3']

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
    
    if not os.path.exists('catch'):
        os.mkdir('catch')
    
    for id in range(1, 11):  # 일단 요 정도만..
        filename = generate_c_code(id)
        with ThreadPoolExecutor() as executor:
            futures = []
            for compiler in compilers:
                for opt_level in optimization_levels:
                    futures.append(executor.submit(compile_and_run, filename, id, compiler, opt_level))
                    
            for future in futures:
                future.result()

if __name__ == "__main__":
    main()


