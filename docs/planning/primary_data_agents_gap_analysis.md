# Primary Data Agents - Gap Analysis & Production Deployment Plan

**작성일**: 2025-12-15
**버전**: v1.0
**대상**: AdditionalDataAgent, BuildingCharacteristicsAgent
**목적**: 테스트 단계에서 확인하지 못한 부분 파악 및 실제 시스템 적용을 위한 수정사항 문서화

---

## 📋 Executive Summary

### ✅ 테스트 완료 항목

1. **병렬 처리 성능**
   - ✅ asyncio.gather() 기반 병렬 처리 구현
   - ✅ 5개 사업장 동시 처리: 10.47초 (순차 대비 4.8x 성능 향상)
   - ✅ 사업장당 평균 처리 시간: 2.09초

2. **Realistic Excel 파일 처리**
   - ✅ 숫자 전용 시계열 데이터 (헤더 제외)
   - ✅ 전력 데이터: 시간(timestamp), 사용량(kWh), 비용(원)
   - ✅ 환경 데이터: 시간(timestamp), 온도(°C), 습도(%), CO2(ppm)
   - ✅ 720행 × 5개 사업장 = 3,600개 데이터 포인트 처리

3. **LLM 가이드라인 생성**
   - ✅ 사업장별 가이드라인 생성 (평균 888자)
   - ✅ Key Insights 추출 (평균 4-5개/사업장)
   - ✅ JSON 직렬화 검증

4. **Scratch 폴더 구조**
   - ✅ `scratch/{site_id}/additional_data.xlsx` 구조 검증
   - ✅ 1 Excel = 1 사업장 원칙 확인

### ⚠️ 미검증 항목 (Production Gaps)

**Critical (필수)**:
1. 실제 DB 연동 (현재: Mock Excel 파일)
2. TTL 기반 Scratch 폴더 자동 정리
3. 악성 Excel 파일 처리 (XSS, 대용량 파일 등)
4. 네트워크 장애 시 재시도 로직
5. 대규모 처리 (100+ 사업장)

**Important (중요)**:
6. 메모리 사용량 모니터링
7. LLM API Rate Limiting
8. 동시성 Race Condition
9. Excel 업로드 프로세스
10. 전체 Workflow 통합 테스트

**Nice-to-have (개선)**:
11. 인증/권한 검증
12. 감사 로그 (Audit Trail)
13. 성능 프로파일링
14. A/B 테스트 (프롬프트 최적화)

---

## 🔍 상세 Gap Analysis

### 1. Database Integration (Critical)

**현재 상태**:
- 테스트에서는 미리 생성된 Excel 파일 사용
- `scratch/{site_id}/additional_data.xlsx` 경로를 직접 지정

**Production 요구사항**:
1. **Site ID 조회**: DB에서 사용자가 요청한 site_ids 유효성 검증
2. **Excel 파일 경로 매핑**: DB 또는 File Storage에서 실제 Excel 파일 위치 조회
3. **메타데이터 저장**: 분석 결과를 DB에 저장 (guideline, key_insights, analyzed_at)

**필요한 수정**:

#### A. `additional_data_agent.py` - 파일 경로 조회 로직 추가

