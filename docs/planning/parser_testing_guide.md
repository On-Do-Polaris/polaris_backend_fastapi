# Parser Testing Guide
**작성일**: 2025-12-12
**목적**: LlamaParse 테스트 절차 및 사용자 필요 작업 안내

---

## 📋 개요

LlamaParse가 "각종 자료/For_RAG" 폴더의 PDF 파일들을 올바르게 처리하는지 검증합니다.

**검증 항목**:
1. ✅ **이미지 처리**: LlamaParse는 이미지를 텍스트 설명으로 변환
2. ✅ **표 추출**: Markdown table 형식으로 추출
3. ✅ **그래프/차트**: 텍스트 설명으로 변환

---

## 🔧 필요한 사전 작업

### 1. 환경 변수 설정 (필수)

`.env` 파일에 LlamaParse API 키가 있는지 확인:

```bash
# .env 파일 확인
cat .env | grep LLAMA_CLOUD_API_KEY
```

**출력 예시**:
```
LLAMA_CLOUD_API_KEY=llx-xxxxxxxxxxxxxxxxxxxxx
```

만약 없다면 추가:
```bash
# .env 파일에 추가
echo 'LLAMA_CLOUD_API_KEY="your-api-key-here"' >> .env
```

API 키 발급 방법:
- LlamaCloud 사이트: https://cloud.llamaindex.ai/
- 로그인 → API Keys → Create New Key
- Free Tier: 1,000 pages/month

---

### 2. Python 가상환경 활성화

```bash
# 프로젝트 루트로 이동
cd /Users/ichangmin/SKALA\ Final\ Project/polaris_backend_fastapi

# 가상환경 활성화 (이미 있다면)
source venv/bin/activate
# 또는
source .venv/bin/activate
```

---

### 3. 의존성 확인

LlamaParse 관련 패키지 설치 확인:

```bash
pip list | grep -E "(llama-parse|llama-index)"
```

**예상 출력**:
```
llama-parse       0.5.14
llama-index       0.11.29
```

만약 없다면 설치:
```bash
pip install llama-parse llama-index
```

---

## 🧪 테스트 실행 방법

### Step 1: 통계 확인 (쿼터 사용 안 함)

먼저 어떤 파일들이 있는지, 예상 페이지 수가 몇 페이지인지 확인:

```bash
python scripts/test_parser.py --stats
```

**예상 출력**:
```
================================================================================
📊 RAG Folder Statistics (No Parsing)
================================================================================

📁 Folder: 각종 자료/For_RAG
📄 Total PDF files: 20

  📄 2025_SK-Inc_Sustainability Report_ENG.pdf
      Size: 33.45 MB
      Estimated pages: ~334

  📄 FINAL-2017-TCFD-Report.pdf
      Size: 2.40 MB
      Estimated pages: ~24

  ...

────────────────────────────────────────────────────────────────────────────────
📊 Total:
  - Total size: 84.23 MB
  - Estimated pages: ~842 pages
  - Free tier quota usage: ~84.2%

💾 Cache Status:
  - Cached files: 0
  - Files already parsed: None
```

**판단**:
- ✅ 1,000페이지 이하면 안전
- ⚠️ 1,000페이지 초과 시 일부 파일만 테스트 권장

---

### Step 2: 단일 파일 테스트 (권장)

가장 작은 파일로 먼저 테스트:

```bash
python scripts/test_parser.py --file "FINAL-2017-TCFD-Report.pdf"
```

**예상 출력**:
```
================================================================================
📄 Testing: 각종 자료/For_RAG/FINAL-2017-TCFD-Report.pdf
================================================================================

✅ Parsing successful!

📊 Statistics:
  - Total documents: 1

  Document 1:
    - Text length: 125430 characters
    - Tables found: 8
    - Has images: Yes

📋 Table Analysis:
  - Total tables extracted: 8

  Example table (first 3 rows):
    Headers: ['Category', 'Recommendation', 'Description']
    Row 1: ['Governance', 'Board Oversight', 'Describe board oversight...']
    Row 2: ['Strategy', 'Risk Identification', 'Describe climate risks...']
    Row 3: ['Risk Management', 'Integration', 'Describe integration...']

🖼️  Image/Chart Analysis:
  - Image/chart mentions found: 15
  - Note: LlamaParse converts images to text descriptions

📝 Content Preview (first 500 characters):
# Final Report
Recommendations of the Task Force on Climate-related Financial Disclosures

## Table of Contents
1. Introduction
2. Governance
   - Board Oversight
   - Management's Role
3. Strategy
   - Climate Risks and Opportunities
   - Scenario Analysis
...

💾 Cache:
  - Cached at: data/parsed_docs/FINAL-2017-TCFD-Report_parsed.json
  - Cache size: 142.35 KB
```

