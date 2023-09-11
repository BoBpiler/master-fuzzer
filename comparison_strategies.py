# comparison_strategies.py
# 현재 사용하지 않습니다.
# 비교 로직을 잘 구성해야 할 것 같습니다. 
# 일단, 하나의 소스코드에 대해서 만들어진 모든 바이너리를 대상으로 결과가 하나라도 다른지 확인하도록 했습니다.
# 비교 로직 함수를 추가해나가면 좋을 것 같습니다.



# basic_comparison 함수: 결과를 비교하는 기본 전략
# argv: results - 바이너리 실행 결과들/ id는 혹시 몰라서...
# return: true - 다른 결과가 존재 즉, 해당 소스코드는 유의미한 소스코드 / false - 모든 결과가 동일
def basic_comparison(results, id):
    first_key = list(results.keys())[0]
    first_result = results[first_key]

    for key, result in results.items():
        # 하나라도 다른 결과가 있다면 True 반환
        if first_result != result:
            return True
    # 모든 결과가 같다면 False 반환     
    return False 