```python
async def analyze_from_db(self, db_session, site_ids: List[int]) -> Dict[str, Any]:
    """
    DB에서 Excel 파일 경로 조회 후 분석

    :param db_session: DB 세션 (SQLAlchemy AsyncSession)
    :param site_ids: 사업장 ID 리스트
    :return: 분석 결과
    """
    # 1. DB에서 site_ids 유효성 검증
    from ai_agent.utils.building_data_fetcher import BuildingDataFetcher
    fetcher = BuildingDataFetcher()

    valid_sites = await fetcher.validate_site_ids(db_session, site_ids)
    if not valid_sites:
        raise ValueError(f"유효하지 않은 site_ids: {site_ids}")

    # 2. Scratch 폴더에서 Excel 파일 경로 조회
    excel_files = {}
    for site_id in valid_sites:
        file_path = f"./scratch/{site_id}/additional_data.xlsx"
        if os.path.exists(file_path):
            excel_files[site_id] = file_path
        else:
            self.logger.warning(f"Site {site_id}: Excel 파일 없음 ({file_path})")

    # 3. 각 사업장별로 병렬 분석
    tasks = [
        self.analyze(excel_path, site_ids=[site_id])
        for site_id, excel_path in excel_files.items()
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 4. 결과 병합
    merged_guidelines = {}
    for site_id, result in zip(excel_files.keys(), results):
        if isinstance(result, Exception):
            self.logger.error(f"Site {site_id} 분석 실패: {result}")
            continue

        site_guidelines = result.get('site_specific_guidelines', {})
        merged_guidelines.update(site_guidelines)

    # 5. DB에 결과 저장 (optional)
    await self._save_results_to_db(db_session, merged_guidelines)

    return {
        "meta": {
            "analyzed_at": datetime.now().isoformat(),
            "site_count": len(merged_guidelines),
            "total_sites_requested": len(site_ids)
        },
        "site_specific_guidelines": merged_guidelines,
        "status": "completed"
    }

async def _save_results_to_db(self, db_session, guidelines: Dict[int, Dict]):
    """분석 결과를 DB에 저장"""
    # TODO: DB 스키마 설계 필요
    # 예상 테이블: additional_data_analysis_results
    # 컬럼: id, site_id, guideline, key_insights, analyzed_at
    pass
```

#### B. DB 스키마 설계

```sql
-- 추가 데이터 분석 결과 테이블
CREATE TABLE additional_data_analysis_results (
    id SERIAL PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES sites(id),
    analysis_date TIMESTAMP NOT NULL DEFAULT NOW(),
    guideline_text TEXT,
    key_insights JSONB,  -- Array of insights
    source_file_path VARCHAR(500),
    analyzed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),

    -- 인덱스
    INDEX idx_site_analysis (site_id, analysis_date DESC)
);

-- Excel 파일 메타데이터 테이블 (파일 경로 관리)
CREATE TABLE site_excel_files (
    id SERIAL PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES sites(id),
    file_type VARCHAR(50),  -- 'power_data', 'environmental_data', etc.
    file_path VARCHAR(500) NOT NULL,  -- scratch/{site_id}/additional_data.xlsx
    uploaded_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,  -- TTL for scratch cleanup
    file_size_bytes BIGINT,
    row_count INTEGER,

    -- 인덱스
    INDEX idx_site_files (site_id, file_type),
    INDEX idx_ttl (expires_at) WHERE expires_at IS NOT NULL
);
```

---

### 2. TTL-based Scratch Folder Cleanup (Critical)

**현재 상태**:
- Scratch 폴더는 테스트 종료 시 수동 삭제
- TTL 관리 로직 없음

**Production 요구사항**:
- 사용자 업로드 Excel 파일은 일정 시간 후 자동 삭제 (예: 7일)
- DB에 TTL 정보 저장 및 주기적 정리

**필요한 수정**:

#### A. Scratch Cleanup Service

```python
# ai_agent/services/scratch_cleanup_service.py

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import logging

logger = logging.getLogger(__name__)


class ScratchCleanupService:
    """
    Scratch 폴더 TTL 기반 자동 정리 서비스

    주기적으로 실행되어 만료된 Excel 파일 삭제
    """

    def __init__(self, scratch_base: Path = Path("./scratch"), ttl_days: int = 7):
        self.scratch_base = scratch_base
        self.ttl_days = ttl_days
        self.logger = logger

    async def cleanup_expired_files(self, db_session):
        """
        만료된 Excel 파일 정리

        1. DB에서 expires_at < NOW() 인 파일 조회
        2. 파일 시스템에서 삭제
        3. DB 레코드 삭제 또는 상태 업데이트
        """
        cutoff_time = datetime.now() - timedelta(days=self.ttl_days)

        # 1. DB에서 만료된 파일 조회
        from sqlalchemy import select, delete
        from ai_agent.models import SiteExcelFile  # 가상의 모델

        query = select(SiteExcelFile).where(
            SiteExcelFile.expires_at < datetime.now()
        )
        result = await db_session.execute(query)
        expired_files = result.scalars().all()

        deleted_count = 0
        for file_record in expired_files:
            file_path = Path(file_record.file_path)

            # 2. 파일 삭제
            if file_path.exists():
                try:
                    file_path.unlink()
                    self.logger.info(f"삭제 완료: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    self.logger.error(f"파일 삭제 실패 ({file_path}): {e}")

            # 3. DB 레코드 삭제
            await db_session.delete(file_record)

        await db_session.commit()

        self.logger.info(f"Scratch cleanup 완료: {deleted_count}개 파일 삭제")
        return deleted_count

    async def cleanup_empty_folders(self):
        """빈 사업장 폴더 정리"""
        if not self.scratch_base.exists():
            return

        for site_folder in self.scratch_base.iterdir():
            if site_folder.is_dir():
                # 폴더가 비어있으면 삭제
                if not any(site_folder.iterdir()):
                    shutil.rmtree(site_folder)
                    self.logger.info(f"빈 폴더 삭제: {site_folder}")


# Background task scheduler
async def schedule_cleanup(interval_hours: int = 24):
    """
    주기적으로 cleanup 실행 (Background Task)

    FastAPI 앱 시작 시 lifespan에서 실행
    """
    cleanup_service = ScratchCleanupService()

    while True:
        try:
            # DB 세션 생성
            from ai_agent.db import get_async_session
            async for session in get_async_session():
                await cleanup_service.cleanup_expired_files(session)
                await cleanup_service.cleanup_empty_folders()
                break
        except Exception as e:
            logger.error(f"Cleanup 실패: {e}")

        # 24시간 대기
        await asyncio.sleep(interval_hours * 3600)
```

