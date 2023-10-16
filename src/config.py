# config.py 
# 컴파일러, 생성기, 옵션을 설정할 수 있습니다.
import os
import platform
from datetime import datetime

# 텔레그램 Chat ID 와 Token 값으로 직접 넣어주어야 합니다!
CHAT_ID = ""
HIGH_SEVERITY_CHAT_ID = ""
TOKEN = ""

# 수행 횟수 및 타임아웃 설정
total_tasks = 100 
generator_time_out = 10
compile_time_out = 30
binary_time_out = 10

# output 디렉토리 양식
BASE_DIR = f'output_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}'

# catch시 결과 txt, json 이름 양식
def get_result_file_names(id):
    return {
        "txt": f"{id}_result.txt",
        "json": f"{id}_result.json"
    }

# linux 생성기 설정
linux_generators_config = {
    'csmith': {
        'name': 'csmith',
        'binary_path': 'csmith',
        'language': 'c',
        'options': [
            "--max-array-dim 3", 
            "--max-array-len-per-dim 10",
            "--max-block-depth 3",
            "--max-block-size 5",
            "--max-expr-complexity 10",
            "--max-funcs 4",
            "--max-pointer-depth 3",
            "--max-struct-fields 10",
            "--max-union-fields 10",
            "--muls",
            "--safe-math",
            "--no-packed-struct",
            "--pointers",
            "--structs",
            "--unions",
            "--volatiles",
            "--volatile-pointers",
            "--const-pointers",
            "--global-variables",
            "--no-builtins",
            "--inline-function",
            "--inline-function-prob 50"
        ],
        'output_format': '{generator} {options} -o {filepath} --seed {random_seed}',
        'src_files': ['{path}/random_program_{id}.c'],
        'src_files_to_send': ['{path}/random_program_{id}.c'],
        'zip_required': False,
        'zip_name': None,
        'include_dir': '/usr/local/include/',
        'path_type': 'filepath'
    },
    'yarpgen': {
        'name': 'yarpgen',
        'binary_path': 'yarpgen',
        'language': 'c',
        'options': [
            "--std=c",
            "--mutate=all"
        ],
        'output_format': '{generator} {options} -o {dir_path} --seed={random_seed} --mutation-seed={random_seed}',
        'src_files': ['{path}/driver.c', '{path}/func.c'],
        'src_files_to_send': ['{path}/driver.c', '{path}/func.c', '{path}/init.h'],
        'zip_required': True,
        'zip_name': "yarpgen_{id}.zip",
        'include_dir': '{path}',
        'path_type': 'dirpath'
    },
    'yarpgen_scalar': {
        'name': 'yarpgen_scalar',
        'binary_path': 'yarpgen_scalar',
        'language': 'c',
        'options': [
            "--std=c99"
        ],
        'output_format': '{generator} {options} -d {dir_path} --seed={random_seed}',
        'src_files': ['{path}/driver.c', '{path}/func.c'],
        'src_files_to_send': ['{path}/driver.c', '{path}/func.c', '{path}/init.h'],
        'zip_required': True,
        'zip_name': "yarpgen_scalar_{id}.zip",
        'include_dir': '{path}',
        'path_type': 'dirpath'
    }
}

# 윈도우 생성기 설정
window_generators_config = {
    'csmith': {
        'name': 'csmith',
        'binary_path': "..\\csmith\\csmith.exe",
        'language': 'c',
        'options': [
            "--max-array-dim 3", 
            "--max-array-len-per-dim 10",
            "--max-block-depth 3",
            "--max-block-size 5",
            "--max-expr-complexity 10",
            "--max-funcs 4",
            "--max-pointer-depth 3",
            "--max-struct-fields 10",
            "--max-union-fields 10",
            "--muls",
            "--safe-math",
            "--no-packed-struct",
            "--pointers",
            "--structs",
            "--unions",
            "--volatiles",
            "--volatile-pointers",
            "--const-pointers",
            "--global-variables",
            "--no-builtins",
            "--inline-function",
            "--inline-function-prob 50"
        ],
        'output_format': '{generator} {options} -o {filepath} --seed {random_seed}',
        'src_files': ['{path}\\random_program_{id}.c'],
        'src_files_to_send': ['{path}\\random_program_{id}.c'],
        'zip_required': False,
        'zip_name': None,
        'include_dir': '..\\runtime',
        'path_type': 'filepath'
    },
    'yarpgen': {
        'name': 'yarpgen',
        'binary_path': "..\\yarpgen\\yarpgen.exe",
        'language': 'cpp',
        'options': [
            "--emit-pragmas=none",
            "--std=c++",
            "--mutate=all"
        ],
        'output_format': '{generator} {options} -o {dir_path} --seed={random_seed} --mutation-seed={random_seed}',
        'src_files': ['{path}\\driver.cpp', '{path}\\func.cpp'],
        'src_files_to_send': ['{path}\\driver.cpp', '{path}\\func.cpp', '{path}\\init.h'],
        'zip_required': True,
        'zip_name': "yarpgen_{id}.zip",
        'include_dir': '{path}',
        'path_type': 'dirpath'
    },
    'yarpgen_scalar': {
        'name': 'yarpgen_scalar',
        'binary_path': "..\\yarpgen\\yarpgen_scalar.exe",
        'language': 'cpp',
        'options': [
            "--std=c++17"
        ],
        'output_format': '{generator} {options} -d {dir_path} --seed={random_seed}',
        'src_files': ['{path}\\driver.cpp', '{path}\\func.cpp'],
        'src_files_to_send': ['{path}\\driver.cpp', '{path}\\func.cpp', '{path}\\init.h'],
        'zip_required': True,
        'zip_name': "yarpgen_scalar_{id}.zip",
        'include_dir': '{path}',
        'path_type': 'dirpath'
    }
}

