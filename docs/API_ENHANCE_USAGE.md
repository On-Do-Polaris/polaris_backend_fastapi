# Analysis Enhancement API 사용 가이드

## 개요

`/api/sites/{site_id}/analysis/enhance` API는 기존 분석 결과에 추가 데이터를 반영하여 분석을 향상시키는 엔드포인트입니다.

**핵심 특징**:
- Node 1~4 (ModelOps 데이터) 결과를 **캐시에서 재사용**
- Node 5 이후 (LLM 분석) 만 재실행
- 비용 효율적이고 빠른 향상 분석

---

## 사용자 흐름

### Scenario 1: 기본 분석 후 추가 데이터 반영

```
사용자: "일단 기본 정보로 분석 시작해줘"
  ↓
1차 실행: POST /api/sites/{site_id}/analysis/start
{
  "site": {
    "id": "uuid",
    "name": "서울 본사",
    "latitude": 37.5665,
    "longitude": 126.9780
  }
}
→ Response: { "jobId": "job-123", "status": "completed" }

사용자: "아 그리고 태양광 200kW 설치 계획 있어"
  ↓
2차 실행: POST /api/sites/{site_id}/analysis/enhance
{
  "jobId": "job-123",
  "additionalData": {
    "rawText": "태양광 200kW 설치 예정, 2025년 3월 준공"
  }
}
→ Response: { "jobId": "job-456", "status": "completed" }
```

### Scenario 2: 추가 정보를 점진적으로 반영

```
1차: 기본 분석
  ↓
2차: 태양광 정보 추가 (enhance)
  ↓
3차: 리모델링 정보 추가 (enhance again using job-456)
```

---

## API 명세

### POST `/api/sites/{site_id}/analysis/enhance`

**Request Body**:
```json
{
  "jobId": "original-job-uuid",
  "additionalData": {
    "rawText": "자유 형식 텍스트 (태양광 설치, 리모델링 등)",
    "metadata": {
      "source": "user_input",
      "timestamp": "2025-12-01T10:00:00Z"
    }
  }
}
```

**Response**:
```json
{
  "jobId": "new-job-uuid",
  "siteId": "site-uuid",
  "status": "completed",
  "progress": 100,
  "currentNode": "completed",
  "startedAt": "2025-12-01T10:00:00Z",
  "completedAt": "2025-12-01T10:02:30Z"
}
```

**Error Response** (404 - Cached State Not Found):
```json
{
  "code": "ENHANCEMENT_FAILED",
  "message": "Cached state not found for job_id: xxx"
}
```

---

## 내부 동작 원리

### 1. State 캐싱 (start_analysis)

```python
# src/services/analysis_service.py:124

result = await self._run_agent_analysis(site_info, additional_data=None)

# State 캐싱 (Node 1~4 결과 포함)
self._cached_states[job_id] = result.copy()
```

**캐싱되는 데이터**:
- `scratch_session_id`: Climate Data 세션 ID
- `climate_summary`: 기후 데이터 요약
- `physical_risk_scores`: H×E×V 기반 리스크 점수 (9개)
- `aal_analysis`: P×D 기반 AAL 분석 결과 (9개)
- `integrated_risk`: 통합 리스크 분석
- `target_location`, `building_info`, `asset_info`: 입력 데이터

### 2. 추가 데이터 전처리 (enhance_with_additional_data)

```python
# ai_agent/main.py:290

# 추가 데이터 State에 추가
enhanced_state['additional_data'] = additional_data

# LLM 1회 호출로 가이드라인 생성
enhanced_state = self._preprocess_additional_data(enhanced_state)

# 결과:
# enhanced_state['additional_data_guidelines'] = {
#     'building_characteristics': {
#         'relevance': 0.85,
#         'suggested_insights': ['태양광 200kW...', '전력 15% 감소...']
#     },
#     'impact_analysis': {...},
#     'strategy_generation': {...},
#     'report_generation': {...}
# }
```

### 3. Node 5 이후 재실행

```python
# ai_agent/main.py:298-316

# Node 5 이후 결과 초기화 (재실행 대상)
enhanced_state['building_characteristics'] = None
enhanced_state['report_template'] = None
enhanced_state['impact_analysis'] = None
enhanced_state['response_strategy'] = None
enhanced_state['generated_report'] = None
enhanced_state['validation_result'] = None
enhanced_state['final_report'] = None

# LangGraph 워크플로우 재실행
for state in self.workflow_graph.stream(enhanced_state):
    final_state = state
```

**재실행되는 노드**:
- Node BC: Building Characteristics (가이드라인 적용)
- Node 5: Report Template
- Node 6: Impact Analysis (가이드라인 적용)
- Node 7: Strategy Generation (가이드라인 적용)
- Node 8: Report Generation (가이드라인 적용)
- Node 9: Validation
- Node 10: Finalization

---

## 비용 및 성능

### 전체 재실행 vs 부분 재실행