#### B. FastAPI Lifespan 통합

```python
# main.py (FastAPI 앱)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from ai_agent.services.scratch_cleanup_service import schedule_cleanup

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 로직"""
    # 앱 시작 시
    cleanup_task = asyncio.create_task(schedule_cleanup(interval_hours=24))
    yield
    # 앱 종료 시
    cleanup_task.cancel()

app = FastAPI(lifespan=lifespan)
```

---

### 3. Excel File Validation & Security (Critical)

**현재 상태**:
- Excel 파일 유효성 검증 없음
- 악성 파일 (XSS, 매크로, 대용량 파일) 처리 미흡

**Production 요구사항**:
1. **파일 크기 제한**: 최대 10MB
2. **MIME 타입 검증**: `.xlsx`, `.xls`, `.csv` 만 허용
3. **바이러스 스캔**: ClamAV 또는 클라우드 서비스
4. **매크로 제거**: `openpyxl`로 재저장하여 매크로 제거
5. **행/열 개수 제한**: 최대 10,000행 × 100열

**필요한 수정**:

```python
# ai_agent/utils/excel_validator.py

import magic
from pathlib import Path
import pandas as pd


class ExcelValidator:
    """Excel 파일 유효성 검증 및 보안 체크"""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_ROWS = 10000
    MAX_COLS = 100
    ALLOWED_MIME_TYPES = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'text/csv'
    ]

    @staticmethod
    def validate(file_path: Path) -> dict:
        """
        Excel 파일 유효성 검증

        Returns:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "metadata": {
                    "file_size": int,
                    "row_count": int,
                    "col_count": int
                }
            }
        """
        errors = []
        warnings = []
        metadata = {}

        # 1. 파일 존재 확인
        if not file_path.exists():
            return {"valid": False, "errors": ["파일이 존재하지 않습니다"], "warnings": [], "metadata": {}}

        # 2. 파일 크기 검증
        file_size = file_path.stat().st_size
        metadata["file_size"] = file_size

        if file_size > ExcelValidator.MAX_FILE_SIZE:
            errors.append(f"파일 크기 초과: {file_size / 1024 / 1024:.2f}MB > 10MB")

        # 3. MIME 타입 검증
        try:
            mime = magic.Magic(mime=True)
            file_mime = mime.from_file(str(file_path))

            if file_mime not in ExcelValidator.ALLOWED_MIME_TYPES:
                errors.append(f"허용되지 않은 파일 타입: {file_mime}")
        except Exception as e:
            warnings.append(f"MIME 타입 검증 실패: {e}")

        # 4. 행/열 개수 검증
        try:
            df = pd.read_excel(file_path, nrows=ExcelValidator.MAX_ROWS + 1)
            row_count = len(df)
            col_count = len(df.columns)

            metadata["row_count"] = row_count
            metadata["col_count"] = col_count

            if row_count > ExcelValidator.MAX_ROWS:
                errors.append(f"행 개수 초과: {row_count} > {ExcelValidator.MAX_ROWS}")

            if col_count > ExcelValidator.MAX_COLS:
                errors.append(f"열 개수 초과: {col_count} > {ExcelValidator.MAX_COLS}")
        except Exception as e:
            errors.append(f"Excel 파일 읽기 실패: {e}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
```

