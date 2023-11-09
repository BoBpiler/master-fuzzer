# fuzzer.py
# main 입니다.

from utils import*
from fuzzer_display import*
from CodeGenerator import generate_c_code
from Analyzer import analyze_results
from running_system import*
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Process
import uuid
import argparse
from itertools import repeat

import signal
import atexit

def signal_handler(sig, frame):
    print("Terminating all processes...")
    terminate_process_and_children(os.getpid())
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def cleanup():
    terminate_process_and_children(os.getpid())

atexit.register(cleanup)


# process_generator 함수: 생성기 별로 퍼징을 수행하는 함수
# argv: generator - 생성기 종류 (현재 csmith와 yarpgen)
# return: None 
def fuzz_with_generator(compilers, generator_config, temp_dirs, catch_dirs, status_info, status_lock, logger, partial_timeout=True):
    generator_name = generator_config["name"]
    with status_lock:
    # generator 별로 상태 정보 저장
        temp_status = dict(status_info)
        if generator_name not in temp_status:
            temp_status[generator_name] = {
                "current_status": INIT,
                "completed_tasks": 0,
                "skipped_tasks": 0,
                "round_number": 0,
                "High": 0,
                "Medium": 0,
                "Low": 0,
                "different_checksums": 0,
                "compile_crashes": 0,
                "binary_crashes": 0,
                "partial_timeouts": 0,
                "abnormal_compiles": 0,
                "abnormal_binaries": 0,
                "duplicated_counts": 0
            }
            status_info.update(temp_status)
    machine_info = get_machine_info(logger)
    round_number = 0  # 라운드 번호 초기화
    
    while True:
            
        # print(f"\n{'#'*100}")
        # print(f"[*] Fuzzing round: {round_number} for generator: {generator_name}")
        # print(f"{'#'*100}\n")
        
        completed_tasks = 0
        skipped_tasks = 0
        
        try:
            for index in range(0, total_tasks):
                with status_lock:
                    temp_status = dict(status_info)
                    temp_status[generator_name]["round_number"] += 1
                    temp_status[generator_name]["current_status"] = CODE_GENERATION
                    temp_status["total"]["round_number"] += 1
                    status_info.update(temp_status)

                # 소스코드 생성
                # print(f"****************************************generated by {generator_name}: {index} task started*********************************************")
                id = uuid.uuid1()    # 고유한 ID 셍성 - 어떤 컴퓨터에서 생성하든 생성된 코드를 구분하기 위함 
                dir_path, random_seed = generate_c_code(id, generator_config, temp_dirs, logger)
                # 코드 생성이 되지 않은 경우 예외 처리 
                if dir_path is None:
                    logger.warning(f"Code generation failed for task {index} using {generator_name}, skipping.")
                    skipped_tasks += 1
                    with status_lock:
                        temp_status = dict(status_info)
                        temp_status[generator_name]["skipped_tasks"] += 1
                        temp_status["total"]["skipped_tasks"] += 1
                        status_info.update(temp_status)
                    continue
                else:
                    with status_lock:
                        temp_status = dict(status_info)
                        temp_status[generator_name]["current_status"] = COMPILING_AND_RUNNING
                        status_info.update(temp_status)
                
                with ProcessPoolExecutor() as executor:
                    futures = []
                    results = {}
                    # 컴파일 및 실행 (gcc, clang으로 -O0 ~ -O3 옵션 주어서 컴파일 하고 실행 결과 저장)
                    for compiler_info in compilers.values():
                        for opt_level in compiler_info['options']:
                            if 'runners' not in compiler_info['language'][generator_config['language']]: # 일반 컴파일러의 경우
                                futures.append(executor.submit(compile_and_run, dir_path, temp_dirs, generator_config, id, compiler_info, opt_level, logger, random_seed))
                            else:
                                binary_name = os.path.join(temp_dirs, f'{id}', f"{compiler_info['file_name']}_{opt_level[1:]}")
                                compile_result = compile(binary_name, dir_path, generator_config, id, compiler_info, opt_level, logger)
                                if compile_result['status']: # 컴파일이 성공한 경우에만 실행
                                    for runner_name, runner_command in compiler_info['language'][generator_config['language']]['runners'].items():
                                        futures.append(executor.submit(run_binary_for_wasm, runner_name, runner_command, compile_result, binary_name, generator_config, id, compiler_info, opt_level, logger, random_seed))
                                else:
                                    child_ground_truth = compiler_info.get('child_ground_truth', None)
                                    is_child_ground_truth = (opt_level == child_ground_truth)  # 참 거짓 비교
                                    result_dict = {
                                        'id': str(id),
                                        'random_Seed': str(random_seed),
                                        'compiler': compiler_info['name'],
                                        'child_ground_truth': is_child_ground_truth,
                                        'optimization_level': opt_level,
                                        'generator': generator_name,
                                        'compile': {
                                            'status': None,
                                            'return_code': None,
                                            'error_type': None,
                                            'error_message': None
                                        },
                                        'run': {
                                            'status': None,
                                            'return_code': None,
                                            'error_type': None,
                                            'error_message': None,
                                            'result': None
                                        }
                                    }
                                    result_dict['compile'] = compile_result
                                    futures.append((binary_name, result_dict))  # 컴파일 실패 결과를 futures에 추가

                    for future in futures:
                        if isinstance(future, tuple):
                            key, result_dict = future
                        else:
                            result = future.result()
                            if result is not None:
                                key, result_dict = result
                        if key == "error": # 에러 처리
                            continue
                        results[key] = result_dict
                
                with status_lock:
                    temp_status = dict(status_info)
                    temp_status[generator_name]["current_status"] = ANALYZING
                    status_info.update(temp_status)
                if len(results) > 0:  # results 딕셔너리가 비어 있지 않다면
                    analyze_results(compilers, dir_path, temp_dirs, catch_dirs, generator_config, id, random_seed, results, machine_info, status_info, status_lock, logger, partial_timeout)
                else:
                    # results 딕셔너리가 비어 있는 경우, 문제가 발생한 것으로 판단
                    skipped_tasks += 1
                    with status_lock:
                        temp_status = dict(status_info)
                        temp_status[generator_name]["skipped_tasks"] += 1
                        temp_status["total"]["skipped_tasks"] += 1
                        status_info.update(temp_status)
                    logger.critical(f"CRITICAL ERROR: This is an exceptional case which means impossible and requires immediate attention.")
                
                # Temp 폴더 청소
                cleanup_temp(temp_dirs, logger)
                # 진행률 업데이트 및 출력
                completed_tasks += 1
                progress = (completed_tasks / total_tasks) * 100
                with status_lock:
                    temp_status = dict(status_info)
                    temp_status[generator_name]["completed_tasks"] += 1
                    temp_status["total"]["completed_tasks"] += 1
                    status_info.update(temp_status)
                # print(f"Progress for {generator_name}: {progress:.2f}% completed. skipped count: {skipped_tasks}")
                # print(f"****************************************generated by {generator_name}: {index} task finished*********************************************")
            round_number += 1  # 라운드 번호 증가 
            cleanup_wasmer_cache(logger) # wasmer cache 지우기  
        except Exception as e:
            logger.error(f"An unexpected error occurred in process_generator for generator {generator_name} and task {index}: {e}")


