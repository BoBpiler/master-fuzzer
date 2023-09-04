# Analyzer.py

from config import RANDOM_CODES_DIR, CATCH_DIR
import shutil

# compare_results 함수: 실행 결과를 비교 로직에 따라서 분석하는 함수
# argv: id - 소스코드 번호/ results - 바이너리 실행 결과들/ comparison_strategy - 비교 로직
def compare_results(id, results, comparison_strategy):
    # 해당 결과들을 대상으로 비교
    if comparison_strategy(results, id):
        print(f"Different results detected for source code ID: {id}")
        shutil.copy(f"{RANDOM_CODES_DIR}/random_program_{id}.c", f"{CATCH_DIR}/random_program_{id}.c")