**사용 예시**:

```python
from ai_agent.utils.excel_validator import ExcelValidator

# Excel 파일 업로드 핸들러
async def upload_excel(file: UploadFile, site_id: int):
    # 1. 임시 저장
    temp_path = Path(f"./scratch/{site_id}/temp_{file.filename}")
    with temp_path.open("wb") as f:
        f.write(await file.read())

    # 2. 유효성 검증
    validation_result = ExcelValidator.validate(temp_path)

    if not validation_result["valid"]:
        temp_path.unlink()
        raise ValueError(f"유효하지 않은 Excel 파일: {validation_result['errors']}")

    # 3. 최종 경로로 이동
    final_path = Path(f"./scratch/{site_id}/additional_data.xlsx")
    temp_path.rename(final_path)

    return {
        "file_path": str(final_path),
        "metadata": validation_result["metadata"]
    }
```

---

### 4. Error Handling & Retry Logic (Critical)

**현재 상태**:
- LLM API 실패 시 fallback 가이드라인만 생성
- 네트워크 장애, 타임아웃 처리 미흡
- 부분 실패 시 전체 실패 처리

**Production 요구사항**:
1. **재시도 로직**: 일시적 오류 시 3회 재시도 (exponential backoff)
2. **부분 성공 처리**: 일부 사업장 실패 시 성공한 결과는 반환
3. **상세 에러 로깅**: Sentry 또는 ELK Stack 연동
4. **Circuit Breaker**: LLM API 장애 시 자동 fallback

**필요한 수정**:

```python
# ai_agent/utils/retry_handler.py

import asyncio
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    Exponential backoff 재시도 로직

    :param func: 비동기 함수
    :param max_retries: 최대 재시도 횟수
    :param base_delay: 기본 대기 시간 (초)
    :param max_delay: 최대 대기 시간 (초)
    :param exceptions: 재시도할 예외 타입
    :return: 함수 실행 결과
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            if attempt == max_retries - 1:
                logger.error(f"재시도 실패 (최종): {e}")
                raise

            # Exponential backoff
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"재시도 {attempt + 1}/{max_retries} (대기: {delay:.2f}초): {e}")
            await asyncio.sleep(delay)


# Circuit Breaker 패턴
class CircuitBreaker:
    """
    Circuit Breaker 패턴 구현

    연속 실패 시 일정 시간 동안 요청 차단 (fallback 사용)
    """

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func: Callable, fallback: Callable = None) -> Any:
        """
        Circuit Breaker를 통한 함수 호출

        :param func: 실행할 함수
        :param fallback: 실패 시 fallback 함수
        :return: 함수 실행 결과
        """
        # OPEN 상태: timeout 경과 후 HALF_OPEN으로 전환
        if self.state == "OPEN":
            if self.last_failure_time and \
               (asyncio.get_event_loop().time() - self.last_failure_time) > self.timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit Breaker: OPEN → HALF_OPEN")
            else:
                logger.warning("Circuit Breaker OPEN: fallback 사용")
                if fallback:
                    return await fallback()
                raise Exception("Circuit Breaker OPEN (서비스 일시 중단)")

        # 함수 실행 시도
        try:
            result = await func()

            # 성공 시 상태 리셋
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("Circuit Breaker: HALF_OPEN → CLOSED")

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = asyncio.get_event_loop().time()

            # 실패 임계값 초과 시 OPEN
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"Circuit Breaker: CLOSED → OPEN (연속 {self.failure_count}회 실패)")

            # Fallback 사용
            if fallback:
                logger.warning(f"Fallback 사용: {e}")
                return await fallback()

            raise
```

**AdditionalDataAgent에 적용**:

