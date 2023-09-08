# BoBpiler-fuzzer
이 프로젝트는 Csmith와 yarpgen을 사용하여 랜덤 C 프로그램을 생성하고, 
다양한 컴파일러 (gcc, clang 등)와 최적화 레벨 (O0, O1, O2, O3)을 적용하여 컴파일한 후, 그 결과를 저장하고 비교하여 다른 결과를 구분하도록 만들었습니다.
---

**Note**: 저장된 결과를 비교하는 로직을 더 발전시켜야 할 것 같습니다.

## 사용법

### 1. 필수 설치

```bash
chmod +x install.sh
./install.sh
```

### 2. 실행
```bash
python3 fuzzer.py
```

### 3. 특이사항
1. 타임아웃: csmith가 계속 실행상태를 유지하는 코드를 생성하는 경우가 있어서, 각 컴파일 및 실행 단계에는 30초의 타임아웃을 설정해두었습니다.  
2. output 폴더에 생성기 별로 결과가 담겨있습니다.  
3. config.py에서 generators, compilers 부분을 수정해서 특정 부분만 실행할 수 있습니다. 추후에 옵션을 줄 수 있도록 해보겠습니다.  
4. 현재 config.py에 있는 설정으로 돌리면 cpu 자원과 메모리 사용이 극심하기 때문에 테스트 하고 싶은 옵션으로 설정해주고 실행하는 것이 좋을 것 같습니다.  


