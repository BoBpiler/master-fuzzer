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
def generate_c_code(id, generator_config):
    try:
        
        dir_path = os.path.join(f'{TEMP_DIRS[generator_config["name"]]}', f'{id}')
        random_seed = secrets.randbelow(4294967296)
    
        # 폴더가 없으면 생성
        if not os.path.exists(dir_path):    
            os.makedirs(dir_path)

        options_str = ' '.join(generator_config['options'])
        command_format = generator_config['output_format']

        # 파일 경로나 디렉토리 경로를 결정하는 로직
        if generator_config['path_type'] == 'filepath':
            path_key = 'filepath'
            path_value = generator_config['src_files'][0].format(path=dir_path, id=id)
        else:
            path_key = 'dir_path'
            path_value = dir_path

        command = command_format.format(
            generator=generator_config['name'],
            options=options_str,
            random_seed=random_seed,
            **{path_key: path_value}
        )

        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=generator_time_out)
        if result.returncode != 0:
            logging.warning(f"{generator_config['name']} code generation failed for {path_value} with return code {result.returncode}, error message: {result.stdout + result.stderr}")
            return (None, None)
        
        return (dir_path, random_seed)
    except subprocess.TimeoutExpired:
        logging.warning(f"Code generation timed out for generator {generator_config['name']} and task {id}")
        return (None, None)
    except Exception as e:
        logging.error(f"An unexpected error occurred in generate_c_code for generator {generator_config['name']} and task {id}: {e}")
        return (None, None)