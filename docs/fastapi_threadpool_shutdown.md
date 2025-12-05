# FastAPI ThreadPoolExecutor 안전한 종료 처리

## 문제

FastAPI에서 `ThreadPoolExecutor` 사용 시 앱 종료할 때 쓰레드 풀 정리 안 하면:
- 실행 중인 작업 강제 종료 → 데이터 손실
- 리소스 누수 (메모리, 파일 핸들)
- `ResourceWarning: unclosed ThreadPoolExecutor` 경고

## 해결

### 1. Service에 shutdown 메서드 추가

```python
# src/services/report_service.py
from concurrent.futures import ThreadPoolExecutor

class ReportService:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=4)

    def shutdown(self):
        """쓰레드 풀 정리"""
        if self._executor:
            self._executor.shutdown(wait=True)  # 실행 중인 작업 완료 대기
            self._executor = None
```

**핵심**: `wait=True`면 실행 중인 작업 완료까지 대기, `False`면 즉시 종료

### 2. FastAPI 이벤트 핸들러에서 호출

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

report_service_instance = None
analysis_service_instance = None

@app.on_event("startup")
async def startup_event():
    global report_service_instance, analysis_service_instance
    report_service_instance = ReportService()
    analysis_service_instance = AnalysisService()

@app.on_event("shutdown")
async def shutdown_event():
    global report_service_instance, analysis_service_instance

    if report_service_instance:
        report_service_instance.shutdown()

    if analysis_service_instance and hasattr(analysis_service_instance, 'shutdown'):
        analysis_service_instance.shutdown()
```

### 3. 백그라운드 작업은 데몬 스레드로

```python
# ai_agent/utils/ttl_cleaner.py
import threading

def setup_background_cleanup(interval_hours: int = 1):
    def cleanup_loop():
        while True:
            cleanup_expired_sessions()
            time.sleep(interval_hours * 3600)

    # daemon=True: 메인 프로세스 종료 시 자동 종료
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
```

**데몬 스레드 특징**:
- 메인 프로세스 종료하면 강제 종료됨
- 중요한 작업 X (데이터 손실 가능)
- 로그 정리, 캐시 정리 같은 부가 작업에만 사용

## 실행 흐름

```
앱 시작
  ↓
startup_event()
  ├─ ReportService 초기화 (ThreadPoolExecutor 생성)
  └─ Background cleanup 시작 (daemon thread)
  ↓
앱 실행
  ↓
Ctrl+C / SIGTERM
  ↓
shutdown_event()
  ├─ executor.shutdown(wait=True)  # 작업 완료 대기
  └─ daemon thread 자동 종료
  ↓
종료
```

## 비교

### ❌ 잘못된 방법
```python
executor = ThreadPoolExecutor(max_workers=4)
# 앱 종료 시 executor 정리 안 함
```

### ✅ 올바른 방법
```python
def shutdown(self):
    if self._executor:
        self._executor.shutdown(wait=True)
        self._executor = None
```

## 확인

앱 종료 시 로그 확인:
```
INFO: Application shutting down
INFO: Shutting down ReportService thread pool executor
INFO: ReportService shutdown complete
INFO: All services shut down successfully
```

`ResourceWarning` 경고 없으면 성공

## 추가 팁

**Timeout 설정** (작업이 너무 오래 걸리는 경우):
```python
def shutdown(self):
    if self._executor:
        # 최대 30초 대기
        self._executor.shutdown(wait=True)
```

**Signal 직접 처리** (필요한 경우):
```python
import signal
import sys

def signal_handler(sig, frame):
    shutdown_event()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```