**검증 포인트**:
1. ✅ **Tables found: 8** → 표 추출 성공
2. ✅ **Image/chart mentions: 15** → 이미지가 텍스트로 변환됨
3. ✅ **Text length: 125430 characters** → 충분한 내용 추출
4. ✅ **Cached** → 다음 실행 시 쿼터 사용 안 함

---

### Step 3: 내용 미리보기 (선택)

파싱된 내용을 더 자세히 보려면:

```bash
python scripts/test_parser.py --file "FINAL-2017-TCFD-Report.pdf" --show-content
```

추가로 파싱된 내용의 첫 500자를 출력합니다.

---

### Step 4: 여러 파일 테스트 (선택)

**주의**: 쿼터를 많이 사용하므로 필요 시에만 실행

```bash
# 특정 파일들만 테스트
python scripts/test_parser.py --file "Extreme_Heat_RAG.pdf"
python scripts/test_parser.py --file "River_Flood_RAG.pdf"
python scripts/test_parser.py --file "SnP_Climanomics_PangyoDC_Summary_Report_SK C&C_2024-02-08_08.25.05.688509.pdf"
```

**또는 모든 파일 테스트** (주의!):
```bash
python scripts/test_parser.py --all
```

이 명령은 실행 전에 확인 프롬프트를 표시합니다:
```
⚠️  WARNING: This will use LlamaParse quota!
  - Found 20 PDF files
  - Estimated total pages: ~842 pages
  - Free tier limit: 1,000 pages/month

❓ Continue? (yes/no):
```

---

## 📊 예상 결과

### 성공적인 파싱 시

각 파일에 대해:
```
✅ Parsing successful!
📊 Statistics:
  - Documents: 1
  - Tables: 3~15개 (문서에 따라 다름)
  - Images: Yes (텍스트 설명으로 변환)

💾 Cache: data/parsed_docs/{filename}_parsed.json
```

**캐시 파일 확인**:
```bash
ls -lh data/parsed_docs/
```

각 PDF마다 `{filename}_parsed.json` 파일이 생성됩니다.

---

### 실패 시 디버깅

#### 오류 1: API 키 없음
```
❌ Error: LLAMA_CLOUD_API_KEY not found in environment
```

**해결**: `.env` 파일에 API 키 추가 (위의 Step 1 참고)

---

#### 오류 2: 쿼터 초과
```
❌ Error: Quota exceeded. You have used 1,000/1,000 pages this month.
```

**해결**:
1. 다음 달까지 대기
2. 또는 유료 플랜 업그레이드
3. 이미 파싱된 파일은 캐시에서 로드 (쿼터 사용 안 함)

---

#### 오류 3: 네트워크 오류
```
❌ Error: Connection timeout
```

**해결**:
1. 인터넷 연결 확인
2. 재시도 (일시적 오류일 수 있음)

---

## 🔍 파싱 결과 품질 확인

### 1. 표 추출 품질

**확인 방법**: 캐시 파일 직접 열기

```bash
# 예시: TCFD 리포트 파싱 결과 확인
cat data/parsed_docs/FINAL-2017-TCFD-Report_parsed.json | jq '.[] | .tables | length'
```

**기대값**: 5개 이상 (TCFD 리포트는 표가 많음)

**표 내용 확인**:
```bash
cat data/parsed_docs/FINAL-2017-TCFD-Report_parsed.json | jq '.[] | .tables[0]'
```

