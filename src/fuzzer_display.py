from multiprocessing import Manager, Lock
import curses
from datetime import datetime
import psutil

# 전역적으로 단계를 정의하는 문자열 상수
INIT = "Initializing"
CODE_GENERATION = "Generating code"
COMPILING_AND_RUNNING = "Compiling and running"
ANALYZING = "Analyzing"

# 상태 정보를 위한 데이터 구조 생성
def initialize_manager():
    manager = Manager()
    status_info = manager.dict({
        "total": {
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
        # 추가적으로 각 제네레이터에 대한 정보도 저장 가능  - 생성기 별로 정보를 저장할 예정
        # 예: status_info['generator1'] = {"completed_tasks": 0, ...}
    })
    status_lock = Lock()
    return status_info, status_lock


# line 하나 지워주는 함수
def clear_line(stdscr, y, x_start, x_end):
    stdscr.addstr(y, x_start, " " * (x_end - x_start))


# box 그려주는 함수
def draw_box(stdscr, y_start, y_end, x_start, x_end, title=None):
    
    # 상하좌우의 라인 그리기
    stdscr.vline(y_start + 1, x_start, curses.ACS_VLINE, y_end - y_start - 1)
    stdscr.vline(y_start + 1, x_end, curses.ACS_VLINE, y_end - y_start - 1)
    stdscr.hline(y_start, x_start + 1, curses.ACS_HLINE, x_end - x_start - 1)
    stdscr.hline(y_end, x_start + 1, curses.ACS_HLINE, x_end - x_start - 1)
    
    # 꼭짓점 문자 그리기
    stdscr.addch(y_start, x_start, curses.ACS_ULCORNER)
    stdscr.addch(y_start, x_end, curses.ACS_URCORNER)
    stdscr.addch(y_end, x_start, curses.ACS_LLCORNER)
    stdscr.addch(y_end, x_end, curses.ACS_LRCORNER)

    # 제목이 있으면 박스 상단에 추가
    if title:
        stdscr.attron(curses.color_pair(3)) # cyan
        stdscr.addstr(y_start, x_start + 2, title)
        stdscr.attroff(curses.color_pair(3))


def draw_main_box(stdscr, title):
    height, width = stdscr.getmaxyx()
    
    # 전체 박스의 크기 계산
    box_width = width - 4
    # 박스의 높이는 전체 화면 높이의 3/4로 설정하되 최소 20 이상은 되도록 설정 (임의의 값)
    box_height = max(int(height * 1/2), 20)

    x_start = 2
    # y_start를 계산하여 박스가 화면의 중앙에 위치하도록 함
    y_start = (height - box_height) // 2

    x_end = x_start + box_width
    y_end = y_start + box_height

    # 전체 박스 그리기
    draw_box(stdscr, y_start, y_end, x_start, x_end)

    # title의 x 좌표 계산
    title_x = x_start + (box_width - len(title)) // 2

    stdscr.attron(curses.color_pair(2)) # 초록색
    stdscr.addstr(y_start, title_x, title) # 중앙
    stdscr.attroff(curses.color_pair(2))

    return y_start, y_end, x_start, x_end


# 시작 시간으로부터 지난 시간 계산
def get_elapsed_time(start_time):
    elapsed = datetime.now() - start_time
    days, remainder = divmod(elapsed.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return int(days), int(hours), int(minutes), int(seconds)

# 실행 시간 측정해서 화면에 보여주는 함수
def draw_process_timing(stdscr, y, x, width, start_time, temp_status):
    draw_box(stdscr, y, y + 2, x, width // 2 - 1, "Process Timing")
    days, hours, minutes, seconds = get_elapsed_time(start_time)
    
    # 해당 줄을 지움
    clear_line(stdscr, y + 1, x + 2, width // 2 - 1)
    
    # "run time :"와 "Total Round :"를 회색으로 출력
    stdscr.attron(curses.color_pair(6))
    stdscr.addstr(y + 1, x + 2, "run time : ")
    offset = len("run time : ")
    stdscr.attroff(curses.color_pair(6))

    # time_str (시간)을 하얀색으로 출력
    time_str = f"{days} days, {hours} hrs, {minutes} min, {seconds} sec"
    stdscr.addstr(y + 1, x + 2 + offset, time_str)
    offset += len(time_str)
    
    stdscr.attron(curses.color_pair(6))
    spacing = 4
    stdscr.addstr(y + 1, x + 2 + offset, " " * spacing + "Total Round : ")
    offset += len(" " * spacing + "Total Round : ")
    stdscr.attroff(curses.color_pair(6))
    
    # Round 숫자 값을 하얀색으로 출력
    total_round = temp_status["total"]["round_number"]
    stdscr.addstr(y + 1, x + 2 + offset, str(total_round))


# 전체 결과를 출력하는 함수
def draw_overall_results(stdscr, y, x, width, temp_status):
    draw_box(stdscr, y, y + 8, x, width - 2, "Overall Results")

    stdscr.attron(curses.color_pair(1)) # 빨간색
    stdscr.addstr(y + 1, x + 2, f"High : {temp_status['total']['High']}")
    stdscr.attroff(curses.color_pair(1))

    stdscr.attron(curses.color_pair(4)) # 노란색
    stdscr.addstr(y + 2, x + 2, f"Medium : {temp_status['total']['Medium']}")
    stdscr.attroff(curses.color_pair(4))
    
    stdscr.attron(curses.color_pair(6)) # 회색
    stdscr.addstr(y + 3, x + 2, f"Low : {temp_status['total']['Low']}")
    stdscr.attroff(curses.color_pair(6))

    detected_counts = temp_status['total']['High'] +  temp_status['total']['Medium'] + temp_status['total']['Low']
    if temp_status['total']['round_number'] != 0:
        progress = (detected_counts / temp_status['total']['round_number']) * 100
    else:
        progress = 0

    # 탐지율 색상 설정
    if progress >= 50:
        progress_color = 3  # 파란색
    else:
        progress_color = 0  # 흰색

    stdscr.attron(curses.color_pair(6))  # 회색
    stdscr.addstr(y + 4, x + 2, "Detection rate : ")
    stdscr.attroff(curses.color_pair(6))
    stdscr.attron(curses.color_pair(progress_color))
    stdscr.addstr(y + 4, x + 2 + len("Detection rate : "), f"{progress:.2f}%")
    stdscr.attroff(curses.color_pair(progress_color))

    stdscr.attron(curses.color_pair(6))  # 회색
    stdscr.addstr(y + 5, x + 2, "Duplication count : ")
    stdscr.attroff(curses.color_pair(6))
    stdscr.addstr(y + 5, x + 2 + len("Duplication count : "), f"{temp_status['total']['duplicated_counts']}")

    # 메모리 사용량
    memory_info = psutil.virtual_memory()
    used_memory = memory_info.used / (1024**3)  # GB 단위로 변환
    total_memory = memory_info.total / (1024**3)  # GB 단위로 변환
    memory_percentage = (used_memory / total_memory) * 100

    # 메모리 사용량 색상 설정
    if memory_percentage < 70:
        memory_color = 2  # 초록색
    else:
        memory_color = 1  # 빨간색

    clear_line(stdscr, y + 6, x + 2, width - 3)
    stdscr.attron(curses.color_pair(6))  # 회색
    stdscr.addstr(y + 6, x + 2, "Used Memory: ")
    stdscr.attroff(curses.color_pair(6))
    stdscr.attron(curses.color_pair(memory_color))
    stdscr.addstr(y + 6, x + 2 + len("Used Memory: "), f"{used_memory:.2f} GB / {total_memory:.2f} GB")
    stdscr.attroff(curses.color_pair(memory_color))

    # CPU 사용량
    cpu_usage = psutil.cpu_percent(interval=1)  # 1초 동안의 CPU 사용량을 %
    
    # CPU 사용량 색상 설정
    if cpu_usage < 70:
        cpu_color = 2  # 초록색
    else:
        cpu_color = 1  # 빨간색

    clear_line(stdscr, y + 7, x + 2, width - 3)
    stdscr.attron(curses.color_pair(6))  # 회색
    stdscr.addstr(y + 7, x + 2, "CPU Usage: ")
    stdscr.attroff(curses.color_pair(6))
    stdscr.attron(curses.color_pair(cpu_color))
    stdscr.addstr(y + 7, x + 2 + len("CPU Usage: "), f"{cpu_usage}%")
    stdscr.attroff(curses.color_pair(cpu_color))


# catch 종류에 대해서 count 수 출력하는 함수
def draw_catch(stdscr, y, x, width, temp_status):
    draw_box(stdscr, y, y + 4, x, width // 2 - 1, "Catch")

    # 첫 번째 줄
    clear_line(stdscr, y + 1, x + 2, width // 2 - 1)
    
    stdscr.attron(curses.color_pair(6))  # 회색
    stdscr.addstr(y + 1, x + 2, "Different Checksums : ")
    offset = len("Different Checksums : ")
    stdscr.attroff(curses.color_pair(6))

    stdscr.addstr(y + 1, x + 2 + offset, f"{temp_status['total']['different_checksums']}")
    offset += len(f"{temp_status['total']['different_checksums']}")
    
    spacing = 4
    stdscr.attron(curses.color_pair(6))  # 회색
    stdscr.addstr(y + 1, x + 2 + offset, " " * spacing + "Partial Timeout : ")
    offset += len(" " * spacing + "Partial Timeout : ")
    stdscr.attroff(curses.color_pair(6))

    stdscr.addstr(y + 1, x + 2 + offset, f"{temp_status['total']['partial_timeouts']}")

    # 두 번째 줄
    clear_line(stdscr, y + 2, x + 2, width // 2 - 1)
    
    stdscr.attron(curses.color_pair(6))  # 회색
    stdscr.addstr(y + 2, x + 2, "Complete Crash : ")
    offset = len("Complete Crash : ")
    stdscr.attroff(curses.color_pair(6))

    stdscr.addstr(y + 2, x + 2 + offset, f"{temp_status['total']['compile_crashes']}")
    offset += len(f"{temp_status['total']['compile_crashes']}")

    stdscr.attron(curses.color_pair(6))  # 회색
    spacing = 9
    stdscr.addstr(y + 2, x + 2 + offset, " " * spacing + "Binary Crash : ")
    offset += len(" " * spacing + "Binary Crash : ")
    stdscr.attroff(curses.color_pair(6))

    stdscr.addstr(y + 2, x + 2 + offset, f"{temp_status['total']['binary_crashes']}")

    # 세 번째 줄
    clear_line(stdscr, y + 3, x + 2, width // 2 - 1)

    stdscr.attron(curses.color_pair(6))  # 회색
    stdscr.addstr(y + 3, x + 2, "Abnormal Compiles : ")
    offset = len("Abnormal Compiles : ")
    stdscr.attroff(curses.color_pair(6))

    stdscr.addstr(y + 3, x + 2 + offset, f"{temp_status['total']['abnormal_compiles']}")
    offset += len(f"{temp_status['total']['abnormal_compiles']}")

    stdscr.attron(curses.color_pair(6))  # 회색
    spacing = 6
    stdscr.addstr(y + 3, x + 2 + offset, " " * spacing + "Abnormal Binaries : ")
    offset += len(" " * spacing + "Abnormal Binaries : ")
    stdscr.attroff(curses.color_pair(6))

    stdscr.addstr(y + 3, x + 2 + offset, f"{temp_status['total']['abnormal_binaries']}")


# generator 별로 status 출력하는 함수
def draw_generator_info(stdscr, y, x, gen_count, gen_width, height, generators, temp_status):
    for i in range(gen_count):
        x_start = x + i * gen_width
        x_end = x_start + gen_width - 1
        gen_title = generators[i]['name']
        if gen_title in temp_status:
            draw_box(stdscr, y, y + 5, x_start, x_end, f"{gen_title}")

            stdscr.attron(curses.color_pair(6))  # 회색
            stdscr.addstr(y + 1, x_start + 2, "Round : ")
            stdscr.attroff(curses.color_pair(6))
            stdscr.addstr(y + 1, x_start + 2 + len("Round : "), f"{temp_status[generators[i]['name']]['round_number']}")

            stdscr.attron(curses.color_pair(6))  # 회색
            stdscr.addstr(y + 2, x_start + 2, "Completed Tasks : ")
            stdscr.attroff(curses.color_pair(6))
            stdscr.addstr(y + 2, x_start + 2 + len("Completed Tasks : "), f"{temp_status[generators[i]['name']]['completed_tasks']}")

            stdscr.attron(curses.color_pair(6))  # 회색
            stdscr.addstr(y + 3, x_start + 2, "Skipped Tasks : ")
            stdscr.attroff(curses.color_pair(6))
            stdscr.addstr(y + 3, x_start + 2 + len("Skipped Tasks : "), f"{temp_status[generators[i]['name']]['skipped_tasks']}")
            
            clear_line(stdscr, y + 4, x_start + 2, x_end - 1)
            stdscr.attron(curses.color_pair(6))  # 회색
            stdscr.addstr(y + 4, x_start + 2, "Current Status : ")
            stdscr.attroff(curses.color_pair(6))
            stdscr.addstr(y + 4, x_start + 2 + len("Current Status : "), f"{temp_status[generators[i]['name']]['current_status']}")




# fuzzer display 함수
def display_status(stdscr, status_info, status_lock, generators, start_time):
    try:
        MIN_HEIGHT, MIN_WIDTH = 20, 80  # 적절한 최소 크기를 지정
        curses.curs_set(0)  # 커서를 숨깁니다.
        stdscr.nodelay(1)  # non-blocking mode로 설정
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)  # 투명한 배경에 빨간색 텍스트
        curses.init_pair(2, curses.COLOR_GREEN, -1)  # 투명한 배경에 초록색 텍스트
        curses.init_pair(3, curses.COLOR_CYAN, -1)  # 투명한 배경에 파랑색 텍스트
        curses.init_pair(4, curses.COLOR_YELLOW, -1)  # 투명한 배경에 노랑색 텍스트
        curses.init_pair(5, curses.COLOR_BLACK, -1)  # 투명한 배경에 검정색 텍스트
        if curses.can_change_color() and curses.COLORS >= 256:
            # 회색 정의 (R, G, B 값은 0에서 1000 사이)
            curses.init_color(8, 500, 500, 500)
            curses.init_pair(6, 8, -1)  # 회색 텍스트

        gen_count = len(generators)
        if gen_count > 3:
            gen_count = 3 # 표현 가능한 생성기 정보 max는 3개 
            
        while True:
            # status 정보 복사 
            height, width = stdscr.getmaxyx()
            # 화면 크기가 지정된 최소 크기보다 작으면 점을 표시하고 다음 반복으로
            if height < MIN_HEIGHT or width < MIN_WIDTH:
                stdscr.clear()
                stdscr.attron(curses.color_pair(2))
                message = "BoBpiler Fuzzing in Progress..."
                y_center, x_center = height // 2, width // 2
                stdscr.addstr(y_center, x_center - len(message) // 2, message)
                stdscr.attroff(curses.color_pair(2))
                stdscr.refresh()
                curses.napms(1000)
                continue
            gen_width = (width - 6) // gen_count

            with status_lock:
                temp_status = dict(status_info)

            # main 박스 그리기
            y_start, y_end, x_start, x_end = draw_main_box(stdscr, "BoBpiler Fuzzer Status")
            internal_width = x_end - x_start
            total_box_height = 13  # 내부 박스들의 총 높이
            margin = (y_end - y_start - total_box_height) // 2  # 상단 및 하단 여백
            # Process Timing 정보 출력
            draw_process_timing(stdscr, y_start + margin, x_start + 1, internal_width, start_time, temp_status)

            # Overall Results 출력 (Process Timing 옆에 위치)
            draw_overall_results(stdscr, y_start + margin, x_start + 1 + internal_width//2, internal_width, temp_status)

            # Catch 출력
            draw_catch(stdscr, y_start + margin + 4, x_start + 1, internal_width, temp_status)

            # Generator 별 정보 출력
            draw_generator_info(stdscr, y_start + margin + 9, x_start + 1, gen_count, gen_width, height - 6, generators, temp_status)


            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_RESIZE:
                stdscr.clear()  # 화면을 클리어합니다.
                continue  # 화면 크기가 변경되면 다음 반복으로 넘어가서 다시 그립니다.            
            curses.napms(1000)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        curses.endwin()
        print(f"display An error occurred: {e}")