| 항목 | 전체 재실행 | 부분 재실행 (enhance) |
|------|------------|---------------------|
| **Node 1** | Climate Data 수집 (30초) | ✅ 캐시 재사용 (0초) |
| **Node 2** | Physical Risk Score (ModelOps) | ✅ 캐시 재사용 |
| **Node 3** | AAL Analysis (ModelOps) | ✅ 캐시 재사용 |
| **Node 4** | Risk Integration (계산) | ✅ 캐시 재사용 |
| **전처리** | - | LLM 1회 (가이드라인 생성) |
| **Node BC** | LLM 호출 | ✅ LLM 호출 (가이드라인 적용) |
| **Node 5~8** | LLM 호출 × 4 | ✅ LLM 호출 × 4 (가이드라인 적용) |
| **Node 9~10** | LLM 호출 | ✅ LLM 호출 |
| **총 시간** | ~3분 | **~1.5분** |
| **총 비용** | 100% | **~50%** |

---

## 사용 예시

### Python Requests

```python
import requests

# 1차: 기본 분석
response1 = requests.post(
    "http://localhost:8000/api/sites/site-uuid/analysis/start",
    headers={"X-API-KEY": "your-api-key"},
    json={
        "site": {
            "id": "site-uuid",
            "name": "서울 본사",
            "latitude": 37.5665,
            "longitude": 126.9780
        }
    }
)
job_id_1 = response1.json()["jobId"]
print(f"1차 분석 완료: {job_id_1}")

# 2차: 추가 데이터 반영
response2 = requests.post(
    "http://localhost:8000/api/sites/site-uuid/analysis/enhance",
    headers={"X-API-KEY": "your-api-key"},
    json={
        "jobId": job_id_1,
        "additionalData": {
            "rawText": "태양광 200kW 설치 예정, 2025년 3월 준공. 건물 리모델링 2023년 완료."
        }
    }
)
job_id_2 = response2.json()["jobId"]
print(f"2차 분석 완료 (향상): {job_id_2}")
```

### cURL

```bash
# 1차: 기본 분석
curl -X POST "http://localhost:8000/api/sites/site-uuid/analysis/start" \
  -H "X-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "site": {
      "id": "site-uuid",
      "name": "서울 본사",
      "latitude": 37.5665,
      "longitude": 126.9780
    }
  }'

# 2차: 추가 데이터 반영
curl -X POST "http://localhost:8000/api/sites/site-uuid/analysis/enhance" \
  -H "X-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": "job-123",
    "additionalData": {
      "rawText": "태양광 200kW 설치 예정, 2025년 3월 준공"
    }
  }'
```

---

## 주의사항

### 1. 캐시 유효 기간

현재 구현에서는 **메모리 내 캐시**를 사용합니다:
- 서버 재시작 시 캐시 손실
- 프로덕션 환경에서는 Redis/DB 캐시 권장

### 2. job_id 관리

- `enhance` API는 **새로운 job_id**를 반환합니다
- 원본 job_id와 새 job_id를 모두 저장해야 히스토리 추적 가능

### 3. 추가 향상

`enhance` API는 여러 번 호출 가능:
```
job-1 (기본) → job-2 (태양광) → job-3 (리모델링)
```

각 enhance 호출 시 이전 job_id를 사용하면 됩니다.

---

## 에러 처리

### 404: Cached State Not Found

```json
{
  "code": "ENHANCEMENT_FAILED",
  "message": "Cached state not found for job_id: xxx"
}
```

**원인**:
- 서버 재시작으로 캐시 손실
- 잘못된 job_id 제공

**해결책**:
- 기본 분석(`/start`)부터 다시 실행

### 500: Enhancement Failed

```json
{
  "code": "ENHANCEMENT_FAILED",
  "message": "Error details..."
}
```

**원인**:
- LLM API 호출 실패
- State 데이터 손상

**해결책**:
- 로그 확인 후 재시도
- 필요시 기본 분석부터 재실행

---

## 모범 사례

### ✅ 권장

```python
# 1. 기본 분석 먼저 실행
job_1 = start_analysis(site_info)

# 2. 사용자가 추가 정보 제공하면 enhance
if user_provides_additional_info:
    job_2 = enhance_analysis(job_1, additional_data)
```

### ❌ 비권장

```python
# 처음부터 추가 데이터 포함
# (enhance API 필요 없음 - start에서 additionalData 사용)
job_1 = start_analysis(site_info, additional_data)
```

**이유**: `start` API도 `additionalData` 필드를 지원하므로, 처음부터 추가 데이터가 있으면 `start`에 포함하는 게 더 효율적입니다.

---

## 로드맵

### v1.1 (향후 개선)

- [ ] Redis 캐시 지원 (서버 재시작 시에도 유지)
- [ ] TTL 설정 (캐시 자동 만료)
- [ ] 캐시 히트율 메트릭
- [ ] 히스토리 추적 API (`/analysis/history/{original_job_id}`)

### v1.2

- [ ] Streaming API 지원 (진행 상황 실시간 확인)
- [ ] Webhook 알림 (분석 완료 시)
- [ ] 부분 결과 조회 (Node별 결과 확인)

---

## 문의

- API 관련 질문: backend-team@example.com
- 버그 리포트: GitHub Issues