# main 함수: 퍼징을 수행하는 총괄 코드
def main():
    try:
        parser = argparse.ArgumentParser(description="This is BoBpiler fuzzer")
        parser.add_argument("--no-timeout", action="store_false", dest="partial_timeout", help='Choose partial_timeout option')
        parser.add_argument('--endian', type=str, choices=['big', 'little'], default='little', help='Choose endian type')
        args = parser.parse_args()

        # 생성기와 컴파일러 선택
        all_generators_config = get_generators_by_platform()
        selected_generator_keys = input_generators(all_generators_config)
        selected_generators = {key: all_generators_config[key] for key in selected_generator_keys}
        generators = list(selected_generators.values())

        all_compilers = get_compilers_by_platform(args)
        selected_compiler_names = input_compilers(all_compilers)
        selected_compilers = {name: all_compilers[name] for name in selected_compiler_names}
        compilers = selected_compilers

        # 디렉토리 구조 설정
        generator_dirs, catch_dirs, temp_dirs = setup_output_dirs(selected_generators, BASE_DIR) # 생성기 디렉토리 설정
        
        temp_dirs_list = list(temp_dirs.values()) # 생성기 별 temp 디렉토리 경로
        catch_dirs_list = list(catch_dirs.values()) # 생성기 별 catch 디렉토리 경로
        
        # 1. display_status 함수를 별도의 프로세스로 시작
        start_time = datetime.now()
        status_info, status_lock = initialize_manager()
        # ARM64 아키텍처가 아니라면 display_process를 시작합니다.
        is_windows = platform.system() == 'Windows'
        is_arm64 = platform.machine().lower() == 'arm64'
        if not (is_arm64 and is_windows):
            display_process = Process(target=curses.wrapper, args=(display_status, status_info, status_lock, generators, start_time))
            display_process.start()
        else:
            # ARM64 아키텍처의 경우 display_process를 시작하지 않습니다.
            print("Windows ARM64 architecture detected. Skipping 'curses' based UI.")
        
        # logging 정보 모든 프로세스 통합
        logger, listener = setup_logging()
        processes = []

        for generator, temp_dir, catch_dir in zip(generators, temp_dirs_list, catch_dirs_list):
            p = Process(target=fuzz_with_generator, args=(compilers, generator, temp_dir, catch_dir, status_info, status_lock, logger, args.partial_timeout))
            processes.append(p)
            p.start()


        for p in processes:
            p.join()

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Terminating all processes...")
        listener.stop()
        if not (is_arm64 and is_windows) and 'display_process' in locals():
            display_process.terminate()  # 화면 출력 프로세스 종료
        terminate_process_and_children(os.getpid())

if __name__ == "__main__":
    main()


