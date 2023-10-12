# CodeGenerator.py
# 생성기를 이용해서 소스코드를 생성하는 함수

from config import TEMP_DIRS, generator_time_out, csmith_options, yarpgen_options, yarpgen_scalar_options
import os
import subprocess
import logging
logging.basicConfig(level=logging.INFO) 
import secrets

# generate_c_code 함수: Csmith와 yarpgen을 통해서 C 코드를 랜덤으로 생성
# argv: id - 소스코드 번호
# return: filepath - 생성된 파일 이름 및 경로
def generate_c_code(id, generator):
    try:
        dir_path = f'{TEMP_DIRS[generator]}/{id}'   
        random_seed = secrets.randbelow(4294967296)
        filepath = f'{dir_path}/random_program_{id}.c'
        
        
        # 폴더가 없으면 생성
        if not os.path.exists(dir_path):    
            os.makedirs(dir_path)
        
        csmith_env= os.environ.copy()
        if generator == 'csmith':
            csmith_env["PATH"] = f"{csmith_env['PATH']}:{os.path.expanduser('~')}/csmith/bin"
            #csmith_include = f"{os.path.expanduser('~')}/csmith/include"
            # C 코드 생성 ['csmith', '-o', filepath]
            result = subprocess.run(f'{generator} {csmith_options} -o {filepath} --seed {random_seed}', shell=True, env=csmith_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=generator_time_out)
            if result.returncode != 0:
                logging.warning(f"{generator} code generation failed for {filepath} with return code {result.returncode}, error message: {result.stdout + result.stderr}")
                return (None, None)
            return (filepath, random_seed)
        elif generator == 'yarpgen':
            yarpgen_options_str = ' '.join(yarpgen_options)
            result = subprocess.run(f'{generator} {yarpgen_options_str} -o {dir_path} --seed={random_seed} --mutation-seed={random_seed}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=generator_time_out)
            if result.returncode != 0:
                logging.warning(f"{generator} code generation failed for {dir_path} with return code {result.returncode}, error message: {result.stdout + result.stderr}")
                return (None, None)
            return (dir_path, random_seed)
        elif generator == 'yarpgen_scalar':
            yarpgen_scalar_options_str = ' '.join(yarpgen_scalar_options)
            result = subprocess.run(f'{generator} {yarpgen_scalar_options_str} -d {dir_path} --seed={random_seed}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=generator_time_out)
            if result.returncode != 0:
                logging.warning(f"{generator} code generation failed for {dir_path} with return code {result.returncode}, error message: {result.stdout + result.stderr}")
                return (None, None)
            return (dir_path, random_seed)
        else:
            return (None, None)
    except subprocess.TimeoutExpired:
        logging.warning(f"Code generation timed out for generator {generator} and task {id}")
        return (None, None)
    except Exception as e:
        logging.error(f"An unexpected error occurred in generate_c_code for generator {generator} and task {id}: {e}")
        return (None, None)