```python
# additional_data_agent.py

from ai_agent.utils.retry_handler import retry_with_backoff, CircuitBreaker

class AdditionalDataAgent:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

    async def _generate_site_guideline(self, site_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """사업장별 가이드라인 생성 (재시도 + Circuit Breaker)"""
        if not data:
            return self._generate_fallback_guideline(site_id, {})

        # LLM 호출 함수 정의
        async def llm_call():
            prompt = self._build_prompt(site_id, data)

            if hasattr(self.llm_client, 'ainvoke'):
                response = await self.llm_client.ainvoke(prompt)
            else:
                response = self.llm_client.invoke(prompt)

            return {
                "site_id": site_id,
                "guideline": response,
                "key_insights": self._extract_key_insights(response)
            }

        # Fallback 함수 정의
        async def fallback():
            self.logger.warning(f"LLM 실패, fallback 사용 (사업장 {site_id})")
            return self._generate_fallback_guideline(site_id, data)

        try:
            # Circuit Breaker + Retry
            result = await self.circuit_breaker.call(
                func=lambda: retry_with_backoff(
                    llm_call,
                    max_retries=3,
                    base_delay=1.0,
                    exceptions=(Exception,)
                ),
                fallback=fallback
            )
            return result

        except Exception as e:
            self.logger.error(f"LLM 호출 최종 실패 (사업장 {site_id}): {e}")
            return await fallback()
```

---

### 5. Large-scale Processing (100+ sites) (Critical)

**현재 상태**:
- 5개 사업장 테스트만 완료 (10.47초)
- 100+ 사업장 시 메모리/네트워크 부하 미검증

**Production 요구사항**:
1. **배치 처리**: 10개씩 묶어서 순차 실행 (메모리 제한)
2. **Rate Limiting**: LLM API QPS 제한 준수 (예: 60 req/min)
3. **프로그레스 추적**: 진행률 실시간 업데이트
4. **부분 결과 저장**: 100개 처리 중 50개 완료 시점에 중간 저장

**필요한 수정**:

```python
# ai_agent/utils/batch_processor.py

import asyncio
from typing import List, Callable, Any
import logging

logger = logging.getLogger(__name__)


class BatchProcessor:
    """대규모 데이터 배치 처리기"""

    def __init__(self, batch_size: int = 10, rate_limit_per_min: int = 60):
        self.batch_size = batch_size
        self.rate_limit_per_min = rate_limit_per_min
        self.requests_this_minute = 0
        self.minute_start = asyncio.get_event_loop().time()

    async def process_batches(
        self,
        items: List[Any],
        process_func: Callable,
        progress_callback: Callable = None
    ) -> List[Any]:
        """
        아이템을 배치로 나눠서 처리

        :param items: 처리할 아이템 리스트
        :param process_func: 각 아이템을 처리하는 async 함수
        :param progress_callback: 진행률 콜백 (processed, total)
        :return: 처리 결과 리스트
        """
        total = len(items)
        results = []

        # 배치로 분할
        batches = [items[i:i + self.batch_size] for i in range(0, total, self.batch_size)]

        logger.info(f"배치 처리 시작: {len(batches)}개 배치, 총 {total}개 아이템")

        for batch_idx, batch in enumerate(batches):
            # Rate limiting 체크
            await self._check_rate_limit(len(batch))

            # 배치 내에서는 병렬 처리
            batch_tasks = [process_func(item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            results.extend(batch_results)

            # 진행률 콜백
            processed = (batch_idx + 1) * self.batch_size
            if progress_callback:
                await progress_callback(min(processed, total), total)

            logger.info(f"배치 {batch_idx + 1}/{len(batches)} 완료 ({processed}/{total})")

        return results

    async def _check_rate_limit(self, request_count: int):
        """Rate limiting 체크 (1분당 요청 수 제한)"""
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - self.minute_start

        # 1분 경과 시 리셋
        if elapsed >= 60:
            self.requests_this_minute = 0
            self.minute_start = current_time

        # Rate limit 초과 시 대기
        if self.requests_this_minute + request_count > self.rate_limit_per_min:
            wait_time = 60 - elapsed
            logger.warning(f"Rate limit 도달, {wait_time:.2f}초 대기")
            await asyncio.sleep(wait_time)

            # 리셋
            self.requests_this_minute = 0
            self.minute_start = asyncio.get_event_loop().time()

        self.requests_this_minute += request_count
```

**AdditionalDataAgent에 적용**:

