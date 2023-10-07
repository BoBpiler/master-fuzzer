# BoBpiler-fuzzer

기존 퍼저와 최적화 퍼저의 속도 차이를 비교하기 위한 브랜치입니다.


### 1. 필수 설치

```bash
chmod +x install.sh
sh ./install.sh
```

`install.sh` 스크립트를 실행하면 필요한 모든 설정과 파일들이 자동으로 설치됩니다.

사실 해당 브랜치에서 필요한 것은 최적화가 적용된 코드로 빌드된 clang-18, gcc-trunk 바이너리가 필요합니다.


### 2. 프로파일링 실행

```bash
python3 code_generate.py
python3 new_fuzzer.py
python3 older_fuzzer.py
```
우선, code_generate.py를 실행해서 테스트 용 코드를 1000개 생성합니다.

new_fuzzer.py, older_fuzzer.py 를 각각 실행해서 시간을 측정합니다.

## 3. 결과 저장 구조

`output` 폴더 내부에서는 각 생성기(yarpgen, csmith 등) 별로 서브폴더가 생성됩니다. 각 서브폴더 안에는 `catch`와 `temp` 두 개의 폴더가 있습니다.

- **temp**: 작업 중인 데이터가 저장됩니다.
- **catch**: 버그를 포착한 경우 해당 데이터가 저장됩니다.

각 `catch`와 `temp` 폴더 내부에는 소스 코드의 UUID를 이름으로 하는 폴더가 생성되고, 그 안에는 다음과 같은 파일들이 저장됩니다:

- 소스 코드 파일
- 컴파일된 바이너리 파일들
- 결과를 정리한 .txt와 .json 파일

### 예시 트리 구조는 다음과 같습니다.

```bash
.
├── **yarpgen**
│   ├── **temp**  (작업 중인 데이터 저장)
│   │   └── {UUID}
│   │       ├── init.h
│   │       ├── func.c
│   │       └── driver.c
│   └── **catch**  (버그를 포착한 데이터 저장)
│       ├── partial_timeout
│       │   └── {UUID}
│       │       ├── ... (GCC, Clang 등 다양한 컴파일러 결과)
│       │       ├── {UUID}_result.txt
│       │       └── {UUID}_result.json
│       └── abnormal_compile
│           └── {UUID}
│               ├── ... (GCC, Clang 등 다양한 컴파일러 결과)
│               ├── {UUID}_result.txt
│               └── {UUID}_result.json
└── **csmith**
    ├── **temp**  (작업 중인 데이터 저장)
    │   └── {UUID}
    │       └── random_program_{UUID}.c
    └── **catch**  (버그를 포착한 데이터 저장)
        └── {UUID}
            ├── ... (GCC, Clang 등 다양한 컴파일러 결과)
            ├── {UUID}_result.txt
            └── {UUID}_result.json
```

