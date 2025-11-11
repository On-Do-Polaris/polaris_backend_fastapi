# SKAX Physical Risk Analyzer

SKAX 물리적 리스크 분석 에이전트 시스템 (Super Agent 계층 구조)

## 개요

이 시스템은 기후 변화에 따른 물리적 리스크를 분석하기 위한 에이전트 기반 프레임워크입니다.
**Super Agent 계층 구조**를 채택하여 18개의 Sub Agent가 병렬로 AAL 분석 및 물리적 리스크 점수를 계산합니다.

## 주요 기능

### 1. 데이터 수집 에이전트 (Data Collection Agent)
- 기상 데이터 수집
- 지리 정보 수집
- 기후 시나리오 데이터 수집

### 2. 취약성 분석 에이전트 (Vulnerability Analysis Agent)
- 건물 연식 분석
- 내진 설계 수준 평가
- 소방차 진입 가능성 분석

### 3. AAL 분석 (9개 Sub Agent)
각 리스크별로 **연평균 재무 손실률(AAL %)** 계산:
- **공식**: AAL(%) = P(H) × 손상률 × (1 - 보험보전율) × 100

**9개 기후 리스크:**
1. 극심한 고온 (High Temperature)
2. 극심한 한파 (Cold Wave)
3. 산불 (Wildfire)
4. 가뭄 (Drought)
5. 물 부족 (Water Scarcity)
6. 해안 홍수 (Coastal Flood)
7. 내륙 홍수 (Inland Flood)
8. 도심 홍수 (Urban Flood)
9. 열대성 태풍 (Typhoon)

### 4. 물리적 리스크 점수 계산 (9개 Sub Agent)
각 리스크별로 **AAL × 자산가치**를 기반으로 100점 스케일 점수 산출:
- **공식**: 재무 손실액 = AAL(%) × 총 자산 가치
- **100점 변환**: 점수 = min((재무손실액 / 10억원) × 100, 100)

### 5. 보고서 템플릿 생성 (Report Template Agent)
- RAG 기반 유사 보고서 검색
- 내용 구조 및 작성 방향 제시
- 리스크별 작성 지침 생성

### 6. 대응 전략 생성 (Strategy Generation Agent)
- LLM + RAG 기반 대응 전략 수립
- 유사 사례 참조 및 리스크별 맞춤 전략
- 우선순위 기반 실행 계획

### 7. 최종 보고서 생성 (Report Generation Agent)
- 모든 분석 결과 통합
- 종합 보고서 작성
- 시각화 포함

### 8. 검증 에이전트 (Validation Agent)
- 분석 결과 품질 검증
- 데이터 일관성 체크
- 자동 재시도 (최대 3회)
