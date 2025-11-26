# DATABASE_URL 환경변수 제거 방법

현재 시스템에 DATABASE_URL 환경변수가 설정되어 있어서 .env 파일의 값이 무시되고 있습니다.

## 문제 상황

```
환경변수 (현재): postgresql://user:password@localhost:5432/skax_db  ← 이게 우선순위가 높음
.env 파일 (원하는 값): postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse
```

## 해결 방법

### Windows에서 환경변수 제거

#### 방법 1: GUI (추천)

1. Windows 검색에서 "환경 변수" 입력
2. "시스템 환경 변수 편집" 클릭
3. "환경 변수" 버튼 클릭
4. "사용자 변수" 또는 "시스템 변수"에서 `DATABASE_URL` 찾기
5. 선택 후 "삭제" 버튼 클릭
6. "확인"으로 저장
7. **터미널 재시작** (중요!)

#### 방법 2: PowerShell (관리자 권한)

```powershell
# 사용자 환경변수 제거
[System.Environment]::SetEnvironmentVariable('DATABASE_URL', $null, 'User')

# 시스템 환경변수 제거 (관리자 권한 필요)
[System.Environment]::SetEnvironmentVariable('DATABASE_URL', $null, 'Machine')
```

실행 후 **터미널을 완전히 종료하고 새로 열어야** 적용됩니다.

#### 방법 3: CMD (관리자 권한)

```cmd
# 사용자 환경변수 제거
setx DATABASE_URL ""

# 영구 삭제
reg delete "HKCU\Environment" /v DATABASE_URL /f
```

### 검증

터미널을 **재시작**한 후:

```bash
# 환경변수 확인
python verify_env.py
```

정상적으로 제거되면 다음과 같이 출력됩니다:

```
1. DATABASE_URL in os.environ:
   [OK] Not set (will use .env file)

3. Loading src/core/config.py:
   DATABASE_URL: postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse
   [OK] Correct value loaded!
```

## 중요 사항

- 환경변수 제거 후 **반드시 터미널을 재시작**해야 합니다
- VSCode를 사용 중이라면 **VSCode도 재시작**해야 합니다
- .env 파일에는 올바른 값이 설정되어 있으므로 환경변수만 제거하면 됩니다

## 우선순위 이해

Pydantic Settings는 다음 순서로 값을 로드합니다:

1. **환경변수** (가장 높은 우선순위) ← 현재 문제
2. .env 파일
3. 코드의 기본값

환경변수가 설정되어 있으면 .env 파일의 값은 무시됩니다.
