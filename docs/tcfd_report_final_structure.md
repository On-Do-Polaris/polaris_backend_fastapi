# TCFD 보고서 최종 구조 명세

**작성일**: 2025-12-15
**버전**: v2.0 (7-Node Structure)
**목적**: 프론트엔드 개발자를 위한 TCFD 보고서 JSON 구조 정의

---

## 📋 목차 (Table of Contents)

TCFD 보고서는 총 **4개 섹션**으로 구성되며, 약 **18-20 페이지** 분량입니다.

### 1. Governance (거버넌스) - 3~4 페이지
```
1. Governance
  1.1 이사회의 감독
  1.2 경영진의 역할
```

### 2. Strategy (전략) - 5~11 페이지
```
2. Strategy
  Executive Summary
  2.1 리스크 및 기회 식별
      - 사업장별 물리적 리스크 AAL 분포 (HeatmapTable)
  2.2 사업 및 재무 영향
  2.3 주요 리스크별 영향 분석 및 대응 방안
      P1. [리스크명] 영향 분석
      P1. [리스크명] 대응 전략
      P2. [리스크명] 영향 분석
      P2. [리스크명] 대응 전략
      P3. [리스크명] 영향 분석
      P3. [리스크명] 대응 전략
      P4. [리스크명] 영향 분석
      P4. [리스크명] 대응 전략
      P5. [리스크명] 영향 분석
      P5. [리스크명] 대응 전략
```

### 3. Risk Management (리스크 관리) - 12~14 페이지
```
3. Risk Management
  3.1 리스크 식별 및 평가 프로세스
  3.2 전사적 리스크 관리 체계(ERM) 통합
  3.3 주요 대응 전략
```

### 4. Metrics and Targets (지표 및 목표) - 15~18 페이지
```
4. Metrics and Targets
  4.1 주요 지표: 연평균 손실(AAL)
      - 시나리오별 포트폴리오 AAL 추이 비교 (Table)
      - 포트폴리오 AAL 추이 (2024-2100) (LineChart)
  4.2 목표 및 이행 계획
```

### 5. Appendix (부록) - 19~20 페이지
```
5. Appendix
  5.1 용어 정의
  5.2 시나리오 설명
  5.3 방법론 상세
```

---

## 🎨 JSON 블록 타입 (5가지)

보고서는 다음 5가지 JSON 블록 타입으로 구성됩니다:

| 블록 타입 | 생성 노드 | 개수 | 설명 |
|---------|---------|------|-----|
| `TextBlock` | Node 2-B, 2-C, 3, 5 | 다수 | 일반 텍스트 섹션 |
| `TableBlock` | Node 2-A | 1개 | 시나리오별 AAL 비교표 |
| `HeatmapTableBlock` | Node 3 | 1개 | 사업장별 리스크 분포 히트맵 |
| `LineChartBlock` | Node 5 | 1개 | AAL 추이 차트 |
| `BarChartBlock` | (미사용) | 0개 | 향후 확장용 |

---

## 📦 최종 JSON 구조 (Key 정의)

### 1️⃣ 최상위 Report 객체

```json
{
  "report_id": "tcfd_report_20251215_143022",
  "meta": {
    "company_name": "폴라리스",
    "report_title": "TCFD 기후 관련 재무정보 공시 보고서",
    "report_date": "2025-12-15",
    "total_pages": 20,
    "total_sections": 5
  },
  "table_of_contents": [
    {
      "section_id": "governance",
      "title": "1. Governance",
      "page_start": 3,
      "page_end": 4
    },
    {
      "section_id": "strategy",
      "title": "2. Strategy",
      "page_start": 5,
      "page_end": 11
    },
    {
      "section_id": "risk_management",
      "title": "3. Risk Management",
      "page_start": 12,
      "page_end": 14
    },
    {
      "section_id": "metrics_targets",
      "title": "4. Metrics and Targets",
      "page_start": 15,
      "page_end": 18
    },
    {
      "section_id": "appendix",
      "title": "5. Appendix",
      "page_start": 19,
      "page_end": 20
    }
  ],
  "sections": [
    /* Section 객체 배열 (아래 참조) */
  ]
}
```