**예상 출력**:
```json
{
  "headers": ["Pillar", "Recommendation", "Description"],
  "rows": [
    ["Governance", "Board Oversight", "Describe the board's oversight..."],
    ["Strategy", "Risk & Opportunities", "Describe the climate-related..."],
    ...
  ],
  "markdown": "| Pillar | Recommendation | Description |\n|--------|----------------|-------------|..."
}
```

✅ **품질 기준**: headers와 rows가 올바르게 추출되었는지 확인

---

### 2. 이미지 처리 품질

**LlamaParse의 이미지 처리 방식**:
- 이미지를 직접 추출하지 않음
- 대신 **이미지 내용을 텍스트로 설명**
- 예: "Figure 1: Graph showing temperature increase from 2020 to 2050"

**확인 방법**:
```bash
cat data/parsed_docs/FINAL-2017-TCFD-Report_parsed.json | jq '.[] | .text' | grep -i "figure\|chart\|graph"
```

**예상 출력**:
```
"Figure 1: Climate scenario comparison showing RCP 2.6, 4.5, and 8.5 pathways"
"Chart 2: Global temperature anomalies from 1850 to 2100"
"Graph 3: Financial impact of physical risks by sector"
```

✅ **품질 기준**: 이미지가 의미 있는 설명으로 변환되었는지 확인

---

### 3. 전체 텍스트 품질

**확인 방법**: 첫 1,000자만 출력
```bash
cat data/parsed_docs/FINAL-2017-TCFD-Report_parsed.json | jq '.[] | .text' | head -c 1000
```

✅ **품질 기준**:
- 구조화된 텍스트 (제목, 섹션이 명확)
- 깨진 글자 없음
- Markdown 형식 유지

---

## 📦 캐시 관리

### 캐시 위치
```
data/parsed_docs/
├── FINAL-2017-TCFD-Report_parsed.json
├── Extreme_Heat_RAG_parsed.json
├── River_Flood_RAG_parsed.json
└── ...
```

### 캐시 삭제 (재파싱 필요 시)
```bash
# 특정 파일 캐시 삭제
rm data/parsed_docs/FINAL-2017-TCFD-Report_parsed.json

# 전체 캐시 삭제
rm -rf data/parsed_docs/*.json
```

**주의**: 캐시 삭제 후 재실행 시 쿼터 다시 사용됨

---

## ✅ 테스트 완료 체크리스트

- [ ] `.env`에 `LLAMA_CLOUD_API_KEY` 설정 확인
- [ ] 가상환경 활성화 확인
- [ ] `llama-parse` 패키지 설치 확인
- [ ] `python scripts/test_parser.py --stats` 실행 (쿼터 사용량 확인)
- [ ] 단일 파일 테스트 성공 (`--file "FINAL-2017-TCFD-Report.pdf"`)
- [ ] 표 추출 확인 (Tables found > 0)
- [ ] 이미지 처리 확인 (Image mentions found > 0)
- [ ] 캐시 파일 생성 확인 (`data/parsed_docs/*.json`)
- [ ] 파싱 품질 검증 (표, 이미지, 텍스트 내용 확인)

---

## 🚀 다음 단계

테스트 완료 후:

1. **결과 공유**:
   - 어떤 파일을 테스트했는지
   - 표/이미지 추출이 잘 되었는지
   - 문제가 있었다면 어떤 부분인지

2. **RAG Ingestion 실행**:
   ```bash
   python scripts/ingest_rag_documents.py --all
   ```
   - 파싱 결과를 Qdrant에 업로드
   - Phase 1 완료

3. **Option 3 Implementation 시작**:
   - [option3_implementation_plan.md](./option3_implementation_plan.md) 참고
   - Phase 2부터 Agent별 RAG 통합

---

## 📞 문제 발생 시

문제가 발생하면 다음 정보와 함께 문의:

1. **오류 메시지** (전체 출력)
2. **테스트한 파일명**
3. **실행한 명령어**
4. **환경 정보**:
   ```bash
   python --version
   pip list | grep llama
   cat .env | grep LLAMA
   ```

---

**작성자**: Claude Code
**관련 문서**:
- [Option 3 Implementation Plan](./option3_implementation_plan.md)
- [RAG Parsing Strategy](./rag_parsing_strategy.md)
