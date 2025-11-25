# AAL Agent v11 API 영향도 분석 및 수정 완료 보고서

**작성일**: 2025-11-25
**버전**: v1.0
**상태**: ✅ 모든 수정 완료

---

## 📋 목차

1. [변경 사항 요약](#변경-사항-요약)
2. [영향을 받는 API 컴포넌트](#영향을-받는-api-컴포넌트)
3. [수정된 파일 목록](#수정된-파일-목록)
4. [상세 변경 내역](#상세-변경-내역)
5. [테스트 가이드](#테스트-가이드)
6. [하위 호환성](#하위-호환성)

---

## 변경 사항 요약

### AAL Agent v11 핵심 변경사항

| 항목 | v10 (이전) | v11 (현재) |
|------|-----------|-----------|
| **출력 필드** | `financial_loss` (원 단위) | `final_aal_percentage` (% 단위) |
| **계산 책임** | Agent가 모든 계산 수행 | Service가 base_aal 계산, Agent는 scaling만 |
| **메서드 시그니처** | `analyze_aal(collected_data, ...)` | `analyze_aal(base_aal, vulnerability_score)` |
| **추가 출력** | - | `vulnerability_scale`, `risk_level`, `base_aal` |

### API 영향 범위

✅ **수정 완료**: 2개 파일
⚠️ **영향 없음**: FastAPI 엔드포인트 (Mock 데이터 사용)

---

## 영향을 받는 API 컴포넌트

### 1. **ai_agent/main.py** ✅ 수정 완료
- **위치**: [ai_agent/main.py:209-228](../ai_agent/main.py#L209-L228)
- **함수**: `_print_summary()`
- **문제**: `financial_loss` 필드 참조
- **해결**: `final_aal_percentage` 사용으로 변경

### 2. **src/services/simulation_service.py** ✅ 수정 완료
- **위치**: [src/services/simulation_service.py:116-142](../src/services/simulation_service.py#L116-L142)
- **함수**: `run_relocation_simulation()`
- **문제**: `financial_loss` 필드로 AAL 계산
- **해결**: `aal_analysis` → `final_aal_percentage` 사용

### 3. **src/services/analysis_service.py** ⚠️ 영향 없음
- Mock 데이터만 반환하므로 AAL Agent 출력과 무관

---

## 수정된 파일 목록

### 1. ai_agent/main.py (v06)

#### 수정 전 (v05)
```python
# 물리적 리스크 점수
physical_risk_scores = result.get('physical_risk_scores', {})
if physical_risk_scores:
    for risk_type, risk_data in sorted_risks[:5]:
        score = risk_data.get('physical_risk_score_100', 0)
        level = risk_data.get('risk_level', 'Unknown')
        financial_loss = risk_data.get('financial_loss', 0)  # ❌ v11에서 제거됨
        print(f"  {risk_type}: {score:.2f}/100 ({level}) - Loss: {financial_loss:,.0f}원")
```

#### 수정 후 (v06)
```python
# 물리적 리스크 점수 및 AAL
physical_risk_scores = result.get('physical_risk_scores', {})
aal_analysis = result.get('aal_analysis', {})  # ✅ AAL 분석 결과 추가

if physical_risk_scores:
    for risk_type, risk_data in sorted_risks[:5]:
        score = risk_data.get('physical_risk_score_100', 0)
        level = risk_data.get('risk_level', 'Unknown')

        # AAL v11: final_aal_percentage 사용
        aal_data = aal_analysis.get(risk_type, {})
        aal_percentage = aal_data.get('final_aal_percentage', 0)  # ✅ v11 필드

        print(f"  {risk_type}: {score:.2f}/100 ({level}) - AAL: {aal_percentage:.4f}%")
```

**변경 사항**:
- ❌ `financial_loss` (원 단위) 제거
- ✅ `final_aal_percentage` (% 단위) 사용
- ✅ `aal_analysis` 딕셔너리에서 AAL 데이터 추출

---

### 2. src/services/simulation_service.py

#### 수정 전
```python
for risk_type, risk_data in base_scores.items():
    current_risks.append(RiskData(
        riskType=hazard_names.get(risk_type, risk_type),
        riskScore=int(risk_data.get('physical_risk_score_100', 0)),
        aal=risk_data.get('financial_loss', 0) / 50000000000,  # ❌ v11에서 제거됨
    ))
```

#### 수정 후
```python
# AAL 분석 결과 가져오기
base_aal_results = result.get('aal_analysis', {})  # ✅ AAL 분석 결과 추가
candidate_aal_results = candidate_result.get('aal_analysis', {})

for risk_type, risk_data in base_scores.items():
    # AAL v11: final_aal_percentage를 0-1 스케일로 변환
    aal_data = base_aal_results.get(risk_type, {})
    aal_percentage = aal_data.get('final_aal_percentage', 0.0)  # ✅ v11 필드
    aal_rate = aal_percentage / 100.0  # % → 0-1 스케일

    current_risks.append(RiskData(
        riskType=hazard_names.get(risk_type, risk_type),
        riskScore=int(risk_data.get('physical_risk_score_100', 0)),
        aal=aal_rate,  # ✅ 0-1 스케일로 변환된 AAL
    ))
```

**변경 사항**:
- ❌ `physical_risk_scores`에서 `financial_loss` 참조 제거
- ✅ `aal_analysis` 딕셔너리 추가
- ✅ `final_aal_percentage` → `aal_rate` 변환 로직 추가
- ✅ % 단위를 0-1 스케일로 변환 (`aal_percentage / 100.0`)

---

## 상세 변경 내역

### 데이터 흐름 변경

#### v10 (이전)
```
physical_risk_scores[risk_type]
  └─ financial_loss (원 단위)
      └─ API에서 직접 사용
```

#### v11 (현재)
```
aal_analysis[risk_type]
  ├─ base_aal (기본 AAL)
  ├─ vulnerability_scale (F_vuln)
  ├─ final_aal_percentage (최종 AAL %)
  ├─ insurance_rate (보험 보전율)
  └─ risk_level (위험 수준)

API 변환 로직:
  final_aal_percentage (%) → aal_rate (0-1 스케일)
```

### AAL 계산 공식 변화

#### v10
```
AAL (원) = 자산 가치 × P(H) × 손상률 × (1-IR)
→ financial_loss 필드에 원 단위로 저장
```

#### v11
```
base_aal = Σ[P_r[i] × DR_intensity_r[i]]  (AALCalculatorService)
final_aal = base_aal × F_vuln × (1-IR)    (AAL Agent)
final_aal_percentage = final_aal × 100    (% 단위)

→ API에서 % → 0-1 스케일로 변환 필요
```

---

## 테스트 가이드

### 1. 단위 테스트

#### main.py `_print_summary()` 테스트
```python
# 테스트 데이터
test_result = {
    'physical_risk_scores': {
        'extreme_heat': {
            'physical_risk_score_100': 75.5,
            'risk_level': 'High'
        }
    },
    'aal_analysis': {
        'extreme_heat': {
            'final_aal_percentage': 2.34,
            'risk_level': 'Low'
        }
    }
}

# 실행
analyzer._print_summary(test_result)

# 예상 출력:
# [SCORE] Physical Risk Scores (100-point scale):
#   extreme_heat: 75.50/100 (High) - AAL: 2.3400%
```

#### simulation_service.py 테스트
```python
# 테스트 데이터
result = {
    'physical_risk_scores': {
        'extreme_heat': {'physical_risk_score_100': 75}
    },
    'aal_analysis': {
        'extreme_heat': {'final_aal_percentage': 2.5}
    }
}

# AAL 계산 확인
aal_data = result['aal_analysis']['extreme_heat']
aal_percentage = aal_data.get('final_aal_percentage', 0.0)
aal_rate = aal_percentage / 100.0

assert aal_rate == 0.025  # 2.5% → 0.025
```

### 2. 통합 테스트

```bash
# 전체 워크플로우 실행
cd ai_agent
python main.py

# 예상 결과:
# [SCORE] Physical Risk Scores (100-point scale):
#   extreme_heat: 75.50/100 (High) - AAL: 2.3400%
#   typhoon: 70.20/100 (High) - AAL: 1.8900%
#   ...
```

### 3. API 엔드포인트 테스트

```bash
# Spring Boot 호환 API 테스트
curl -X POST http://localhost:8000/api/v1/analysis/sites/{siteId}/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "site": {
      "id": "uuid",
      "name": "Test Site",
      "latitude": 37.5665,
      "longitude": 126.9780
    }
  }'

# 응답 확인:
# {
#   "jobId": "...",
#   "status": "completed",
#   ...
# }
```

---

## 하위 호환성

### ⚠️ Breaking Changes

1. **`financial_loss` 필드 제거**
   - v10에서 `physical_risk_scores[risk_type]['financial_loss']`를 사용하던 코드는 작동하지 않음
   - **대안**: `aal_analysis[risk_type]['final_aal_percentage']` 사용

2. **데이터 구조 변경**
   - Physical Risk Score와 AAL 분석이 분리됨
   - **대안**: 두 딕셔너리를 모두 참조

### ✅ 호환성 유지

1. **FastAPI 엔드포인트**
   - Mock 데이터 사용 중이므로 영향 없음
   - 실제 데이터 연동 시 위 수정사항 적용 필요

2. **API 스키마**
   - `PhysicalRiskBarItem.financial_loss_rate` 스키마는 변경 없음
   - 내부 계산 로직만 변경됨

---

## 🔍 점검 체크리스트

- [x] `ai_agent/main.py` 수정 완료
- [x] `src/services/simulation_service.py` 수정 완료
- [x] AAL v11 출력 형식 (`final_aal_percentage`) 적용
- [x] % → 0-1 스케일 변환 로직 추가
- [x] `aal_analysis` 딕셔너리 참조 추가
- [ ] 단위 테스트 실행 (권장)
- [ ] 통합 테스트 실행 (권장)
- [ ] API 엔드포인트 테스트 (프로덕션 배포 전 필수)

---

## 📚 관련 문서

- [AAL_V11_MIGRATION_SUMMARY.md](./AAL_V11_MIGRATION_SUMMARY.md): AAL Agent v11 전체 마이그레이션 요약
- [AAL_AGENT_INCONSISTENCY_ANALYSIS.md](./AAL_AGENT_INCONSISTENCY_ANALYSIS.md): 불일치 분석 및 해결 방안
- [README.md](../README.md): 전체 시스템 개요 및 변경 이력

---

**작성자**: Claude Code
**검토 상태**: ✅ 완료
**배포 준비**: 테스트 완료 후 배포 가능