**Key 설명**:
- `report_id` (string): 보고서 고유 ID (타임스탬프 기반)
- `meta` (object): 보고서 메타데이터
- `table_of_contents` (array): 목차 정보
- `sections` (array): 실제 섹션 데이터

---

### 2️⃣ Section 객체

```json
{
  "section_id": "strategy",
  "title": "2. Strategy",
  "page_start": 5,
  "page_end": 11,
  "blocks": [
    /* Block 객체 배열 (아래 참조) */
  ]
}
```

**Key 설명**:
- `section_id` (string): 섹션 고유 ID (`governance`, `strategy`, `risk_management`, `metrics_targets`, `appendix`)
- `title` (string): 섹션 제목
- `page_start` (integer): 시작 페이지 번호
- `page_end` (integer): 종료 페이지 번호
- `blocks` (array): 섹션 내 블록 배열

---

### 3️⃣ Block 객체 (5가지 타입)

#### Type 1: TextBlock

```json
{
  "type": "text",
  "subheading": "P1. 하천범람 영향 분석",
  "content": "**재무적 영향**\n하천 범람으로 인한 예상 연평균 손실액은..."
}
```

**Key 설명**:
- `type` (string): `"text"` (고정값)
- `subheading` (string): 소제목
- `content` (string): 본문 (Markdown 형식 지원)

---

#### Type 2: TableBlock

```json
{
  "type": "table",
  "title": "시나리오별 포트폴리오 AAL 추이 비교",
  "data": {
    "headers": ["시나리오", "2024", "2030", "2040", "2050", "2100", "증가율"],
    "rows": [
      {
        "cells": ["SSP1-2.6 (지속가능)", "52.9%", "51.2%", "49.5%", "48.1%", "45.0%", "-14.9%"]
      },
      {
        "cells": ["SSP2-4.5 (중간)", "52.9%", "53.8%", "56.2%", "58.9%", "65.3%", "+23.4%"]
      },
      {
        "cells": ["SSP3-7.0 (지역경쟁)", "52.9%", "54.5%", "59.1%", "65.2%", "78.1%", "+47.6%"]
      },
      {
        "cells": ["SSP5-8.5 (화석연료)", "52.9%", "55.2%", "61.8%", "70.4%", "89.7%", "+69.6%"]
      }
    ]
  }
}
```

**Key 설명**:
- `type` (string): `"table"` (고정값)
- `title` (string): 표 제목
- `data.headers` (array of strings): 헤더 행
- `data.rows` (array of objects): 데이터 행
  - `cells` (array of strings): 각 행의 셀 값

---

#### Type 3: HeatmapTableBlock

```json
{
  "type": "heatmap_table",
  "title": "사업장별 물리적 리스크 AAL 분포",
  "data": {
    "headers": ["사업장", "하천범람", "태풍", "도시침수", "극심한고온", "해수면상승", "Total AAL"],
    "rows": [
      {
        "site_name": "서울 본사",
        "cells": [
          {
            "value": "5.2%",
            "bg_color": "yellow"
          },
          {
            "value": "12.8%",
            "bg_color": "orange"
          },
          {
            "value": "3.1%",
            "bg_color": "yellow"
          },
          {
            "value": "1.5%",
            "bg_color": "gray"
          },
          {
            "value": "0.2%",
            "bg_color": "gray"
          },
          {
            "value": "22.8%",
            "bg_color": "orange"
          }
        ]
      }
    ],
    "legend": [
      {
        "color": "gray",
        "label": "0-3% (낮음)"
      },
      {
        "color": "yellow",
        "label": "3-10% (중간)"
      },
      {
        "color": "orange",
        "label": "10-30% (높음)"
      },
      {
        "color": "red",
        "label": "30%+ (매우 높음)"
      }
    ]
  }
}
```

**Key 설명**:
- `type` (string): `"heatmap_table"` (고정값)
- `title` (string): 표 제목
- `data.headers` (array of strings): 헤더 행
- `data.rows` (array of objects): 데이터 행
  - `site_name` (string): 사업장 이름
  - `cells` (array of objects): 각 셀
    - `value` (string): 표시 값
    - `bg_color` (string): 배경색 (`"gray"`, `"yellow"`, `"orange"`, `"red"`)