# cl 컴파일러 obj 구분을 위한 폴더
def cl_prepare(dir_path, optimization_level):
    obj_folder = os.path.join(dir_path, f"obj_{optimization_level[1:]}")
    if not os.path.exists(obj_folder):
        os.makedirs(obj_folder)
    return obj_folder

# 윈도우 컴파일러 설정
window_compilers = {
    "cl": {
        "name": "CL",
        "file_name": "cl",
        "options": ["/O1", "/O2", "/Od", "/Ox", "/Ot"],
        "prepare_command": cl_prepare,
        "output_format": "\"{compiler_path}\" {optimization} /I {include_dir} {src_files} /Fo:{obj_path}\\ /Fe:\"{exe_path}.exe\"",
        "language": {
            "c": {
                "binary_path": "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Tools\\MSVC\\14.37.32822\\bin\\Hostx64\\x64\\cl.exe",
                "execute": "{exe_path}.exe"  
            },
            "cpp": {
                "binary_path": "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Tools\\MSVC\\14.37.32822\\bin\\Hostx64\\x64\\cl.exe",
                "execute": "{exe_path}.exe"  
            }
        }
    },
    "mingw": {
        "name": "MinGW",
        "file_name": "mingw",
        "options": ["-O0", "-O1", "-O2", "-O3"],
        "output_format": "\"{compiler_path}\" {optimization} -I {include_dir} {src_files} -o \"{exe_path}.exe\"",
        "language": {
            "c": {
                "binary_path": "C:\\Program Files\\mingw64\\bin\\gcc.exe",
                "execute": "{exe_path}.exe"  
            },
            "cpp": {
                "binary_path": "C:\\Program Files\\mingw64\\bin\\g++.exe",
                "execute": "{exe_path}.exe"  
            }
        }
    },
    "llvm-mingw": {
        "name": "LLVM-MinGW",
        "file_name": "llvm-mingw",
        "options": ["-O0", "-O1", "-O2", "-O3"],
        "output_format": "\"{compiler_path}\" {optimization} -I {include_dir} {src_files} -o \"{exe_path}.exe\"",
        "language": {
            "c": {
                "binary_path": "C:\\Program Files\\llvm-mingw-64\\bin\\clang.exe",
                "execute": "{exe_path}.exe"    
            },
            "cpp": {
                "binary_path": "C:\\Program Files\\llvm-mingw-64\\bin\\clang++.exe",
                "execute": "{exe_path}.exe"  
            }
        }
    }
}

