# BoBpiler-fuzzer
이 프로젝트는 Csmith와 yarpgen을 사용하여 랜덤 C 프로그램을 생성하고, 
다양한 컴파일러 (gcc, clang 등)와 최적화 레벨 (O0, O1, O2, O3)을 적용하여 컴파일한 후, 그 결과를 저장하고 비교하여 다른 결과를 구분하도록 만들었습니다.

***저장된 결과를 비교하는 로직을 더 발전시켜야 할 것 같습니다.***

사용법
1. Csmith 설치
chmod +x install.sh
./install.sh

2. 실행
python3 fuzzer.py


3. 특이사항
타임아웃: csmith가 계속 실행상태를 유지하는 코드를 생성하는 경우가 있어서, 각 컴파일 및 실행 단계에는 30초의 타임아웃을 설정해두었습니다. 