- `data.legend` (array of objects): 범례
  - `color` (string): 색상 코드
  - `label` (string): 범례 레이블

---

#### Type 4: LineChartBlock

```json
{
  "type": "line_chart",
  "title": "포트폴리오 AAL 추이 (2024-2100)",
  "data": {
    "x_axis": {
      "label": "연도",
      "categories": [2024, 2030, 2040, 2050, 2100]
    },
    "y_axis": {
      "label": "AAL",
      "min": 0,
      "max": 100,
      "unit": "%"
    },
    "series": [
      {
        "name": "SSP1-2.6",
        "color": "#4CAF50",
        "data": [52.9, 51.2, 49.5, 48.1, 45.0]
      },
      {
        "name": "SSP2-4.5",
        "color": "#FFC107",
        "data": [52.9, 53.8, 56.2, 58.9, 65.3]
      },
      {
        "name": "SSP3-7.0",
        "color": "#FF9800",
        "data": [52.9, 54.5, 59.1, 65.2, 78.1]
      },
      {
        "name": "SSP5-8.5",
        "color": "#F44336",
        "data": [52.9, 55.2, 61.8, 70.4, 89.7]
      }
    ]
  }
}
```

**Key 설명**:
- `type` (string): `"line_chart"` (고정값)
- `title` (string): 차트 제목
- `data.x_axis` (object): X축 정보
  - `label` (string): X축 레이블
  - `categories` (array): X축 카테고리 (연도)
- `data.y_axis` (object): Y축 정보
  - `label` (string): Y축 레이블
  - `min` (number): 최소값
  - `max` (number): 최대값
  - `unit` (string): 단위
- `data.series` (array of objects): 데이터 시리즈
  - `name` (string): 시리즈 이름
  - `color` (string): 선 색상 (HEX 코드)
  - `data` (array of numbers): 데이터 포인트

---

#### Type 5: BarChartBlock (향후 확장용)

```json
{
  "type": "bar_chart",
  "title": "리스크별 AAL 분포",
  "data": {
    "x_axis": {
      "label": "리스크 유형",
      "categories": ["하천범람", "태풍", "도시침수", "극심한고온", "해수면상승"]
    },
    "y_axis": {
      "label": "AAL",
      "min": 0,
      "max": 30,
      "unit": "%"
    },
    "series": [
      {
        "name": "2024",
        "color": "#2196F3",
        "data": [12.5, 18.3, 8.7, 5.2, 3.1]
      },
      {
        "name": "2100",
        "color": "#F44336",
        "data": [18.9, 28.5, 15.2, 12.8, 8.9]
      }
    ]
  }
}
```

**Key 설명**:
- `type` (string): `"bar_chart"` (고정값)
- 나머지 구조는 LineChartBlock과 동일

---

## 🔄 데이터 흐름 요약

```
Node 0 (Data Loading)
  ↓
Node 1 (Template Loading)
  ↓
Node 2-A (Scenario Analysis) → TableBlock 생성
  ↓
Node 2-B (Impact Analysis) → TextBlock x5 생성 (P1~P5 영향)
  ↓
Node 2-C (Mitigation Strategies) → TextBlock x5 생성 (P1~P5 대응)
  ↓
Node 3 (Strategy Section) → HeatmapTableBlock 생성 + 블록 조립
  ↓
Node 4 (Validator) → 검증
  ↓
Node 5 (Composer) → LineChartBlock 생성 + 전체 조립
  ↓
Node 6 (Finalizer) → 최종 보고서 JSON 반환
```

---

## 📌 프론트엔드 구현 가이드

### 1. JSON 파싱 순서
1. `report.meta`를 읽어 보고서 제목 및 페이지 수 표시
2. `report.table_of_contents`를 읽어 목차 렌더링
3. `report.sections` 배열을 순회하며 각 섹션 렌더링
4. 각 섹션의 `blocks` 배열을 순회하며 `type` 필드에 따라 적절한 컴포넌트 렌더링