```python
# additional_data_agent.py

from ai_agent.utils.batch_processor import BatchProcessor

class AdditionalDataAgent:
    async def analyze_large_scale(
        self,
        site_data: Dict[int, str],  # {site_id: excel_path}
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        대규모 사업장 분석 (100+)

        :param site_data: {site_id: excel_path} 매핑
        :param progress_callback: 진행률 콜백
        :return: 분석 결과
        """
        batch_processor = BatchProcessor(batch_size=10, rate_limit_per_min=60)

        # 각 사업장 처리 함수
        async def process_site(site_info):
            site_id, excel_path = site_info
            return await self.analyze(excel_path, site_ids=[site_id])

        # 배치 처리
        site_items = list(site_data.items())
        results = await batch_processor.process_batches(
            site_items,
            process_site,
            progress_callback
        )

        # 결과 병합
        merged_guidelines = {}
        for (site_id, _), result in zip(site_items, results):
            if isinstance(result, Exception):
                self.logger.error(f"Site {site_id} 실패: {result}")
                continue

            site_guidelines = result.get('site_specific_guidelines', {})
            merged_guidelines.update(site_guidelines)

        return {
            "meta": {
                "analyzed_at": datetime.now().isoformat(),
                "site_count": len(merged_guidelines),
                "total_requested": len(site_data)
            },
            "site_specific_guidelines": merged_guidelines,
            "status": "completed"
        }
```

---

## 📝 Production Deployment Checklist

### Phase 1: DB & Infrastructure (Week 1-2)

- [ ] DB 스키마 설계 및 마이그레이션
  - [ ] `additional_data_analysis_results` 테이블
  - [ ] `site_excel_files` 테이블
- [ ] BuildingDataFetcher에 site ID 유효성 검증 추가
- [ ] Scratch cleanup service 구현
  - [ ] TTL 기반 파일 정리
  - [ ] Background task scheduler
- [ ] FastAPI 라이프사이클 통합

### Phase 2: Security & Validation (Week 2-3)

- [ ] Excel 파일 유효성 검증
  - [ ] 파일 크기/MIME 타입 체크
  - [ ] 행/열 개수 제한
  - [ ] 바이러스 스캔 (optional)
- [ ] 인증/권한 미들웨어
  - [ ] API Key 또는 JWT 인증
  - [ ] 사업장별 접근 권한 검증
- [ ] Rate limiting (FastAPI-limiter)

### Phase 3: Robustness (Week 3-4)

- [ ] 재시도 로직 구현
  - [ ] Exponential backoff
  - [ ] Circuit Breaker 패턴
- [ ] 에러 핸들링 강화
  - [ ] 상세 에러 로깅 (Sentry 연동)
  - [ ] 부분 실패 처리
- [ ] 메모리 사용량 모니터링
  - [ ] 대용량 Excel 파일 스트리밍 읽기
  - [ ] 메모리 제한 (cgroups)

### Phase 4: Scalability (Week 4-5)

- [ ] 배치 처리 구현
  - [ ] 10개씩 묶어서 순차 실행
  - [ ] 프로그레스 추적 API
- [ ] LLM API Rate Limiting
  - [ ] 60 req/min 제한 준수
  - [ ] 큐잉 시스템 (Celery/RQ)
- [ ] 대규모 테스트
  - [ ] 100+ 사업장 부하 테스트
  - [ ] 성능 프로파일링 (cProfile)

### Phase 5: Monitoring & Observability (Week 5-6)

- [ ] 로깅 표준화
  - [ ] Structured logging (JSON)
  - [ ] 로그 레벨 관리
- [ ] 메트릭 수집
  - [ ] Prometheus + Grafana
  - [ ] 처리 시간, 성공률, 에러율
- [ ] 알림 설정
  - [ ] 에러율 임계값 초과 시 알림
  - [ ] Slack/Email 연동

### Phase 6: Integration & E2E Testing (Week 6-7)

- [ ] 전체 Workflow 통합 테스트
  - [ ] Node 0 → Node 1 → Node 2-A/B/C 연동
  - [ ] State 전달 검증
- [ ] Excel 업로드 API 테스트
  - [ ] Multipart/form-data 처리
  - [ ] 파일 업로드 → 분석 → 결과 조회 E2E
