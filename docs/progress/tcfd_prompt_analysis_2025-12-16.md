# TCFD 보고서 생성 워크플로우 LLM 프롬프팅 상세 분석

**작성일**: 2025-12-16
**분석 대상**: Node 2-A, 2-B, 2-C, 3, 4, 5, 6
**목적**: 각 노드의 LLM 프롬프트 품질 평가 및 개선방안 제안

---

## 목차

1. [Node 2-A: Scenario Analysis](#node-2-a-scenario-analysis)
2. [Node 2-B: Impact Analysis](#node-2-b-impact-analysis)
3. [Node 2-C: Mitigation Strategies](#node-2-c-mitigation-strategies)
4. [Node 3: Strategy Section](#node-3-strategy-section)
5. [Node 4: Validator](#node-4-validator)
6. [Node 5: Composer](#node-5-composer)
7. [Node 6: Finalizer](#node-6-finalizer)
8. [종합 요약 및 우선순위별 개선 권장사항](#종합-요약-및-우선순위별-개선-권장사항)

---

## Node 2-A: Scenario Analysis

### 1. 프롬프트 위치 및 구조

**메서드명**: `_analyze_scenarios_with_llm` (line 312-476)
**호출 시점**: Step 3/5 - 포트폴리오 시나리오 집계 후 LLM 기반 비교 분석 수행
**프롬프트 구조**:
- `<ROLE>`: 역할 정의 ("ELITE climate scenario analyst")
- `<CRITICAL_ANALYSIS_REQUIREMENTS>`: 5개 핵심 분석 요구사항
- `<INPUT_DATA>`: 시나리오 데이터, 템플릿 정보, 가이드라인
- `<OUTPUT_REQUIREMENTS>`: 출력 형식 정의 (5개 섹션, 800-1200 words)
- `<QUALITY_CHECKLIST>`: 품질 검증 체크리스트 (6개 항목)

### 2. 현재 프롬프트 분석

#### 2.1 강점

✅ **EXHAUSTIVE 접근**: "처음부터 완벽하게 분석" 철학을 구현하여 재분석 필요성 최소화
✅ **구조화된 분석 요구사항**: 5개 주요 카테고리로 분석 차원을 명확히 구분
  - **Scenario Differentiation** (시나리오 차별화): 4개 SSP 시나리오 명확한 구분 요구
  - **Timeline Analysis** (타임라인 분석): 단기(2024-2030) / 중기(2030-2050) / 장기(2050-2100) 3단계
  - **Risk Interpretation** (리스크 해석): AAL → 비즈니스 영향 변환 요구
  - **Strategic Implications** (전략적 시사점): 시나리오별 대응 전략 제시
  - **Stakeholder Communication** (이해관계자 소통): 투자자 관점 메시징

✅ **정량적 요구사항 명확**: AAL 값 인용, 시나리오별 차이 정량화 요구
✅ **컨텍스트 풍부**: Node 1 템플릿 참조 (tone, scenario_templates, formatting_rules)
✅ **Quality Checklist**: 6개 항목 검증으로 출력 품질 보장
  - [ ] 모든 4개 시나리오 동등한 깊이로 논의
  - [ ] AAL 값 정확 인용
  - [ ] WHY 설명 (단순 WHAT 아님)
  - [ ] 권장사항 구체적/실행 가능
  - [ ] 템플릿 톤 일치
  - [ ] TCFD Strategy 섹션에 바로 사용 가능

#### 2.2 약점

⚠️ **출력 구조 모호성**: 5개 섹션 요구하지만 실제 출력 형식이 불명확 (Markdown vs JSON)
⚠️ **사업장 수(num_sites) 정보 활용 부족**: 입력에는 포함되나 분석 지시사항에 명시되지 않음
⚠️ **토큰 효율성**: 중복된 설명이 많음 (예: "data-driven", "specific numbers" 반복)
⚠️ **예제 부재**: 기대하는 출력 샘플이 없어 LLM이 스타일을 추론해야 함
⚠️ **Fallback 전략**: LLM 실패 시 `_generate_fallback_analysis`가 너무 간단함 (시나리오별 AAL만 나열)

#### 2.3 토큰 사용량 추정

- **프롬프트 토큰**: 약 1,500-2,000 토큰
- **입력 데이터 토큰**: 약 500-1,000 토큰 (시나리오 4개 + 템플릿)
- **예상 출력 토큰**: 800-1200 words → 약 1,600-2,400 토큰
- **총 예상**: 약 3,600-5,400 토큰/호출

### 3. 개선 방안

#### 3.1 구조적 개선

**현재 문제**: OUTPUT_REQUIREMENTS에서 5개 섹션을 요구하지만 Markdown vs JSON이 명확하지 않음

**개선안**:
```markdown
<OUTPUT_FORMAT>
출력을 다음 JSON 구조로 제공하세요:
{
  "executive_summary": "2-3 문장 요약",
  "scenario_analyses": [
    {
      "scenario": "ssp1_2.6",
      "trajectory": "AAL 시작→종료 값",
      "inflection_points": ["시점1", "시점2"],
      "implications": "비즈니스 영향",
      "response": "권장 대응"
    },
    // ... 3개 더 (ssp2_4.5, ssp3_7.0, ssp5_8.5)
  ],
  "comparative_analysis": {
    "sensitivity": "시나리오 선택이 얼마나 중요한가",
    "risk_range": "최선 vs 최악 AAL 델타"
  },
  "strategic_recommendations": ["우선순위1", "우선순위2", "우선순위3"],
  "stakeholder_message": "1-2 문장"
}
</OUTPUT_FORMAT>
```

**효과**: 출력 파싱 오류 감소, 후처리 용이

#### 3.2 컨텍스트 보강

**현재 문제**: Portfolio Information에 사업장 수가 포함되나 분석 요구사항에 명시되지 않음

**개선안**:
```markdown
<PORTFOLIO_CONTEXT>
- 전체 사업장 수: {num_sites}
- 분석 대상 사업장 비율: 100% (전체 포트폴리오)
- 집계 방법: {num_sites}개 사업장의 평균 AAL

**분석 시 고려사항**:
- 사업장 수가 많을수록 포트폴리오 다각화 효과 언급 필요
- 소수 사업장의 경우 개별 사업장 리스크에 더 민감함을 언급
</PORTFOLIO_CONTEXT>
```

**효과**: LLM이 포트폴리오 규모를 고려한 분석 수행

#### 3.3 출력 형식 개선

**현재 문제**: Few-shot 예제가 없어 LLM이 출력 스타일을 추론해야 함

**개선안**: 프롬프트에 실제 출력 예제 1개 추가
```markdown
<EXAMPLE_OUTPUT>
{
  "executive_summary": "포트폴리오 AAL은 SSP1-2.6 시나리오에서 2025년 52.9%에서 2100년 45.0%로 감소하지만, SSP5-8.5 최악 시나리오에서는 85.3%까지 상승합니다. **핵심 발견**: 시나리오 선택에 따라 AAL이 최대 40.3%p 차이나며, 중간 경로(SSP2-4.5)가 가장 현실적입니다.",
  "scenario_analyses": [
    {
      "scenario": "ssp1_2.6",
      "trajectory": "52.9% (2025) → 45.0% (2100), **-7.9%p 감소**",
      "inflection_points": ["2040년 이후 AAL 하락 가속화", "2030년대 적응 투자 효과 발현"],
      "implications": "기후 적응 투자가 효과를 발휘하여 자산 가치 보존. 장기적으로 저탄소 전환에 맞춘 투자가 리스크 저감에 기여.",
      "response": "저탄소 전환에 맞춘 장기 투자 지속, 2030년 이전 주요 적응 조치 완료 목표"
    },
    // ... 3개 더
  ],
  "comparative_analysis": {
    "sensitivity": "시나리오 선택이 매우 중요함. SSP1-2.6과 SSP5-8.5 간 AAL 차이가 40.3%p로, 연평균 손실 규모가 2배 이상 차이 남.",
    "risk_range": "최선 45.0% vs 최악 85.3%, 델타 40.3%p"
  },
  "strategic_recommendations": [
    "중간 시나리오(SSP2-4.5)를 기준으로 대응 전략 수립",
    "SSP5-8.5 최악 시나리오에 대비한 비상 계획 병행",
    "2030년, 2050년 시나리오 재평가 및 전략 조정"
  ],
  "stakeholder_message": "우리는 4가지 기후 시나리오를 모두 고려하여 대응 전략을 수립했으며, 최악의 경우에도 대비할 준비가 되어 있습니다."
}
</EXAMPLE_OUTPUT>
```

**효과**: 일관된 출력 품질, LLM 추론 부담 감소

#### 3.4 토큰 효율화

**현재 문제**: CRITICAL_ANALYSIS_REQUIREMENTS에서 중복 설명이 많음

**개선안**: 중복 제거 및 간결화
```markdown
# Before (길고 중복적)
- Use clear, data-driven language (avoid jargon)
- Support claims with specific numbers from the scenarios
- Frame risks in terms of opportunities (where applicable)
- Address investor concerns: "Is this company climate-resilient?"

# After (간결)
- 명확한 언어 + 구체적 수치 인용
- 투자자 관점: "기후 회복력이 충분한가?"
```

**효과**: 프롬프트 토큰 10-15% 절감

### 4. 개선 우선순위

#### Critical (필수)
- [x] 출력 형식 명확화 (JSON vs Markdown 통일) → JSON 권장
- [x] 사업장 수 컨텍스트 명시 (`num_sites` 활용)

#### High (높음)
- [ ] Few-shot 예제 1개 추가
- [ ] Quality Checklist를 실제로 검증하는 후처리 로직 추가
- [ ] Fallback 로직 개선 (시나리오별 간단한 분석이라도 제공)

#### Medium (중간)
- [ ] 토큰 효율화 (중복 제거)
- [ ] 시나리오 비교 분석 강화 (민감도 분석)

#### Low (낮음)
- [ ] 프롬프트 언어 통일 (영어 vs 한국어)

---

## Node 2-B: Impact Analysis

### 1. 프롬프트 위치 및 구조

**메서드명**: `_analyze_single_risk_impact` (line 308-530)
**호출 시점**: Step 3/4 - LLM 기반 영향 분석 (5개 리스크 병렬 처리)
**프롬프트 구조**:
- `<ROLE>`: 역할 정의 ("ELITE climate risk impact analyst")
- `<CRITICAL_ANALYSIS_REQUIREMENTS>`: 4개 핵심 분석 카테고리
- `<INPUT_DATA>`: 리스크 정보, 사업장 데이터, 건물 특성, 추가 데이터
- `<OUTPUT_REQUIREMENTS>`: JSON 출력 형식
- `<QUALITY_CHECKLIST>`: 8개 항목 검증

### 2. 현재 프롬프트 분석

#### 2.1 강점

✅ **Building Data 통합**: BC Agent의 건물 특성 데이터를 적극 활용
  - 구조 등급 (A/B/C), 취약점 (vulnerabilities), 복원력 (resilience) 정보 제공
  - `building_impact_guide` 섹션으로 구체적 가이드 제공
  - "**Use building structural grades to refine damage estimates**" 명시

✅ **Additional Data 통합**: AD Agent의 Excel 데이터 활용 (site_specific_guidelines)
✅ **3차원 영향 분석**: 재무적/운영적/자산 영향을 균형있게 분석
✅ **정량화 요구**: KRW 금액, 다운타임 시간, AAL 감소율 등 구체적 요구
✅ **JSON 출력**: 구조화된 출력으로 후처리 용이

```json
{
  "financial_impact": "## 재무적 영향\n\n...",
  "operational_impact": "## 운영적 영향\n\n...",
  "asset_impact": "## 자산 영향\n\n...",
  "summary": "P{rank} {risk_name_kr}는..."
}
```

#### 2.2 약점

⚠️ **건물 데이터 누락 시 대응 부족**: Building Data가 없는 경우 "기본 분석 수행" 메시지만 있고 구체적 fallback 없음
⚠️ **영향받는 사업장 정보 불충분**: `_format_affected_sites_with_building`에서 최대 5개 사업장만 표시하여 나머지 정보 손실
⚠️ **포트폴리오 비율 정보 누락**: `total_num_sites` 정보는 있으나 프롬프트 INPUT_DATA에서 활용도가 낮음
⚠️ **JSON 파싱 실패 처리**: `_parse_text_response`가 너무 간단하여 텍스트 응답 시 품질 저하

#### 2.3 토큰 사용량 추정

- **프롬프트 토큰**: 약 1,200-1,500 토큰
- **입력 데이터 토큰**: 약 800-1,200 토큰 (건물 데이터 + 추가 데이터 포함)
- **예상 출력 토큰**: 600-900 words → 약 1,200-1,800 토큰
- **총 예상 (5개 병렬)**: 약 16,000-22,500 토큰

### 3. 개선 방안

#### 3.1 구조적 개선

**현재 문제**: 3차원 분석 요구사항이 일반적이고, 건물 데이터 활용이 "고려하라"는 수준

**개선안**: 분석 프레임워크를 구조화
```markdown
<ANALYSIS_FRAMEWORK>
각 영향 차원을 다음 구조로 분석하세요:

**1. 재무적 영향**
   - 직접 손실 추정 (건물 손상, 설비 교체):
     * 건물 등급이 B/C인 경우 손해액 1.5배 적용
     * AAL {total_aal}%를 금액으로 환산
   - 간접 손실 추정 (매출 손실, 고객 이탈):
     * 운영 중단 기간 × 일평균 매출
   - 보험 커버리지 고려:
     * 자기부담금, 보험료 증가 예상
   - 총 재무 노출: **KRW X억원 (연평균)**

**2. 운영적 영향**
   - 다운타임 추정:
     * 건물 취약점 (vulnerabilities)을 고려한 복구 시간
     * 예: 배수 시설 부족 → 침수 복구 +2일
   - 핵심 시스템 중단: {critical_systems_at_risk} 목록
   - 공급망 영향: 상류/하류 영향 평가
   - 고객 서비스 영향: SLA 위반 리스크

**3. 자산 영향**
   - 물리적 손상: {vulnerable_assets} 기반 손상 시나리오
   - 수명 단축: 반복적 리스크로 인한 자산 노화 가속
   - 복구 비용: 교체 vs 수리 비용 비교
</ANALYSIS_FRAMEWORK>
```

**효과**: 분석 일관성 향상, 건물 데이터 활용도 증가

#### 3.2 컨텍스트 보강

**현재 문제**: Portfolio Overview는 있으나 영향 비율 분석이 부족

**개선안**: (이미 v2.1에서 적용됨!)
```markdown
<PORTFOLIO_IMPACT_CONTEXT>
- 포트폴리오 전체 사업장 수: {total_num_sites}
- 이 리스크 영향받는 사업장 수: {num_affected_sites}
- 영향 비율: {(num_affected_sites/total_num_sites*100):.1f}%
- 영향 심각도 분포:
  * 높음 (AAL>10%): X개 사업장
  * 중간 (AAL 3-10%): Y개 사업장
  * 낮음 (AAL<3%): Z개 사업장

**분석 관점**:
- 영향 비율이 50% 이상이면 "포트폴리오 전반적 리스크"로 강조
- 영향 비율이 20% 미만이면 "국지적 리스크"로 표현
</PORTFOLIO_IMPACT_CONTEXT>
```

**효과**: LLM이 포트폴리오 관점에서 리스크 심각도 평가

#### 3.3 출력 형식 개선

**현재 문제**: 출력 예제가 없어 품질 편차 발생 가능

**개선안**: 프롬프트에 출력 예제 추가
```markdown
<OUTPUT_EXAMPLE>
{
  "financial_impact": "## 재무적 영향\n\n{risk_name_kr} 리스크로 인한 포트폴리오 총 AAL은 **{total_aal}%**입니다. 이를 금액으로 환산하면 연평균 **약 120억원**의 손실이 예상됩니다.\n\n### 건물 특성 고려\n- **B등급 건물** (3개 사업장): 구조적 취약성으로 인해 손해액이 A등급 대비 **1.5배** 증가\n- **방수 시설 미비** 사업장: 침수 시 복구 비용 **추가 30억원** 소요 예상\n- **보험 커버리지**: 현재 보험으로 60% 커버, 자기부담금 약 48억원\n\n### 재무 영향 요약\n- **직접 손실**: 연평균 80억원 (건물 손상 50억원 + 설비 교체 30억원)\n- **간접 손실**: 연평균 40억원 (매출 손실 30억원 + 고객 이탈 10억원)\n- **총 노출**: 연평균 **120억원**",
  "operational_impact": "## 운영적 영향\n\n{risk_name_kr} 발생 시 평균 **3일**의 운영 중단이 예상됩니다...",
  "asset_impact": "## 자산 영향\n\n물리적 자산 손상액은 연평균 **80억원**으로 추정됩니다...",
  "summary": "P{rank} {risk_name_kr}는 {num_affected_sites}개 사업장 ({(num_affected_sites/total_num_sites*100):.1f}%)에 영향을 미치며, 총 AAL {total_aal}%는 연평균 약 120억원의 재무 노출을 의미합니다. B등급 건물 3개 사업장의 구조적 취약성이 주요 원인이며, 즉각적인 대응이 필요합니다."
}
</OUTPUT_EXAMPLE>
```

**효과**: 일관된 분석 품질, 정량화 수준 향상

#### 3.4 예제 및 가이드 추가

**개선안**: 건물 데이터 활용 Best Practice 추가
```markdown
<BUILDING_DATA_UTILIZATION_GUIDE>
건물 특성 데이터를 다음과 같이 활용하세요:

1. **구조 등급 (Structural Grade)**
   - A등급: 기준 손해액
   - B등급: 기준 × 1.5배
   - C등급: 기준 × 2.0배

2. **취약점 (Vulnerabilities)**
   - 각 취약점당 다운타임 +1일 또는 손해액 +10% 적용
   - 예: "배수 시설 부족" → 침수 복구 시간 +2일

3. **복원력 요소 (Resilience)**
   - 각 복원력 요소당 다운타임 -0.5일 또는 손해액 -5% 적용
   - 예: "비상 발전기" → 전력 복구 시간 -1일
</BUILDING_DATA_UTILIZATION_GUIDE>
```

**효과**: 건물 데이터 활용 일관성 향상

### 4. 개선 우선순위

#### Critical (필수)
- [x] 건물 데이터 누락 시 fallback 강화 → 표준 산업 기준 적용 권장
- [x] 포트폴리오 비율 컨텍스트 명시 (v2.1에서 이미 적용됨!)

#### High (높음)
- [ ] JSON 파싱 실패 시 텍스트 파싱 로직 개선
- [ ] 출력 예제 추가
- [ ] 건물 데이터 활용 가이드 추가

#### Medium (중간)
- [ ] 영향받는 사업장 표시 개수 확대 (5개→10개)
- [ ] 토큰 효율화

#### Low (낮음)
- [ ] 추가 데이터 컨텍스트 포맷 개선

---

## Node 2-C: Mitigation Strategies

### 1. 프롬프트 위치 및 구조

**메서드명**: `_generate_single_risk_strategy` (line 192-398)
**호출 시점**: Step 1/3 - LLM 기반 대응 전략 생성 (5개 리스크 병렬 처리)
**프롬프트 구조**:
- `<ROLE>`: 역할 정의 ("ELITE climate adaptation strategist")
- `<CRITICAL_STRATEGY_REQUIREMENTS>`: 6개 핵심 전략 요구사항
- `<INPUT_DATA>`: 리스크 정보, 영향 분석, 건물 권장사항, 추가 데이터
- `<OUTPUT_REQUIREMENTS>`: JSON 출력 형식 + 품질 기준
- `<QUALITY_CHECKLIST>`: 7개 항목 검증

### 2. 현재 프롬프트 분석

#### 2.1 강점

✅ **3단계 시간축 명확**: 단기(2026)/중기(2026-2030)/장기(2020-2050년대) 구분 명확
✅ **Building Data 권장사항 통합**: BC Agent의 `mitigation_recommendations` 활용
  - 단기/중기/장기 권장사항을 건물별로 제공
  - 구조 보강, 방수 처리, 설비 이전 등 구체적 조치 포함

✅ **Additional Data 활용**: AD Agent의 site_specific_guidelines 통합
✅ **비용-효과 분석 요구**: 예상 비용, 기대 효과, ROI 정량화 요구
✅ **우선순위 정당화**: 우선순위 레벨에 대한 근거 제시 요구
✅ **JSON 출력**: 구조화된 출력으로 TextBlock 생성 용이

```json
{
  "short_term": ["조치1", "조치2", "조치3"],
  "mid_term": ["조치1", "조치2", "조치3"],
  "long_term": ["조치1", "조치2"],
  "priority": "매우 높음",
  "priority_justification": "...",
  "estimated_cost": "단기: X억원, 중기: Y억원, 장기: Z억원",
  "expected_benefit": "AAL X% → Y% 감소, ROI: N년",
  "implementation_considerations": "• ...\n• ..."
}
```

#### 2.2 약점

⚠️ **건물 데이터 누락 시 대응 부족**: "기본 분석 수행" 메시지만 있음
⚠️ **시간축 설명 중복**: 프롬프트에서 시간축 정의가 3번 반복됨 (REQUIREMENTS, OUTPUT_REQUIREMENTS, 예시)
⚠️ **예제 부재**: 구체적인 조치 예시는 있으나 전체 JSON 출력 샘플 없음
⚠️ **Implementation Considerations 모호**: "2-3 bullet points" 요구하나 구체적 내용 불명확
⚠️ **Fallback 전략**: `_generate_fallback_strategy`가 너무 일반적 (예: "물리적 방어 시설 설치")

#### 2.3 토큰 사용량 추정

- **프롬프트 토큰**: 약 1,400-1,700 토큰
- **입력 데이터 토큰**: 약 900-1,400 토큰 (영향 분석 요약 + 건물 권장사항 + 추가 데이터)
- **예상 출력 토큰**: JSON 구조 + 조치 목록 → 약 800-1,200 토큰
- **총 예상 (5개 병렬)**: 약 15,500-21,500 토큰

### 3. 개선 방안

#### 3.1 구조적 개선

**현재 문제**: 시간축 정의가 프롬프트 여러 곳에서 반복됨

**개선안**: TIMELINE_DEFINITIONS 섹션으로 통합
```markdown
<TIMELINE_DEFINITIONS>
단기/중기/장기 조치는 다음 기준으로 구분하세요:

**1. 단기 (2026년, 향후 1년)**
   - 기준: 즉시 실행 가능, 현재 예산 내 처리 가능
   - 예산 범위: 사업장당 1억원 이하
   - 목표: 즉각적 리스크 완화, 긴급 취약점 보강
   - 예시: 배수 펌프 설치, 비상 대응 매뉴얼, 모니터링 시스템

**2. 중기 (2026-2030년, 5년 계획)**
   - 기준: 자본 투자 필요, 연도별 단계적 실행
   - 예산 범위: 사업장당 5-10억원
   - 목표: 구조적 개선, 인프라 업그레이드
   - 예시: 방수벽 3m 증축, 냉각 시스템 교체, 건물 내진 보강
   - **연도별 계획 필수**: "2027년: X, 2028년: Y" 형식으로 작성

**3. 장기 (2020-2050년대, 10년 단위)**
   - 기준: 전략적 의사결정, 대규모 투자 또는 사업 재편
   - 예산 범위: 사업장당 10억원 이상 또는 사업장 재배치
   - 목표: 시스템 전환, 포트폴리오 재구성
   - 예시: 고위험 사업장 이전, 기후 중립 설계 적용, 재생에너지 전환
</TIMELINE_DEFINITIONS>
```

**효과**: 프롬프트 중복 제거, 토큰 10-15% 절감

#### 3.2 컨텍스트 보강

**현재 문제**: 건물 데이터가 없을 때 대응이 불명확

**개선안**: Building Data 활용 가이드 추가
```markdown
<BUILDING_DATA_INSIGHTS>
{building_mitigation_guide가 있는 경우:}
**건물 특성 기반 우선순위 조정**:
- B/C등급 건물: 구조 보강을 단기→중기로 상향 조정
- 취약점이 3개 이상인 사업장: 우선순위 "매우 높음" 설정 권장
- 복원력 요소가 있는 사업장: 기존 강점 활용 전략 포함

{building_mitigation_guide가 없는 경우:}
⚠️ **건물 특성 데이터가 없으므로, 표준 산업 기준을 적용합니다**:
- 모든 사업장에 대해 보수적 접근 (worst-case 가정)
- 구조 보강을 중기 조치에 기본 포함
- **정밀 조사 및 건물 평가를 단기 조치에 추가** (예: "건물 구조 안전 진단 실시")
</BUILDING_DATA_INSIGHTS>
```

**효과**: 건물 데이터 누락 시에도 합리적인 전략 제시

#### 3.3 출력 형식 개선

**현재 문제**: 출력 예제가 없어 품질 편차 발생 가능

**개선안**: 프롬프트에 Full JSON 예제 추가
```markdown
<OUTPUT_EXAMPLE>
{
  "short_term": [
    "침수 취약 지역 배수 펌프 3대 설치 (용량: 500m³/h, 예산: 5천만원)",
    "비상 대응 매뉴얼 업데이트 및 분기별 훈련 실시 (예산: 1천만원)",
    "실시간 수위 모니터링 시스템 구축 (IoT 센서 10개, 예산: 3천만원)"
  ],
  "mid_term": [
    "2027년: 데이터센터 방수벽 2m→4m 증축 (예산: 8억원)",
    "2028-2029년: 지하 전기실 방수 처리 및 배수 시스템 업그레이드 (예산: 5억원)",
    "2030년: 침수 취약 설비 1층→2층 이전 (예산: 3억원)"
  ],
  "long_term": [
    "2030년대: 침수 위험 높은 A사업장 재배치 검토 및 부지 매각 (예산: 50억원)",
    "2040년대: 신규 사업장에 기후 중립 설계 기준 적용 (방수 6m, 태양광 100%)",
    "2050년대: 포트폴리오 전체 Net-Zero 달성"
  ],
  "priority": "매우 높음",
  "priority_justification": "P1 리스크로 AAL 18.2%는 연평균 약 120억원의 재무 노출을 의미하며, B등급 건물 3개 사업장의 구조적 취약성으로 인해 즉각적 대응이 필요합니다.",
  "estimated_cost": "단기: 9천만원, 중기: 16억원, 장기: 50억원, 총: 66.9억원",
  "expected_benefit": "AAL 18.2% → 12.5% (-5.7%p 감소), 연평균 38억원 손실 저감, ROI: 5.7년",
  "implementation_considerations": "• 단기 조치는 2026년 2분기 내 완료 목표\n• 중기 투자는 2027년 예산 편성 시 반영 필요\n• 장기 재배치는 부지 가치 평가 후 2028년 결정"
}
</OUTPUT_EXAMPLE>
```

**효과**: 일관된 출력 품질, 정량화 수준 향상

#### 3.4 예제 및 가이드 추가

**개선안**: 비용-효과 분석 가이드 추가
```markdown
<COST_BENEFIT_ANALYSIS_GUIDE>
**비용 산정 방법**:
- 단기: 사업장당 평균 1억원 이하
- 중기: 사업장당 평균 5-10억원
- 장기: 사업장당 평균 10억원 이상

**기대 효과 산정 방법**:
1. AAL 감소율 추정:
   - 단기 조치: AAL -1~2%p
   - 중기 조치: AAL -3~5%p
   - 장기 조치: AAL -5~10%p

2. 손실 저감액 계산:
   - AAL 감소율 × 포트폴리오 자산 가치
   - 예: AAL 5%p 감소 × 1조원 = 500억원

3. ROI 계산:
   - ROI (년) = 총 투자 비용 / 연평균 손실 저감액
   - 예: 67억원 / 38억원 = 1.76년 → **약 2년**

**권장 ROI 기준**:
- 매우 높음: ROI < 3년
- 높음: ROI 3-5년
- 중간: ROI 5-10년
- 낮음: ROI > 10년
</COST_BENEFIT_ANALYSIS_GUIDE>
```

**효과**: 비용-효과 산정 일관성 향상

### 4. 개선 우선순위

#### Critical (필수)
- [x] 건물 데이터 누락 시 표준 대응 전략 제공
- [ ] 출력 예제 추가

#### High (높음)
- [ ] Timeline 정의 중복 제거 (토큰 절감)
- [ ] ROI/비용 산정 가이드 추가
- [ ] Fallback 전략 개선

#### Medium (중간)
- [ ] Implementation Considerations 구체화
- [ ] 우선순위 매트릭스 추가 (건물 등급 × AAL)

#### Low (낮음)
- [ ] 토큰 효율화

---

## Node 3: Strategy Section

### 1. 프롬프트 위치 및 구조

**메서드명**: `_generate_executive_summary` (line 341-506)
**호출 시점**: Step 3/6 - Executive Summary 생성 (LLM)
**프롬프트 구조**:
- `<ROLE>`: 역할 정의 ("ELITE TCFD report writer")
- `<CRITICAL_SUMMARY_REQUIREMENTS>`: 4개 핵심 요약 요구사항
- `<INPUT_DATA>`: 포트폴리오 개요, Top 3 리스크, 시나리오 요약, 대응 전략 개요
- `<OUTPUT_REQUIREMENTS>`: 구조 (4단계), 길이 (400-600 words), 톤, 포맷
- `<QUALITY_CHECKLIST>`: 8개 항목 검증

### 2. 현재 프롬프트 분석

#### 2.1 강점

✅ **이해관계자 중심**: "institutional investors" 등 명확한 청중 타겟팅
✅ **4단계 구조**:
  - Opening Statement (포트폴리오 전체 AAL)
  - Key Findings (Top 리스크 + 시나리오 분석)
  - Strategic Response (대응 전략 개요)
  - Stakeholder Message (이해관계자 메시지)

✅ **템플릿 톤 활용**: Node 1의 tone (formality, audience, voice) 반영
✅ **정량적 요구**: AAL, 사업장 수, 비용 등 구체적 수치 인용 요구
✅ **적절한 길이**: 400-600 words (약 2-3 페이지)

#### 2.2 약점

⚠️ **Top 3 한정**: Top 5 리스크가 있음에도 Top 3만 요약 (P4, P5 정보 손실)
⚠️ **시나리오 요약 간소화**: 4개 시나리오를 단순 나열만 함 (비교 분석 부족)
⚠️ **투자 계획 정보 부족**: "Investment commitment and expected ROI" 요구하나 INPUT_DATA에 구체적 정보 없음
⚠️ **JSON 파싱 시도**: Executive Summary는 텍스트인데 JSON 파싱 시도하여 혼란
⚠️ **Fallback 품질**: `_generate_fallback_executive_summary`가 너무 간단함

#### 2.3 토큰 사용량 추정

- **프롬프트 토큰**: 약 1,000-1,300 토큰
- **입력 데이터 토큰**: 약 400-600 토큰
- **예상 출력 토큰**: 400-600 words → 약 800-1,200 토큰
- **총 예상**: 약 2,200-3,100 토큰

### 3. 개선 방안

#### 3.1 구조적 개선

**현재 문제**: 4단계 구조는 명확하나 각 단계별 단어 수 가이드가 없음

**개선안**: 단계별 길이 가이드 추가
```markdown
<EXECUTIVE_SUMMARY_STRUCTURE>
다음 4단계 구조로 작성하되, 각 단계별 단어 수 가이드를 준수하세요:

**1. Opening Statement** (50-80 words):
   - 전체 포트폴리오 AAL: {total_portfolio_aal:.1f}%
   - 위험 수준 평가: "우려 수준" / "관리 가능" / "즉각 대응 필요"
   - 예시: "우리 {len(sites_data)}개 사업장 포트폴리오의 기후 물리적 리스크 AAL은 총 {total_portfolio_aal:.1f}%입니다. 이는 연평균 약 X억원의 재무 노출을 의미하며, 즉각적인 대응 전략이 필요합니다."

**2. Key Findings** (150-200 words, 4-5 bullet points):
   - **Top 5 리스크** (AAL 값 포함) ← ✅ Top 3 → Top 5로 확장
   - 시나리오 분석 핵심: 최선(SSP1-2.6) vs 최악(SSP5-8.5) AAL 차이
   - 재무 영향 범위: KRW X억원 ~ Y억원
   - 가장 취약한 사업장 및 운영 중단 리스크

**3. Strategic Response** (120-150 words):
   - 단기(2026) / 중기(2026-2030) / 장기(2020-2050년대) 전략 개요
   - **총 투자 규모**: KRW Z억원 ← ✅ 추가
   - **기대 효과**: AAL 감소율, 손실 저감액 ← ✅ 추가
   - 실행 타임라인

**4. Stakeholder Message** (80-100 words):
   - 신뢰 메시지: "우리는 준비되어 있습니다"
   - TCFD 투명성 및 지속적 개선 약속
   - 장기 비전: 2050 Net-Zero 등
</EXECUTIVE_SUMMARY_STRUCTURE>
```

**효과**: 균형잡힌 구조, 길이 일관성

#### 3.2 컨텍스트 보강

**현재 문제**: INPUT_DATA에 투자 계획 정보가 부족함

**개선안**: Enhanced INPUT_DATA
```markdown
<ENHANCED_INPUT_DATA>
**Portfolio Overview**:
- Total Sites: {len(sites_data)}
- Total Portfolio AAL (Top 5): {total_portfolio_aal:.1f}%
- 재무 노출 추정: 연평균 약 X억원 (AAL 기반 산출)
- 최대 리스크 사업장: {max_aal_site} (AAL {max_aal:.1f}%)

**Top 5 Physical Risks** (확장):  ← ✅ Top 3 → Top 5
{chr(10).join([
  f"- P{i}. {risk['risk_name_kr']}: AAL {risk['total_aal']:.1f}% ({risk['num_affected_sites']}개 사업장)"
  for i, risk in enumerate(top_5_risks, 1)
])}

**Scenario Analysis Comparative Summary**:  ← ✅ 비교 분석 추가
- 최선 시나리오 (SSP1-2.6): AAL {aal_best:.1f}% (2100년)
- 최악 시나리오 (SSP5-8.5): AAL {aal_worst:.1f}% (2100년)
- **시나리오 민감도**: 최대 {aal_worst - aal_best:.1f}%p 차이
- 중간 시나리오 (SSP2-4.5): AAL {aal_mid:.1f}% (가장 현실적)

**Mitigation Strategy Overview**:  ← ✅ 투자 계획 정보 추가
- Number of Strategies: {len(mitigation_strategies)}
- 우선순위 "매우 높음": {num_very_high} 건
- **총 투자 규모**: 단기 X억원 + 중기 Y억원 + 장기 Z억원 = **총 N억원**
- **기대 효과**: AAL {total_portfolio_aal:.1f}% → {target_aal:.1f}% (**-{reduction:.1f}%p**)
- Timeline: 2026년 시작 → 2050년 Net-Zero 목표
</ENHANCED_INPUT_DATA>
```

**효과**: LLM이 투자 계획 정보를 Executive Summary에 포함 가능

#### 3.3 출력 형식 개선

**현재 문제**: 출력 예제가 없음

**개선안**: 프롬프트에 Full 예제 추가
```markdown
<OUTPUT_EXAMPLE>
## Executive Summary

우리 8개 사업장 포트폴리오의 기후 물리적 리스크 AAL은 총 **65.3%**입니다. 이는 연평균 약 **430억원**의 재무 노출을 의미하며, **즉각적인 대응 전략이 필요**합니다. 특히 하천 홍수(AAL 18.2%)와 태풍(AAL 15.7%)이 주요 리스크로 식별되었습니다.

### 주요 발견 사항

- **P1. 하천 홍수**: AAL 18.2% (연평균 120억원 노출), 5개 사업장 영향
- **P2. 태풍**: AAL 15.7% (연평균 103억원 노출), 4개 사업장 영향
- **P3. 도시 홍수**: AAL 12.4% (연평균 82억원 노출), 6개 사업장 영향
- **P4. 극심한 고온**: AAL 10.5% (연평균 69억원 노출), 8개 사업장 영향
- **P5. 해수면 상승**: AAL 8.5% (연평균 56억원 노출), 2개 사업장 영향
- **시나리오 분석**: SSP1-2.6(최선) AAL 45.0% vs SSP5-8.5(최악) AAL 85.3%, **최대 40.3%p 차이**
- **재무 영향 범위**: 연평균 300억원(최선) ~ 560억원(최악)
- **최대 취약 사업장**: 서울 데이터센터 (AAL 28.5%), 침수 시 최대 3일 운영 중단 리스크

### 대응 전략

우리는 Top 5 리스크에 대해 **단기(2026년), 중기(2026-2030년), 장기(2020-2050년대)** 3단계 대응 전략을 수립했습니다. 총 투자 규모는 **약 330억원** (단기 4억원, 중기 80억원, 장기 246억원)이며, AAL을 **65.3% → 45.0%로 20.3%p 감소**시켜 연평균 약 **133억원의 손실을 저감**할 것으로 기대됩니다.

단기 조치는 2026년 2분기 내 완료를 목표로 하며, 우선순위가 "매우 높음"인 3개 리스크에 집중합니다. 중기 투자는 2027년부터 연도별로 단계적 실행하며, 장기적으로는 2050년 Net-Zero 포트폴리오 달성을 목표로 합니다.

### 이해관계자 메시지

우리는 TCFD 권고안에 따라 기후 리스크를 체계적으로 관리하고 있으며, **즉각적 대응과 장기 투자를 균형있게 실행**할 준비가 되어 있습니다. 분기별 AAL 모니터링과 연 1회 시나리오 재평가를 통해 지속적으로 전략을 개선하며, 투명한 공시를 통해 이해관계자 신뢰를 구축하겠습니다.
</OUTPUT_EXAMPLE>
```

**효과**: 일관된 품질, LLM 추론 부담 감소

#### 3.4 JSON 파싱 로직 제거

**현재 문제**: Executive Summary는 텍스트인데 JSON 파싱 시도

**개선안**: 텍스트 응답만 처리
```python
# Before
try:
    response = await self.llm.ainvoke(prompt)
    if response.strip().startswith("{"):
        parsed = json.loads(response)
        return parsed.get("summary", response)
    return response
except:
    ...

# After
response = await self.llm.ainvoke(prompt)
return response.strip()  # JSON 파싱 시도 제거
```

**효과**: 불필요한 파싱 오류 방지

### 4. 개선 우선순위

#### Critical (필수)
- [x] Top 5 리스크로 확장 (현재 Top 3)
- [x] 투자 계획 정보 보강 (INPUT_DATA)

#### High (높음)
- [ ] 시나리오 비교 분석 강화
- [ ] 출력 예제 추가
- [ ] JSON 파싱 로직 제거

#### Medium (중간)
- [ ] Fallback 품질 개선
- [ ] 단계별 길이 가이드 추가

#### Low (낮음)
- [ ] 템플릿 톤 활용 강화

---

## Node 4: Validator

### 1. 프롬프트 위치 및 구조

**메서드명**: Node 4는 **LLM을 사용하지 않음** (규칙 기반 검증)
**호출 시점**: Step 1-4 - 완성도, 일관성, TCFD 원칙, 품질 점수 검증
**검증 방식**:
- `_check_completeness`: 필수 필드 체크 (Python 로직)
- `_check_data_consistency`: 데이터 일관성 체크 (Python 로직)
- `_check_tcfd_principles`: TCFD 7대 원칙 점수화 (Python 로직)
- `_calculate_quality_score`: 품질 점수 산출 (Python 로직)

### 2. 현재 검증 로직 분석

#### 2.1 강점

✅ **LLM 불필요**: 규칙 기반 검증으로 빠르고 비용 효율적
✅ **TCFD 7대 원칙 커버**: Relevant, Specific, Clear, Consistent, Comparable, Reliable, Timely
✅ **Critical vs Warning 구분**: 심각도 레벨로 이슈 분류
✅ **품질 점수 산출**: 0-100점 정량화

#### 2.2 약점

⚠️ **검증 항목 제한적**:
  - 필드 존재 여부만 체크 (내용 품질 검증 없음)
  - Executive Summary 길이만 체크 (200자 미만 경고)
  - AAL 범위만 체크 (0-100%)

⚠️ **TCFD 원칙 점수 단순**:
  - Relevant: Executive Summary 있으면 100점, 없으면 50점 (이분법)
  - 실제 내용 품질 평가 없음

⚠️ **LLM 활용 기회 놓침**:
  - 내용 일관성 검증 (예: Executive Summary와 세부 분석 일치 여부)
  - 논리적 흐름 검증
  - 전문성 평가

#### 2.3 토큰 사용량

- **없음** (LLM 미사용)

### 3. 개선 방안

#### 3.1 구조적 개선 - LLM 기반 내용 검증 추가

**개선안**: LLM 기반 내용 일관성 검증 (선택적)
```python
async def _validate_content_with_llm(self, strategy_section: Dict) -> List[Dict]:
    """
    LLM 기반 내용 품질 검증 (선택적)

    검증 항목:
    1. Executive Summary와 세부 분석 일관성
    2. AAL 값 인용 정확성
    3. 논리적 흐름 (리스크 → 영향 → 대응)
    4. TCFD 7대 원칙 실제 적용도
    """

    prompt = f"""
<ROLE>
You are a TCFD report quality auditor.
Your task is to validate the content quality of the Strategy section.
</ROLE>

<VALIDATION_CRITERIA>
1. **Consistency** (일관성):
   - Executive Summary의 AAL 값이 세부 분석과 일치하는가?
   - 리스크 순위(P1-P5)가 모든 섹션에서 일관되게 유지되는가?

2. **Accuracy** (정확성):
   - 인용된 수치(AAL, 사업장 수, 비용)가 INPUT_DATA와 일치하는가?

3. **Logical Flow** (논리적 흐름):
   - 리스크 식별 → 영향 분석 → 대응 전략 흐름이 자연스러운가?

4. **TCFD Principles** (TCFD 원칙):
   - Relevant: 투자자 관점에서 유용한 정보인가?
   - Specific: 구체적인 수치와 사례를 포함하는가?
   - Clear: 전문 용어 설명이 충분한가?
</VALIDATION_CRITERIA>

<INPUT_DATA>
{json.dumps(strategy_section, ensure_ascii=False, indent=2)}
</INPUT_DATA>

<OUTPUT_FORMAT>
JSON 배열로 이슈를 반환하세요:
[
  {{
    "severity": "critical" or "warning" or "info",
    "type": "consistency" or "accuracy" or "logical_flow" or "tcfd_principle",
    "field": "필드명",
    "message": "구체적 이슈 설명",
    "suggestion": "개선 제안"
  }}
]

이슈가 없으면 빈 배열 []을 반환하세요.
</OUTPUT_FORMAT>
"""

    try:
        response = await self.llm.ainvoke(prompt)
        issues = json.loads(response)
        return issues
    except:
        return []  # LLM 실패 시 규칙 기반 검증만 사용
```

**효과**: 실제 내용 품질 검증 가능

#### 3.2 컨텍스트 보강 - 검증 기준 명확화

**개선안**: TCFD 원칙 점수 산출 로직 개선
```python
def _check_tcfd_principles(self, strategy_section: Dict) -> Dict[str, float]:
    """
    TCFD 7대 원칙 검증 (개선 버전)
    """
    scores = {}

    # 1. Relevant (관련성): Executive Summary 존재 + 길이 + Top 5 언급
    exec_summary = self._get_executive_summary(strategy_section)
    score = 0.0
    if exec_summary:
        score += 40.0  # 존재
        if len(exec_summary) >= 400:
            score += 30.0  # 충분한 길이
        if all(f"P{i}" in exec_summary for i in range(1, 6)):
            score += 30.0  # Top 5 모두 언급
    scores["Relevant"] = score

    # 2. Specific (구체성): AAL 값, KRW 금액, 사업장 수 인용 여부
    score = 0.0
    if "AAL" in exec_summary:
        score += 30.0
    if "억원" in exec_summary or "billion" in exec_summary:
        score += 40.0
    if "사업장" in exec_summary or "site" in exec_summary:
        score += 30.0
    scores["Specific"] = score

    # 3. Clear (명확성): 섹션 구조 + 블록 수
    score = 0.0
    blocks = strategy_section.get("blocks", [])
    if len(blocks) >= 5:  # Executive Summary + Heatmap + P1-P5
        score += 50.0
    if len(blocks) >= 10:
        score += 50.0
    scores["Clear"] = score

    # ... (나머지 원칙도 유사하게 개선)

    return scores
```

**효과**: 더 세분화된 점수, 개선 방향 명확

#### 3.3 출력 형식 개선 - 상세 검증 리포트

**개선안**: 검증 리포트 마크다운 생성
```python
def _generate_validation_report(self, validation_result: Dict) -> str:
    """
    상세 검증 리포트 생성
    """
    report = []

    report.append("## TCFD 보고서 품질 검증 리포트\n")
    report.append(f"**품질 점수**: {validation_result['quality_score']:.1f}/100\n")
    report.append(f"**검증 상태**: {'✅ 통과' if validation_result['is_valid'] else '⚠️ 재검토 필요'}\n\n")

    report.append("### TCFD 7대 원칙 점수\n")
    for principle, score in validation_result['principle_scores'].items():
        icon = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
        report.append(f"- {icon} **{principle}**: {score:.1f}/100\n")

    if validation_result['issues']:
        report.append("\n### 발견된 이슈\n")
        critical = [i for i in validation_result['issues'] if i['severity'] == 'critical']
        warning = [i for i in validation_result['issues'] if i['severity'] == 'warning']

        if critical:
            report.append(f"\n**Critical ({len(critical)}건)**:\n")
            for issue in critical[:5]:
                report.append(f"- ❌ [{issue['field']}] {issue['message']}\n")

        if warning:
            report.append(f"\n**Warning ({len(warning)}건)**:\n")
            for issue in warning[:5]:
                report.append(f"- ⚠️ [{issue['field']}] {issue['message']}\n")

    report.append("\n### 개선 권장사항\n")
    report.append(validation_result['feedback'])

    return "".join(report)
```

**효과**: 사용자 친화적인 검증 결과

#### 3.4 예제 및 가이드 추가

- 없음 (규칙 기반 검증)

### 4. 개선 우선순위

#### Critical (필수)
- [ ] LLM 기반 내용 검증 추가 (일관성, 정확성 체크)

#### High (높음)
- [ ] TCFD 원칙 점수 산출 로직 개선 (이분법 → 다단계)
- [ ] 검증 리포트 상세화

#### Medium (중간)
- [ ] 추가 검증 항목 확대 (예: 참조 무결성)

#### Low (낮음)
- [ ] 검증 임계값 조정 (200자 → 400자 등)

---

## Node 5: Composer

### 1. 프롬프트 위치 및 구조

**메서드명**: Node 5는 **LLM을 거의 사용하지 않음** (하드코딩 + 데이터 조립)
**호출 시점**:
- Governance, Risk Management, Appendix 섹션은 완전 하드코딩
- Metrics 섹션은 템플릿 + LineChart 생성 (LLM 없음)
**LLM 사용 여부**: 없음 (Node 3의 Executive Summary 재사용)

### 2. 현재 구성 로직 분석

#### 2.1 강점

✅ **빠른 실행**: LLM 호출 없이 즉시 조립
✅ **일관된 품질**: 하드코딩으로 표준화된 섹션 생성
✅ **구조 명확**: TCFD 4대 섹션 (Governance, Strategy, Risk Mgmt, Metrics) 완비
✅ **차트 생성**: LineChartBlock으로 시각화 제공

#### 2.2 약점

⚠️ **유연성 부족**: 회사별 맞춤화 불가능
  - Governance 섹션: "이사회", "CSO" 등 모든 회사에 동일한 내용
  - Risk Management: 프로세스 설명이 일반적

⚠️ **Node 2-C 활용 제한적**: Top 3 대응 전략만 Risk Management에 삽입 (Top 4-5 누락)
⚠️ **LLM 활용 기회 놓침**:
  - Governance를 회사 정보 기반으로 맞춤 생성 가능
  - Risk Management를 실제 프로세스 데이터 기반으로 생성 가능

⚠️ **Metrics 섹션 단순**: AAL 추이 차트만 있고 다른 지표(예: 탄소 배출) 없음

#### 2.3 토큰 사용량

- **없음** (LLM 미사용)

### 3. 개선 방안

#### 3.1 구조적 개선 - LLM 기반 맞춤화 옵션 추가

**개선안**: Governance 섹션 LLM 맞춤 생성 (선택적)
```python
async def _create_governance_section_with_llm(
    self,
    company_context: Optional[Dict] = None
) -> Dict:
    """
    LLM 기반 Governance 섹션 맞춤 생성 (선택적)

    Args:
        company_context: 회사 정보 (이사회 구성, ESG 위원회, CSO 유무 등)

    Returns:
        Dict: Governance 섹션
    """

    if not company_context or not self.llm_client:
        # Fallback: 하드코딩 버전 사용
        return self._create_governance_section()

    prompt = f"""
<ROLE>
You are a TCFD governance section writer.
Your task is to create a customized Governance section based on the company's actual governance structure.
</ROLE>

<REQUIREMENTS>
Generate a Governance section with 2 subsections:
1. **1.1 이사회의 감독**: 이사회가 기후 리스크를 어떻게 감독하는지
2. **1.2 경영진의 역할**: 경영진의 기후 리스크 관리 역할

Each subsection should be 150-250 words in Korean.
</REQUIREMENTS>

<COMPANY_CONTEXT>
{json.dumps(company_context, ensure_ascii=False, indent=2)}
</COMPANY_CONTEXT>

<OUTPUT_FORMAT>
JSON object:
{{
  "board_oversight": "1.1 이사회의 감독 내용 (Markdown)",
  "management_role": "1.2 경영진의 역할 내용 (Markdown)"
}}
</OUTPUT_FORMAT>
"""

    try:
        response = await self.llm_client.ainvoke(prompt)
        data = json.loads(response)

        return {
            "section_id": "governance",
            "title": "1. Governance",
            "page_start": 3,
            "page_end": 4,
            "blocks": [
                {
                    "type": "text",
                    "subheading": "1.1 이사회의 감독",
                    "content": data["board_oversight"]
                },
                {
                    "type": "text",
                    "subheading": "1.2 경영진의 역할",
                    "content": data["management_role"]
                }
            ]
        }
    except:
        # LLM 실패 시 하드코딩 버전 사용
        return self._create_governance_section()
```

**효과**: 회사별 맞춤 Governance 섹션 생성 가능

#### 3.2 컨텍스트 보강 - Risk Management 강화

**개선안**: Top 5 전체 활용 + 상세 요약
```python
def _create_risk_management_section(
    self,
    mitigation_strategies: List[Dict],
    scenario_analysis: Optional[Dict] = None,
    impact_analyses: Optional[List[Dict]] = None
) -> Dict:
    """
    Risk Management 섹션 생성 (개선 버전)

    Args:
        mitigation_strategies: Node 2-C 출력 (Top 5 전체 활용)
        scenario_analysis: Node 2-A 출력 (선택적)
        impact_analyses: Node 2-B 출력 (선택적)
    """

    blocks = []

    # 3.1 리스크 식별 및 평가 프로세스
    blocks.append({
        "type": "text",
        "subheading": "3.1 리스크 식별 및 평가 프로세스",
        "content": self._generate_risk_process_text(scenario_analysis, impact_analyses)
    })

    # 3.2 전사적 리스크 관리 체계(ERM) 통합 (기존 유지)
    blocks.append({...})

    # 3.3 주요 대응 전략 요약 (Top 5 전체 포함, 개선)
    mitigation_summary = self._generate_detailed_mitigation_summary(mitigation_strategies)
    blocks.append({
        "type": "text",
        "subheading": "3.3 주요 대응 전략 요약",
        "content": mitigation_summary
    })

    return {
        "section_id": "risk_management",
        "title": "3. Risk Management",
        "page_start": 13,
        "page_end": 15,
        "blocks": blocks
    }

def _generate_detailed_mitigation_summary(self, strategies: List[Dict]) -> str:
    """
    Top 5 대응 전략 상세 요약 (개선)
    """
    parts = ["우리는 다음과 같은 기후 리스크 대응 전략을 수립하고 있습니다:\n"]

    for i, strategy in enumerate(strategies, 1):  # Top 5 전체
        risk_type = strategy.get('risk_type', f'risk_{i}')
        risk_name_kr = self.risk_name_mapping.get(risk_type, risk_type)
        priority = strategy.get('priority', '중간')
        short_term = strategy.get('short_term', [])
        estimated_cost = strategy.get('estimated_cost', '산정 중')

        parts.append(f"\n**P{i}. {risk_name_kr}** (우선순위: {priority})")
        parts.append(f"- 예상 비용: {estimated_cost}")

        if short_term:
            parts.append(f"- 단기 조치: {short_term[0]}")  # 첫 번째만
        else:
            parts.append("- 대응 전략 수립 중")

    parts.append("\n\n상세한 대응 전략은 Strategy 섹션(2.3)에서 확인하실 수 있습니다.")
    return "\n".join(parts)
```

**효과**: Top 5 전체 정보 활용, 일관성 향상

#### 3.3 출력 형식 개선 - Metrics 섹션 확장

**개선안**: 리스크 분포 테이블 추가
```python
def _create_metrics_section(
    self,
    scenarios: Dict,
    impact_analyses: Optional[List[Dict]] = None
) -> Dict:
    """
    Metrics & Targets 섹션 생성 (확장 버전)
    """
    blocks = []

    # 4.1 AAL 지표 (기존 유지)
    blocks.append({...})

    # 4.2 AAL 추이 차트 (기존 유지)
    blocks.append(self._create_aal_trend_chart(scenarios))

    # 4.3 리스크별 AAL 분포 (신규 추가)
    if impact_analyses:
        blocks.append(self._create_risk_breakdown_table(impact_analyses))

    # 4.4 목표 및 이행 계획 (기존 유지)
    blocks.append({...})

    return {
        "section_id": "metrics_targets",
        "title": "4. Metrics and Targets",
        "page_start": 16,
        "page_end": 18,
        "blocks": blocks
    }

def _create_risk_breakdown_table(self, impact_analyses: List[Dict]) -> Dict:
    """
    리스크별 AAL 분포 테이블 생성 (신규)
    """
    headers = ["순위", "리스크", "AAL", "영향 사업장", "비율"]
    rows = []

    total_aal = sum([ia.get("total_aal", 0.0) for ia in impact_analyses])

    for i, ia in enumerate(impact_analyses, 1):
        risk_type = ia.get("risk_type", "unknown")
        risk_name_kr = self.risk_name_mapping.get(risk_type, risk_type)
        aal = ia.get("total_aal", 0.0)
        num_affected = ia.get("num_affected_sites", 0)
        ratio = (aal / total_aal * 100) if total_aal > 0 else 0

        rows.append({
            "cells": [
                f"P{i}",
                risk_name_kr,
                f"{aal:.1f}%",
                f"{num_affected}개",
                f"{ratio:.1f}%"
            ]
        })

    return {
        "type": "table",
        "title": "리스크별 AAL 분포",
        "data": {
            "headers": headers,
            "rows": rows
        }
    }
```

**효과**: Metrics 섹션 풍부화

#### 3.4 예제 및 가이드 추가

**개선안**: 회사 컨텍스트 예제
```python
# 회사 컨텍스트 예제 (Governance 맞춤화용)
company_context_example = {
    "board": {
        "has_esg_committee": True,
        "committee_name": "ESG위원회",
        "review_frequency": "분기별",
        "climate_expertise": True
    },
    "management": {
        "has_cso": True,
        "cso_title": "최고지속가능경영책임자(CSO)",
        "reports_to": "CEO",
        "team_size": 5
    }
}
```

**효과**: 사용자가 회사 정보 제공 시 맞춤 생성 가능

### 4. 개선 우선순위

#### Critical (필수)
- [x] Risk Management 섹션에서 Top 5 전체 활용

#### High (높음)
- [ ] Governance 섹션 LLM 맞춤화 옵션 추가
- [ ] Metrics 섹션에 리스크 분포 테이블 추가

#### Medium (중간)
- [ ] 회사 컨텍스트 입력 구조화

#### Low (낮음)
- [ ] Appendix 섹션 동적 생성

---

## Node 6: Finalizer

### 1. 프롬프트 위치 및 구조

**메서드명**: Node 6는 **LLM을 사용하지 않음** (DB 저장 + 메타데이터 생성)
**호출 시점**:
- Step 1: JSONB로 DB 저장
- Step 2: 사업장-보고서 관계 저장
- Step 3: 다운로드 URL 생성
**LLM 사용 여부**: 없음

### 2. 현재 Finalizer 로직 분석

#### 2.1 강점

✅ **간결함**: LLM 없이 빠른 저장
✅ **JSONB 활용**: PostgreSQL JSONB로 유연한 스키마
✅ **메타데이터 생성**: 보고서 요약 정보 제공 (`get_report_summary`)
✅ **검증 함수**: `validate_report`로 DB 저장 전 검증

#### 2.2 약점

⚠️ **실제 DB 저장 미구현**: TODO 주석만 있고 Mock ID 반환
⚠️ **PDF 생성 없음**: 프론트엔드에 의존 (백엔드에서 생성 가능성 검토 필요)
⚠️ **LLM 활용 기회 놓침**:
  - 보고서 품질 최종 검증 (Node 4와 중복이나 더 엄격)
  - 메타데이터 자동 생성 (예: 보고서 요약문)

#### 2.3 토큰 사용량

- **없음** (LLM 미사용)

### 3. 개선 방안

#### 3.1 구조적 개선 - LLM 기반 최종 품질 검증 (선택적)

**개선안**: 최종 품질 검증 추가
```python
async def _final_quality_check_with_llm(self, report: Dict) -> Dict:
    """
    LLM 기반 최종 품질 검증 (선택적, Node 4보다 엄격)

    검증 항목:
    1. 보고서 전체 일관성 (섹션 간 내용 일치)
    2. 투자자 관점 유용성
    3. TCFD 가이드라인 준수

    Returns:
        Dict: {
            "is_acceptable": bool,
            "quality_grade": "A" / "B" / "C",
            "final_recommendations": List[str]
        }
    """

    if not self.llm:
        return {
            "is_acceptable": True,
            "quality_grade": "B",
            "final_recommendations": []
        }

    # 보고서 요약 추출 (토큰 절약)
    summary = {
        "meta": report.get("meta", {}),
        "executive_summary": self._extract_executive_summary(report),
        "section_titles": [s.get("title") for s in report.get("sections", [])],
        "total_blocks": sum([len(s.get("blocks", [])) for s in report.get("sections", [])])
    }

    prompt = f"""
<ROLE>
You are a senior TCFD auditor performing final quality assurance before report publication.
</ROLE>

<CRITICAL_CHECKS>
1. **Investor Perspective**: 이 보고서가 기관 투자자에게 실질적으로 유용한가?
2. **TCFD Compliance**: TCFD 권고안의 11개 권장 공시 항목을 충족하는가?
3. **Completeness**: Governance, Strategy, Risk Mgmt, Metrics 모두 완비되었는가?
4. **Actionability**: 대응 전략이 실행 가능하고 구체적인가?
</CRITICAL_CHECKS>

<REPORT_SUMMARY>
{json.dumps(summary, ensure_ascii=False, indent=2)}
</REPORT_SUMMARY>

<OUTPUT_FORMAT>
JSON object:
{{
  "is_acceptable": true or false,
  "quality_grade": "A" or "B" or "C",
  "final_recommendations": [
    "개선 권장사항 1",
    "개선 권장사항 2"
  ],
  "strengths": ["강점 1", "강점 2"],
  "weaknesses": ["약점 1", "약점 2"]
}}

- A등급: TCFD 우수 사례 수준
- B등급: TCFD 요구사항 충족
- C등급: 개선 필요
</OUTPUT_FORMAT>
"""

    try:
        response = await self.llm.ainvoke(prompt)
        result = json.loads(response)
        return result
    except:
        return {
            "is_acceptable": True,
            "quality_grade": "B",
            "final_recommendations": []
        }
```

**효과**: 보고서 품질 최종 확인

#### 3.2 컨텍스트 보강 - 메타데이터 자동 생성

**개선안**: LLM 기반 보고서 요약문 생성
```python
async def _generate_report_summary_with_llm(self, report: Dict) -> str:
    """
    LLM 기반 보고서 요약문 자동 생성 (메타데이터용)

    Returns:
        str: 1-2 문장 요약문
    """

    if not self.llm:
        return "TCFD 보고서"

    exec_summary = self._extract_executive_summary(report)

    prompt = f"""
<ROLE>
You are a report summarizer.
Generate a 1-2 sentence summary of this TCFD report for metadata.
</ROLE>

<EXECUTIVE_SUMMARY>
{exec_summary[:500]}...
</EXECUTIVE_SUMMARY>

<OUTPUT_FORMAT>
Plain text (1-2 sentences, Korean, max 100 characters):
"이 보고서는 X개 사업장의 기후 물리적 리스크 AAL Y%를 분석하고, Top 5 리스크에 대한 대응 전략을 제시합니다."
</OUTPUT_FORMAT>
"""

    try:
        summary = await self.llm.ainvoke(prompt)
        return summary.strip()[:100]  # 최대 100자
    except:
        return "TCFD 보고서"
```

**효과**: 자동화된 메타데이터 생성

#### 3.3 출력 형식 개선 - DB 저장 로직 구현

**개선안**: 실제 DB 저장 구현
```python
async def _save_to_db(self, report: Dict, user_id: int) -> int:
    """
    DB 저장 (실제 구현 예시)
    """

    if self.db is None:
        print("  ⚠️  DB 세션이 없어 실제 저장을 생략합니다 (테스트 모드)")
        return 123  # Mock ID

    from app.models import TCFDReport
    from sqlalchemy import func

    # LLM 기반 요약문 생성 (선택적)
    summary = await self._generate_report_summary_with_llm(report)

    # DB 레코드 생성
    db_report = TCFDReport(
        user_id=user_id,
        title=report.get("meta", {}).get("title", "TCFD 보고서"),
        summary=summary,  # LLM 생성 요약
        report_type="TCFD",
        content=report,  # JSONB 컬럼
        total_pages=report.get("meta", {}).get("total_pages", 0),
        total_aal=report.get("meta", {}).get("total_aal", 0.0),
        site_count=report.get("meta", {}).get("site_count", 0),
        generated_at=func.now(),
        llm_model=report.get("meta", {}).get("llm_model", "gpt-4o"),
        status="completed"
    )

    self.db.add(db_report)
    await self.db.commit()
    await self.db.refresh(db_report)

    return db_report.id
```

**효과**: 실제 운영 가능

#### 3.4 예제 및 가이드 추가

**개선안**: DB 스키마 예시
```sql
CREATE TABLE tcfd_reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    report_type VARCHAR(50) DEFAULT 'TCFD',
    content JSONB NOT NULL,
    total_pages INTEGER,
    total_aal DECIMAL(5,2),
    site_count INTEGER,
    generated_at TIMESTAMP DEFAULT NOW(),
    llm_model VARCHAR(50),
    status VARCHAR(50) DEFAULT 'completed'
);
```

**효과**: 구현 가이드 제공

### 4. 개선 우선순위

#### Critical (필수)
- [ ] 실제 DB 저장 로직 구현

#### High (높음)
- [ ] LLM 기반 최종 품질 검증 추가
- [ ] 메타데이터 요약문 자동 생성

#### Medium (중간)
- [ ] PDF 생성 백엔드 옵션 검토

#### Low (낮음)
- [ ] 다운로드 URL 서명 (보안)

---

## 종합 요약 및 우선순위별 개선 권장사항

### 전체 워크플로우 프롬프팅 평가

| Node | LLM 사용 | 프롬프트 품질 | 토큰 효율성 | 개선 필요도 |
|------|----------|--------------|-------------|-------------|
| 2-A  | ✅ Yes   | B+           | B           | **High**    |
| 2-B  | ✅ Yes   | A-           | B+          | Medium      |
| 2-C  | ✅ Yes   | A-           | B+          | Medium      |
| 3    | ✅ Yes   | B+           | A-          | **High**    |
| 4    | ❌ No    | N/A (규칙 기반) | A+       | **High** (LLM 추가 권장) |
| 5    | ❌ No    | N/A (하드코딩) | A+        | Medium (LLM 옵션 추가) |
| 6    | ❌ No    | N/A (DB 저장) | A+         | Low         |

**평가 기준**:
- **프롬프트 품질**: 구조, 명확성, TCFD 요구사항 충족도
- **토큰 효율성**: 중복 제거, 간결성
- **개선 필요도**: Critical > High > Medium > Low

---

### Critical 개선사항 (즉시 적용 필요)

#### 1. Node 2-A (Scenario Analysis)
- [x] 출력 형식 명확화: JSON vs Markdown 통일 → **JSON 권장**
- [x] 사업장 수 컨텍스트 명시 (`num_sites` 활용)

#### 2. Node 2-B (Impact Analysis)
- [x] 건물 데이터 누락 시 fallback 전략 강화 → 표준 산업 기준 적용
- [x] 포트폴리오 비율 정보 프롬프트에 명시 (v2.1에서 이미 적용됨!)

#### 3. Node 2-C (Mitigation Strategies)
- [ ] 건물 데이터 없을 때 표준 대응 전략 제공
- [ ] 출력 JSON 예제 추가

#### 4. Node 3 (Strategy Section)
- [x] Top 5 리스크 전체 포함 (현재 Top 3만)
- [x] 투자 계획 정보 INPUT_DATA에 보강

#### 5. Node 4 (Validator)
- [ ] LLM 기반 내용 일관성 검증 추가

#### 6. Node 5 (Composer)
- [x] Risk Management 섹션에서 Top 5 전체 활용

#### 7. Node 6 (Finalizer)
- [ ] 실제 DB 저장 로직 구현 (현재 TODO)

---

### High 우선순위 개선사항

#### 1. 전체 노드 공통
- [ ] **Few-shot 예제 추가** (각 노드당 1개 이상)
- [ ] **Quality Checklist를 실제로 검증하는 후처리 로직**

#### 2. Node 2-A
- [ ] 시나리오 비교 분석 강화 (민감도 분석)
- [ ] Fallback 로직 개선

#### 3. Node 2-B
- [ ] JSON 파싱 실패 시 텍스트 파싱 로직 개선
- [ ] 출력 예제 추가
- [ ] 건물 데이터 활용 가이드 추가

#### 4. Node 2-C
- [ ] Timeline 정의 중복 제거
- [ ] ROI/비용 산정 가이드 추가
- [ ] Fallback 전략 개선

#### 5. Node 3
- [ ] 시나리오 비교 분석 강화
- [ ] 출력 예제 추가
- [ ] JSON 파싱 로직 제거

#### 6. Node 4
- [ ] TCFD 원칙 점수 산출 로직 개선 (이분법 → 다단계)
- [ ] 검증 리포트 상세화

#### 7. Node 5
- [ ] Governance 섹션 LLM 맞춤화 옵션
- [ ] Metrics 섹션에 리스크 분포 테이블 추가

#### 8. Node 6
- [ ] LLM 기반 최종 품질 검증 추가
- [ ] 메타데이터 요약문 자동 생성

---

### Medium 우선순위 개선사항

#### 1. 토큰 효율화
- [ ] Node 2-A, 2-B, 2-C: 중복 설명 제거
- [ ] 프롬프트 길이 10-15% 단축 목표

#### 2. 컨텍스트 활용도 향상
- [ ] Building Data 활용률 증가
- [ ] Additional Data 활용 패턴 표준화

#### 3. 출력 구조 통일
- [ ] JSON vs Markdown 일관성
- [ ] 에러 처리 패턴 통일

#### 4. Chain-of-Thought 적용 검토
- [ ] Node 2-A 시나리오 분석에 적용 가능
- [ ] Node 3 Executive Summary에 적용 가능

---

### Low 우선순위 개선사항

1. **프롬프트 언어 통일** (영어 vs 한국어)
2. **검증 임계값 조정** (예: 200자 → 400자)
3. **추가 차트 및 시각화** (Node 5)
4. **PDF 생성 백엔드 옵션** (Node 6)

---

### 예상 효과

#### **개선 전 (현재)**
- 총 토큰 사용량: 약 40,000-55,000 토큰/보고서
- LLM 호출 시간: 약 2-3분 (5개 병렬 × 2 노드)
- 품질 점수: 평균 75-85/100

#### **개선 후 (예상)**
- 총 토큰 사용량: 약 35,000-48,000 토큰/보고서 (**10-15% 감소**)
- LLM 호출 시간: 약 2-2.5분 (효율화)
- 품질 점수: 평균 85-95/100 (**10-20점 향상**)

---

### 다음 단계 권장사항

#### **Phase 1 (1-2주)**: Critical 개선사항 적용
1. 출력 형식 통일 (JSON vs Markdown)
2. 컨텍스트 보강 (사업장 수, 포트폴리오 비율)
3. DB 저장 구현
4. Top 5 리스크 전체 활용

#### **Phase 2 (2-3주)**: High 우선순위 개선사항 적용
1. Few-shot 예제 추가 (각 노드당 1개)
2. LLM 기반 검증 추가 (Node 4, 6)
3. 섹션 맞춤화 (Node 5 Governance)
4. 건물 데이터 활용 가이드

#### **Phase 3 (3-4주)**: Medium 우선순위 개선사항 적용
1. 토큰 효율화 (중복 제거)
2. 고급 기능 추가 (리스크 분포 테이블 등)
3. Chain-of-Thought 적용 검토

#### **Phase 4 (지속적)**: 모니터링 및 최적화
1. 실제 보고서 품질 점수 추적
2. 사용자 피드백 반영
3. 프롬프트 A/B 테스트

---

## 결론

이 분석 보고서는 TCFD 보고서 생성 워크플로우의 Node 2-A부터 Node 6까지 총 7개 노드의 LLM 프롬프팅을 상세히 분석했습니다.

**핵심 발견사항**:
1. **LLM 활용 노드 (2-A, 2-B, 2-C, 3)**: 전반적으로 우수한 구조를 가지고 있으나, 출력 형식 명확화, Few-shot 예제 추가, 토큰 효율화가 필요
2. **규칙 기반 노드 (4, 5, 6)**: 빠르고 효율적이나, LLM 활용 기회를 놓쳤으며 추가 검증 및 맞춤화 기능 필요

**최우선 개선사항**:
- Node 2-A: 출력 형식 JSON 통일, 사업장 수 컨텍스트 명시
- Node 3: Top 5 리스크 전체 포함, 투자 계획 정보 보강
- Node 4: LLM 기반 내용 검증 추가
- Node 5: Top 5 전체 활용, 리스크 분포 테이블 추가
- Node 6: 실제 DB 저장 구현

이러한 개선사항을 단계적으로 적용하면 보고서 품질을 10-20점 향상시키고, 토큰 사용량을 10-15% 절감할 수 있을 것으로 기대됩니다.

---

**문서 메타데이터**:
- 작성자: AI Agent Analysis System
- 분석 범위: 7개 노드, 총 약 4,500줄 코드
- 분석 방법: 전체 파일 읽기 + 프롬프트 구조 분석 + TCFD 기준 평가
- 권장사항 수: Critical 7개, High 15개, Medium 4개, Low 4개
