# BoBpiler-fuzzer

gcc, clang 등의 컴파일러 버그 탐지를 위한 퍼저입니다.



**Note**: 결과를 분석하는 로직을 더 발전시켜야 할 것 같습니다.

## Telegram Notification Setup

알림을 받기 위해서는 텔레그램 봇 설정이 필요합니다.

### Steps:
1. **Get your Bot Token**: Telegram's BotFather를 통해 봇을 생성하고 토큰을 획득합니다.
2. **Find your Chat ID**: 텔레그램 봇에 메시지를 보내고 `/getUpdates` API 메서드를 사용하여 Chat ID를 찾습니다.
3. **Edit `config.py`**: 프로젝트 폴더에서 `conf.py` 파일을 열고, `TOKEN`과 `CHAT_ID` 변수에 획득한 Bot Token과 Chat ID를 할당합니다.

## 사용법

### 1. 필수 설치

```bash
chmod +x install.sh
./install.sh
```

`install.sh` 스크립트를 실행하면 필요한 모든 설정과 파일들이 자동으로 설치됩니다.

### 2. 실행

```bash
python3 fuzzer.py
```

`python3 fuzzer.py`를 실행하면 `output` 폴더가 자동으로 생성되고, 해당 폴더에는 테스트 결과가 저장됩니다.

## 3. 결과 저장 구조

`output` 폴더 내부에서는 각 생성기(yarpgen, csmith 등) 별로 서브폴더가 생성됩니다. 각 서브폴더 안에는 `catch`와 `temp` 두 개의 폴더가 있습니다.

- **temp**: 작업 중인 데이터가 저장됩니다.
- **catch**: 버그를 포착한 경우 해당 데이터가 저장됩니다.

각 `catch`와 `temp` 폴더 내부에는 소스 코드의 UUID를 이름으로 하는 폴더가 생성되고, 그 안에는 다음과 같은 파일들이 저장됩니다:

- 소스 코드 파일
- 컴파일된 바이너리 파일들
- 결과를 정리한 .txt와 .json 파일

### 예시 트리 구조는 다음과 같습니다.

```plaintext
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

## 4. 특이사항
1. 타임아웃: csmith가 계속 실행상태를 유지하는 코드를 생성하는 경우가 있어서, 각 컴파일 및 실행 단계에는 30초의 타임아웃을 설정해두었습니다.  
2. output 폴더에 생성기 별로 결과가 담겨있습니다.  
3. config.py에서 generators, compilers 부분을 수정해서 특정 부분만 실행할 수 있습니다. 추후에 옵션을 줄 수 있도록 해보겠습니다.  
4. 현재 config.py에 있는 설정으로 돌리면 CPU 자원과 메모리 사용이 극심하기 때문에 테스트 하고 싶은 옵션으로 설정해주고 실행하는 것이 좋을 것 같습니다. (컴파일러 종류, 옵션 등...)
