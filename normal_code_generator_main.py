import os
import secrets
import subprocess
import logging
import uuid
import time
from normal_generator_config import*




# generate_c_code 함수: Csmith와 yarpgen을 통해서 C 코드를 랜덤으로 생성
# argv: id - 소스코드 번호
# return: filepath - 생성된 파일 이름 및 경로
def generate_c_code(id, generator):
    try:
        dir_path = f'{TEMP_DIRS[generator]}/{id}'   
        random_seed = id
        filepath = f'{dir_path}/{id}.c'
        
        # 폴더가 없으면 생성
        if not os.path.exists(dir_path):    
            os.makedirs(dir_path)
        
        csmith_env= os.environ.copy()
        if generator == 'csmith':
            csmith_env["PATH"] = f"{csmith_env['PATH']}:{os.path.expanduser('~')}/csmith/bin"
            #csmith_include = f"{os.path.expanduser('~')}/csmith/include"
            # C 코드 생성 ['csmith', '-o', filepath]
            result = subprocess.run(f'csmith {csmith_options} -o {filepath} --seed {random_seed}', shell=True, env=csmith_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=generator_time_out)
            if result.returncode != 0:
                logging.warning(f"{generator} code generation failed for {filepath} with return code {result.returncode}, error message: {result.stdout + result.stderr}")
                return (None, None)
            return (filepath, random_seed)
        elif generator == 'yarpgen':
            yarpgen_options_str = ' '.join(yarpgen_options)
            result = subprocess.run(f'yarpgen {yarpgen_options_str} -o {dir_path} --seed={random_seed} --mutation-seed={random_seed}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=generator_time_out)
            if result.returncode != 0:
                logging.warning(f"{generator} code generation failed for {dir_path} with return code {result.returncode}, error message: {result.stdout + result.stderr}")
                return (None, None)
            return (dir_path, None)
        else:
            return (None, None)
    except subprocess.TimeoutExpired:
        logging.warning(f"Code generation timed out for generator {generator} and task {id}")
        return (None, None)
    except Exception as e:
        logging.error(f"An unexpected error occurred in generate_c_code for generator {generator} and task {id}: {e}")
        return (None, None)


if __name__ == "__main__":
    generator = input("Enter the generator (csmith/yarpgen): ").strip()
    repeat_times = 10000
    successful_generations = 0
    failed_generations = 0
    start_time = time.time()
    for i in range(repeat_times):
        id = i
        filepath, random_seed = generate_c_code(id, generator)
        
        if filepath is not None:
            print(f"Generated code at {filepath} with seed {random_seed}")
            successful_generations += 1
        else:
            print(f"Failed to generate code")
            failed_generations += 1

    end_time = time.time()

    elapsed_time = end_time - start_time
    print(f"\nTotal time for generating {repeat_times} codes: {elapsed_time:.2f} seconds")
    print(f"Successfully generated {successful_generations} codes")
    print(f"Failed to generate {failed_generations} codes")
