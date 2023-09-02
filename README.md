# BoBpiler-fuzzer
이 프로젝트는 Csmith를 사용하여 랜덤 C 프로그램을 생성하고, 
다양한 컴파일러 (gcc, clang 등)와 최적화 레벨 (O0, O1, O2, O3)을 적용하여 컴파일한 후, 그 결과를 저장하도록 만들어졌습니다.

***아직, 저장된 결과를 비교하는 로직을 구현하지 못했습니다***

사용법
1. Csmith 설치
chmod +x install_csmith.sh
./install_csmith.sh

2. 실행
python3 fuzzer.py
results 폴더에 실행 결과가 저장됩니다.

특이사항
타임아웃: csmith가 계속 실행상태를 유지하는 코드를 생성하는 경우가 있어서, 각 컴파일 및 실행 단계에는 60초의 타임아웃을 설정해두었습니다. 


