# Parser Test Summary - 바로 시작하기
**작성일**: 2025-12-12

---

## 📦 생성된 파일들

### 1. 📘 Implementation Plan
**파일**: `docs/planning/option3_implementation_plan.md`

**내용**:
- Option 3 (Hybrid) 전체 실행 계획
- 6개 Phase로 구성 (6주 예상)
- Agent별 RAG 통합 방법
- Prompt 개선 예시 (SK 스타일)
- StrategyAgent, MetricsAgent 신규 개발 계획
- Governance 하드코딩 템플릿 설계
- Before/After 보고서 비교 (2페이지 → 7페이지)

**주요 하이라이트**:
- ✅ RAG 사용 Agent: 1/7 → 6/7
- ✅ TCFD 커버리지: 30% → 80%+
- ✅ 보고서 분량: 2페이지 → 5~7페이지
- ✅ SK 스타일 프롬프트 (계산식 ❌, 결과/활용 ✅)

---

### 2. 🧪 Parser Test Script
**파일**: `scripts/test_parser.py`

**기능**:
- 단일 PDF 파일 파싱 테스트
- 이미지, 표, 그래프 처리 확인
- 통계 출력 (쿼터 사용 없이)
- 전체 폴더 일괄 테스트

**사용법**:
```bash
# 통계만 확인 (쿼터 사용 안 함)
python scripts/test_parser.py --stats

# 단일 파일 테스트
python scripts/test_parser.py --file "FINAL-2017-TCFD-Report.pdf"

# 모든 파일 테스트 (주의: 쿼터 사용)
python scripts/test_parser.py --all
```

---

### 3. 📖 Testing Guide
**파일**: `docs/planning/parser_testing_guide.md`

**내용**:
- 사전 준비 사항 (환경 변수, 의존성)
- Step-by-step 테스트 절차
- 예상 출력 및 해석 방법
- 오류 발생 시 디버깅
- 파싱 품질 검증 방법
- 체크리스트

---

## ✅ 당신이 해야 할 작업

### Step 1: 환경 변수 확인 (필수)

```bash
# .env 파일에 LlamaParse API 키가 있는지 확인
cat .env | grep LLAMA_CLOUD_API_KEY
```

**예상 출력**:
```
LLAMA_CLOUD_API_KEY=llx-xxxxxxxxxxxxx
```

만약 없다면:
1. LlamaCloud 가입: https://cloud.llamaindex.ai/
2. API Key 발급 (Free Tier: 1,000 pages/month)
3. `.env` 파일에 추가:
   ```bash
   echo 'LLAMA_CLOUD_API_KEY="your-key-here"' >> .env
   ```

---

### Step 2: 의존성 확인

```bash
pip list | grep llama-parse
```

**없다면 설치**:
```bash
pip install llama-parse
```

---

### Step 3: 통계 확인 (쿼터 사용 안 함)

```bash
cd /Users/ichangmin/SKALA\ Final\ Project/polaris_backend_fastapi
python scripts/test_parser.py --stats
```

**예상 출력**:
```
📊 RAG Folder Statistics
📁 Folder: 각종 자료/For_RAG
📄 Total PDF files: 20

📊 Total:
  - Estimated pages: ~842 pages
  - Free tier quota usage: ~84.2%
```

✅ **판단**: 1,000페이지 이하면 안전

---

### Step 4: 단일 파일 테스트

```bash
python scripts/test_parser.py --file "FINAL-2017-TCFD-Report.pdf"
```

**예상 출력**:
```
✅ Parsing successful!

📊 Statistics:
  - Tables found: 8
  - Image mentions: 15

💾 Cache: data/parsed_docs/FINAL-2017-TCFD-Report_parsed.json
```

✅ **검증 포인트**:
- Tables found > 0 → 표 추출 성공
- Image mentions > 0 → 이미지 텍스트 변환 성공
- Cache 생성 → 다음 실행 시 쿼터 사용 안 함

---

### Step 5: 결과 확인

파싱된 내용 확인:
```bash
cat data/parsed_docs/FINAL-2017-TCFD-Report_parsed.json | jq '.[] | .tables | length'
```

**예상**: 5~10 (표 개수)

---

## 🚀 테스트 완료 후 다음 단계

### 1. 결과 공유
다음 정보를 공유해주세요:
- ✅ 테스트한 파일 이름
- ✅ Tables found 개수
- ✅ Image mentions 개수
- ❌ 문제가 있었다면 오류 메시지

### 2. RAG Ingestion 실행
테스트가 성공적이면:
```bash
python scripts/ingest_rag_documents.py --all
```

이 명령은:
- 파싱된 결과를 Qdrant에 업로드
- `tcfd_documents` collection (일반 텍스트)
- `tcfd_tables` collection (표 데이터)

### 3. Option 3 Implementation 시작
- Phase 1 완료 체크
- Phase 2로 진행 (Agent별 RAG 통합)

---

## 📊 빠른 명령어 레퍼런스

| 명령어 | 용도 | 쿼터 사용 |
|--------|------|-----------|
| `python scripts/test_parser.py --stats` | 통계 확인 | ❌ 없음 |
| `python scripts/test_parser.py --file "XXX.pdf"` | 단일 파일 테스트 | ✅ 사용 (캐시 후 재사용 ❌) |
| `python scripts/test_parser.py --all` | 전체 파일 테스트 | ✅ 많이 사용 |
| `python scripts/test_parser.py --file "XXX.pdf" --show-content` | 내용 미리보기 | ✅ 사용 |

---

## ❓ FAQ

**Q: 쿼터는 얼마나 사용하나요?**
A:
- TCFD 리포트: ~24 pages
- SK 보고서: ~334 pages
- Risk RAG 파일들: ~20 pages each
- 전체: ~842 pages (Free Tier의 84%)

**Q: 캐시는 어디에 저장되나요?**
A: `data/parsed_docs/` 폴더에 JSON 형식으로 저장됩니다.

**Q: 캐시를 삭제하면 쿼터를 다시 사용하나요?**
A: 네, 캐시 삭제 후 재실행 시 쿼터가 다시 사용됩니다.

**Q: 표나 이미지가 잘 추출 안 되면?**
A:
1. 파일 품질 확인 (스캔 PDF는 품질 저하)
2. `--show-content`로 텍스트 확인
3. 필요 시 다른 PDF 파서 고려 (PyPDF2, pdfplumber)

---

**작성자**: Claude Code
**다음 읽을 문서**:
1. [Parser Testing Guide](./parser_testing_guide.md) - 자세한 설명
2. [Option 3 Implementation Plan](./option3_implementation_plan.md) - 전체 계획
