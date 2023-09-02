import os
import subprocess

def compile_and_run(filename, id, compiler, optimization_level):
    output_filename = f"results/{compiler}/{id}_{compiler}_O{optimization_level}.txt"
    binary_name = f"temp/{compiler}/{id}_{compiler}_O{optimization_level}"

    csmith_include = f"{os.path.expanduser('~')}/csmith/include"
    subprocess.run([compiler, filename, '-o', binary_name, f'-O{optimization_level}', f'-I{csmith_include}'], timeout=60)

    try:
        result = subprocess.run([f'./{binary_name}'], capture_output=True, text=True, timeout=60).stdout
    except subprocess.TimeoutExpired:
        print(f"TimeoutExpired occurred in {binary_name}")
        result = "Timeout"  # 이 값을 어떻게 할까

    with open(output_filename, 'w') as f:
        f.write(result)

    return result