# 리눅스 컴파일러 설정
linux_compilers = {
    "gcc": {
        "name": "gcc-trunk",
        "file_name": "gcc",
        "options": ["-O0", "-O1", "-O2", "-O3"],
        "output_format": "{compiler_path} {src_files} -o {exe_path} {optimization} -I {include_dir}",
        "language": {
            "c": {
                "binary_path": "./gcc-trunk",
                "execute": "{exe_path}"  
            },
            "cpp": {
                "binary_path": "./g++-trunk",
                "execute": "{exe_path}"  
            }
        }
    },
    "clang": {
        "name": "clang-18",
        "file_name": "clang",
        "options": ["-O0", "-O1", "-O2", "-O3"],
        "output_format": "{compiler_path} {src_files} -o {exe_path} {optimization} -I {include_dir}",
        "language": {
            "c": {
                "binary_path": "./clang-18",
                "execute": "{exe_path}"  
            },
            "cpp": {
                "binary_path": "./clang++-18",
                "execute": "{exe_path}"  
            }
        }
    },
    "gcc-aarch64": {
        "name": "aarch64-linux-gnu-gcc",
        "file_name": "gcc-aarch64",
        "options": ["-O0", "-O1", "-O2", "-O3"],
        "output_format": "{compiler_path} {src_files} -o {exe_path} {optimization} -I {include_dir}",
        "language": {
            "c": {
                "binary_path": "aarch64-linux-gnu-gcc",
                "execute": "qemu-aarch64-static -L /usr/aarch64-linux-gnu {exe_path}"
            },
            "cpp": {
                "binary_path": "aarch64-linux-gnu-g++",
                "execute": "qemu-aarch64-static -L /usr/aarch64-linux-gnu {exe_path}"
            }
        }
    },
    "clang-aarch64": {
        "name": "clang-18 --target=aarch64-linux-gnu",
        "file_name": "clang-aarch64",
        "options": ["-O0", "-O1", "-O2", "-O3"],
        "output_format": "{compiler_path} {src_files} -o {exe_path} {optimization} -I {include_dir}",
        "language": {
            "c": {
                "binary_path": "./clang-18 --target=aarch64-linux-gnu",
                "execute": "qemu-aarch64-static -L /usr/aarch64-linux-gnu {exe_path}"
            },
            "cpp": {
                "binary_path": "./clang++-18 --target=aarch64-linux-gnu",
                "execute": "qemu-aarch64-static -L /usr/aarch64-linux-gnu {exe_path}"
            }
        }
    },
    "gcc-mips64el": {
        "name": "mips64el-linux-gnuabi64-gcc",
        "file_name": "gcc-mips64el",
        "options": ["-O0", "-O1", "-O2", "-O3"],
        "output_format": "{compiler_path} {src_files} -o {exe_path} {optimization} -I {include_dir}",
        "language": {
            "c": {
                "binary_path": "mips64el-linux-gnuabi64-gcc",
                "execute": "qemu-mips64el-static -L /usr/mips64el-linux-gnuabi64 {exe_path}"
            },
            "cpp": {
                "binary_path": "mips64el-linux-gnuabi64-g++",
                "execute": "qemu-mips64el-static -L /usr/mips64el-linux-gnuabi64 {exe_path}"
            }
        }
    },
    "clang-mips64el": {
        "name": "clang-18 --target=mips64el-linux-gnuabi64",
        "file_name": "clang-mips64el",
        "options": ["-O0", "-O1", "-O2", "-O3"],
        "output_format": "{compiler_path} {src_files} -o {exe_path} {optimization} -I {include_dir}",
        "language": {
            "c": {
                "binary_path": "./clang-18 --target=mips64el-linux-gnuabi64",
                "execute": "qemu-mips64el-static -L /usr/mips64el-linux-gnuabi64 {exe_path}"
            },
            "cpp": {
                "binary_path": "./clang++-18 --target=mips64el-linux-gnuabi64",
                "execute": "qemu-mips64el-static -L /usr/mips64el-linux-gnuabi64 {exe_path}"
            }
        }
    },
    "gcc-riscv64": {
        "name": "riscv64-unknown-elf-gcc",
        "file_name": "gcc-riscv64",
        "options": ["-O0", "-O1", "-O2", "-O3"],
        "output_format": "{compiler_path} {src_files} -o {exe_path} {optimization} -I {include_dir}",
        "language": {
            "c": {
                "binary_path": "./riscv64-unknown-elf-gcc",
                "execute": "qemu-riscv64-static {exe_path}"
            },
            "cpp": {
                "binary_path": "./riscv64-unknown-elf-g++",
                "execute": "qemu-riscv64-static {exe_path}"
            }
        }
    },
    "clang-riscv64": {
        "name": "clang-18 --target=riscv64-unknown-elf",
        "file_name": "clang-riscv64",
        "options": ["-O0", "-O1", "-O2", "-O3"],
        "output_format": "{compiler_path} {src_files} -o {exe_path} {optimization} -I {include_dir}",
        "language": {
            "c": {
                "binary_path": "./clang-18 --sysroot=$HOME/riscv/riscv64-unknown-elf --gcc-toolchain=$HOME/riscv --target=riscv64-unknown-elf -march=rv64gc",
                "execute": "qemu-riscv64-static {exe_path}"
            },
            "cpp": {
                "binary_path": "./clang++-18 --sysroot=$HOME/riscv/riscv64-unknown-elf --gcc-toolchain=$HOME/riscv --target=riscv64-unknown-elf -march=rv64gc",
                "execute": "qemu-riscv64-static {exe_path}"
            }
        }
    }
}

# platform에 따라서 생성기 및 컴파일러 설정 결정
if platform.system() == 'Linux':
    generators_config = linux_generators_config
    compilers = linux_compilers
elif platform.system() == 'Windows':
    generators_config = window_generators_config
    compilers = window_compilers
else:
    generators_config = linux_generators_config
    compilers = linux_compilers

# 결정된 생성기에 따라서 output 디렉토리의 트리 구조 결정
GENERATOR_DIRS = {key: os.path.join(BASE_DIR, config['name']) for key, config in generators_config.items()}
CATCH_DIRS = {key: os.path.join(GENERATOR_DIRS[key], 'catch') for key in generators_config.keys()}
TEMP_DIRS = {key: os.path.join(GENERATOR_DIRS[key], 'temp') for key in generators_config.keys()}