### 2. Block 렌더링 매핑
```javascript
switch (block.type) {
  case 'text':
    return <TextBlock data={block} />
  case 'table':
    return <TableBlock data={block} />
  case 'heatmap_table':
    return <HeatmapTableBlock data={block} />
  case 'line_chart':
    return <LineChartBlock data={block} />
  case 'bar_chart':
    return <BarChartBlock data={block} />
  default:
    return null
}
```

### 3. 색상 코드 (HeatmapTable)
```css
.bg-gray { background-color: #E0E0E0; }   /* 0-3% (낮음) */
.bg-yellow { background-color: #FFF59D; } /* 3-10% (중간) */
.bg-orange { background-color: #FFCC80; } /* 10-30% (높음) */
.bg-red { background-color: #EF9A9A; }    /* 30%+ (매우 높음) */
```

### 4. 차트 라이브러리 권장
- **LineChart / BarChart**: Chart.js, Recharts, ApexCharts
- **HeatmapTable**: 커스텀 CSS Grid 또는 Material-UI Table

---

## 🚀 API 응답 예시

### Request
```
POST /api/tcfd-report/generate
{
  "site_ids": [1, 2, 3, 4, 5, 6, 7, 8],
  "excel_file": "optional_additional_data.xlsx",
  "user_id": 123
}
```

### Response
```json
{
  "status": "success",
  "report": {
    "report_id": "tcfd_report_20251215_143022",
    "meta": { ... },
    "table_of_contents": [ ... ],
    "sections": [ ... ]
  }
}
```

---

## ✅ Key 값 체크리스트

프론트엔드 개발 시 다음 key 값들이 **고정**되어 있으므로 안전하게 사용 가능합니다:

### Report 레벨
- ✅ `report_id` (string)
- ✅ `meta` (object)
  - ✅ `company_name` (string)
  - ✅ `report_title` (string)
  - ✅ `report_date` (string)
  - ✅ `total_pages` (integer)
  - ✅ `total_sections` (integer)
- ✅ `table_of_contents` (array)
- ✅ `sections` (array)

### Section 레벨
- ✅ `section_id` (string): `"governance"`, `"strategy"`, `"risk_management"`, `"metrics_targets"`, `"appendix"`
- ✅ `title` (string)
- ✅ `page_start` (integer)
- ✅ `page_end` (integer)
- ✅ `blocks` (array)

### Block 레벨 (공통)
- ✅ `type` (string): `"text"`, `"table"`, `"heatmap_table"`, `"line_chart"`, `"bar_chart"`

### TextBlock
- ✅ `subheading` (string)
- ✅ `content` (string)

### TableBlock
- ✅ `title` (string)
- ✅ `data.headers` (array of strings)
- ✅ `data.rows` (array of objects)
  - ✅ `cells` (array of strings)

### HeatmapTableBlock
- ✅ `title` (string)
- ✅ `data.headers` (array of strings)
- ✅ `data.rows` (array of objects)
  - ✅ `site_name` (string)
  - ✅ `cells` (array of objects)
    - ✅ `value` (string)
    - ✅ `bg_color` (string): `"gray"`, `"yellow"`, `"orange"`, `"red"`
- ✅ `data.legend` (array of objects)
  - ✅ `color` (string)
  - ✅ `label` (string)

### LineChartBlock & BarChartBlock
- ✅ `title` (string)
- ✅ `data.x_axis` (object)
  - ✅ `label` (string)
  - ✅ `categories` (array)
- ✅ `data.y_axis` (object)
  - ✅ `label` (string)
  - ✅ `min` (number)
  - ✅ `max` (number)
  - ✅ `unit` (string)
- ✅ `data.series` (array of objects)
  - ✅ `name` (string)
  - ✅ `color` (string)
  - ✅ `data` (array of numbers)

---

## 📞 문의

- **백엔드 담당**: AI Agent 팀
- **스키마 정의**: `polaris_backend_fastapi/ai_agent/agents/tcfd_report/schemas.py`
- **업데이트 이력**: `polaris_backend_fastapi/docs/progress/tcfd_report_refactoring_progress.md`