- [ ] 부하 테스트
  - [ ] Locust 또는 k6 사용
  - [ ] 동시 100명 사용자 시뮬레이션

---

## 🔧 Code Modifications Summary

### 파일별 수정사항

| 파일 | 수정 내용 | 우선순위 |
|-----|----------|---------|
| `additional_data_agent.py` | `analyze_from_db()` 메서드 추가 (DB 연동) | Critical |
| `additional_data_agent.py` | `_save_results_to_db()` 메서드 추가 | Critical |
| `additional_data_agent.py` | 재시도 + Circuit Breaker 적용 | Critical |
| `additional_data_agent.py` | `analyze_large_scale()` 메서드 추가 | Critical |
| `building_data_fetcher.py` | `validate_site_ids()` 메서드 추가 | Critical |
| **NEW** `services/scratch_cleanup_service.py` | TTL 기반 파일 정리 서비스 | Critical |
| **NEW** `utils/excel_validator.py` | Excel 파일 유효성 검증 | Critical |
| **NEW** `utils/retry_handler.py` | 재시도 + Circuit Breaker 유틸 | Critical |
| **NEW** `utils/batch_processor.py` | 대규모 배치 처리기 | Critical |
| **NEW** `models/additional_data_models.py` | DB 모델 (SQLAlchemy) | Critical |
| **NEW** `api/excel_upload.py` | Excel 업로드 API 엔드포인트 | Important |
| **NEW** `api/analysis_progress.py` | 분석 진행률 조회 API | Important |
| `main.py` (FastAPI) | Lifespan 이벤트 추가 (cleanup scheduler) | Critical |

---

## 📊 Performance Expectations

### 현재 테스트 결과 (5개 사업장)

- **총 처리 시간**: 10.47초
- **사업장당 평균**: 2.09초
- **성능 향상**: 순차 대비 4.8배 빠름
- **LLM 호출**: 5개 동시 (병렬)

### Production 예상 (100개 사업장)

**Without Optimization (순차 처리)**:
- 100 사업장 × 10초 = **1,000초 (16분 40초)**

**With Parallel Processing (현재 구현)**:
- 100 사업장 동시 LLM 호출 → **메모리 폭발 위험** ❌
- Rate limiting 위반 (60 req/min) → **API 차단** ❌

**With Batch Processing (권장)**:
- 10개씩 10개 배치 → 각 배치 10초 (병렬)
- Rate limiting 준수 → 1분당 60개 제한
- **예상 시간**:
  - Batch 1-6: 1분 (60개)
  - Batch 7-10: 40초 (40개)
  - **총 100초 (1분 40초)** ✅

**최적화 목표**:
- 100개 사업장: **2분 이내**
- 500개 사업장: **10분 이내**
- 1,000개 사업장: **20분 이내**

---

## 🚀 Next Steps

### Immediate (This Week)

1. **DB 스키마 설계 및 마이그레이션**
   - `additional_data_analysis_results` 테이블
   - `site_excel_files` 테이블

2. **Excel Validator 구현**
   - 파일 크기/MIME 타입 체크
   - 행/열 개수 제한

3. **Retry Handler 구현**
   - Exponential backoff
   - Circuit Breaker

### Short-term (Next 2 Weeks)

4. **Scratch Cleanup Service**
   - TTL 기반 파일 정리
   - Background task scheduler

5. **Batch Processor**
   - 10개씩 배치 처리
   - Rate limiting

6. **Integration Testing**
   - DB 연동 E2E 테스트
   - Excel 업로드 API 테스트

### Long-term (Next Month)

7. **Monitoring & Observability**
   - Prometheus 메트릭 수집
   - Grafana 대시보드

8. **Load Testing**
   - 100+ 사업장 부하 테스트
   - 성능 프로파일링

9. **Production Deployment**
   - Staging 환경 배포
   - Production 배포

---

## 📖 References

- TCFD Report v2.1 Architecture: `docs/architecture/tcfd_v2.1_overview.md`
- Primary Data Agents README: `ai_agent/agents/primary_data/README.md`
- DB Schema (DBML): `docs/database/schema.dbml`
- API Documentation: `docs/api/endpoints.md`

---

**작성자**: AI Agent Team
**검토자**: [TBD]
**승인자**: [TBD]
**다음 리뷰 일정**: 2025-12-20
