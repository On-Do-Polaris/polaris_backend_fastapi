"""
Node 1 Template Loading v2 - 실제 PDF 테스트

실행 방법:
    cd c:/Users/SKAX/Documents/POLARIS/polaris_backend_fastapi-develop
    python -m ai_agent.agents.tcfd_report.test_node1_with_pdf

필수 패키지:
    pip install pymupdf  # PDF 읽기용
    pip install openai   # 실제 LLM 사용 시

환경변수 (실제 LLM 사용 시):
    set OPENAI_API_KEY=your_key_here
    set USE_REAL_LLM=true
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
import sys


def extract_text_from_pdf(pdf_path: str, max_pages: int = None) -> dict:
    """
    PDF에서 텍스트 추출 (pymupdf 사용)

    Returns:
        {
            "full_text": str,
            "total_pages": int,
            "extracted_pages": int,
            "page_texts": list[str]
        }
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("❌ PyMuPDF가 설치되지 않았습니다.")
        print("   설치: pip install pymupdf")
        sys.exit(1)

    print(f"\n📄 PDF 읽는 중: {Path(pdf_path).name}")

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    extract_pages = max_pages if max_pages else total_pages

    page_texts = []
    full_text = []

    for page_num in range(min(extract_pages, total_pages)):
        page = doc[page_num]
        text = page.get_text()

        if text.strip():  # 빈 페이지 제외
            page_texts.append(text)
            full_text.append(text)

        if (page_num + 1) % 10 == 0:
            print(f"  - {page_num + 1}/{extract_pages} 페이지 처리 중...")

    doc.close()

    result = {
        "full_text": "\n\n".join(full_text),
        "total_pages": total_pages,
        "extracted_pages": len(page_texts),
        "page_texts": page_texts
    }

    print(f"✅ PDF 추출 완료:")
    print(f"  - 총 페이지: {total_pages}")
    print(f"  - 추출 페이지: {len(page_texts)}")
    print(f"  - 텍스트 길이: {len(result['full_text']):,} 글자")

    return result


def find_tcfd_section(full_text: str) -> str:
    """
    PDF 전체 텍스트에서 TCFD 관련 섹션만 추출

    전략:
    - "TCFD", "기후변화", "물리적 리스크", "시나리오 분석" 키워드 근처 텍스트 추출
    - Governance, Strategy, Risk Management, Metrics 섹션 찾기
    """
    # 간단한 구현: TCFD 키워드가 포함된 라인부터 일정 범위 추출
    lines = full_text.split('\n')

    tcfd_start = None
    tcfd_end = None

    for i, line in enumerate(lines):
        if tcfd_start is None:
            if any(keyword in line.upper() for keyword in ['TCFD', '기후변화', 'CLIMATE', 'GOVERNANCE']):
                tcfd_start = max(0, i - 10)  # 10줄 앞부터

        if tcfd_start is not None and tcfd_end is None:
            # TCFD 섹션 끝 감지 (다음 챕터 시작 or 부록 시작)
            if any(keyword in line for keyword in ['부록', 'APPENDIX', '재무제표', '감사보고서']):
                tcfd_end = i
                break

    if tcfd_start is not None:
        if tcfd_end is None:
            tcfd_end = len(lines)

        tcfd_text = '\n'.join(lines[tcfd_start:tcfd_end])
        print(f"\n🔍 TCFD 섹션 추출:")
        print(f"  - 시작 라인: {tcfd_start}")
        print(f"  - 종료 라인: {tcfd_end}")
        print(f"  - 추출 길이: {len(tcfd_text):,} 글자")

        return tcfd_text
    else:
        print("\n⚠️ TCFD 섹션을 찾지 못했습니다. 전체 텍스트를 사용합니다.")
        return full_text


class MockLLM:
    """Mock LLM (테스트용)"""

    def __init__(self):
        self.call_count = 0

    async def ainvoke(self, prompt):
        self.call_count += 1

        print(f"\n{'='*80}")
        print(f"🤖 Mock LLM 호출 #{self.call_count}")
        print(f"{'='*80}")
        print(f"프롬프트 길이: {len(prompt):,} 글자")

        # 프롬프트에서 주요 키워드 추출
        keywords = []
        if "INIT" in prompt or "ELITE" in prompt:
            keywords.append("INIT 모드 (최고 퀄리티)")
        if "REPAIR" in prompt or "AGGRESSIVELY" in prompt:
            keywords.append("REPAIR 모드 (강화된 재분석)")
        if "SK" in prompt:
            keywords.append(f"회사: {prompt.split('for ')[1].split('.')[0] if 'for ' in prompt else 'Unknown'}")

        print(f"감지된 키워드: {', '.join(keywords)}")
        print(f"{'='*80}\n")

        # 실제와 유사한 Mock 응답 (더 풍부하게)
        return json.dumps({
            "tone": {
                "formality": "formal, professional",
                "audience": "institutional investors, stakeholders, regulatory bodies",
                "voice": "data-driven, transparent, forward-looking",
                "language_level": "technical yet accessible",
                "emotional_tone": "confident but measured, acknowledging risks while showing commitment"
            },
            "section_structure": {
                "executive_summary": {
                    "pages": 2,
                    "priority": "highest",
                    "key_messages": ["overall AAL", "top risks", "strategic response"]
                },
                "governance": {
                    "pages": 3,
                    "subsections": [
                        "이사회 감독 체계",
                        "경영진 역할 및 책임",
                        "ESG 위원회 운영",
                        "보상 체계 연계"
                    ]
                },
                "strategy": {
                    "pages": 8,
                    "subsections": [
                        "리스크 및 기회 식별",
                        "시나리오 분석 (SSP 4종)",
                        "사업장별 물리적 리스크 평가",
                        "P1-P5 리스크 상세 분석",
                        "재무적 영향 평가",
                        "대응 전략 (단기/중기/장기)"
                    ]
                },
                "risk_management": {
                    "pages": 3,
                    "subsections": [
                        "리스크 식별 프로세스",
                        "평가 방법론 (AAL, 시나리오 기반)",
                        "통합 리스크 관리 체계"
                    ]
                },
                "metrics_targets": {
                    "pages": 4,
                    "subsections": [
                        "Scope 1,2,3 배출량",
                        "재생에너지 사용률 (RE100)",
                        "AAL 추이",
                        "Net Zero 2040 목표 및 진척도"
                    ]
                },
                "appendix": {
                    "pages": 5,
                    "subsections": [
                        "분석 방법론",
                        "데이터 소스",
                        "용어 정의",
                        "제3자 검증"
                    ]
                }
            },
            "section_style": {
                "executive_summary": {
                    "intro": "TCFD 권고안 준수 및 분석 개요",
                    "body": "핵심 지표 요약 (AAL, 온실가스, 목표), 주요 리스크 하이라이트",
                    "conclusion": "전략적 대응 방향 및 커밋먼트"
                },
                "governance": {
                    "intro": "기후변화 지배구조 체계 소개",
                    "body": "이사회 역할, 경영진 책임, 위원회 구성 및 운영 실적",
                    "conclusion": "지배구조 강화 계획"
                },
                "strategy": {
                    "intro": "기후변화 전략 프레임워크",
                    "body": "시나리오별 정량 분석, 사업장별 리스크 평가, P1-P5 영향 분석, 대응 로드맵",
                    "conclusion": "전략 실행 계획 및 모니터링 체계"
                },
                "risk_management": {
                    "intro": "통합 리스크 관리 체계 개요",
                    "body": "물리적 리스크 식별/평가/관리 프로세스, 전사 리스크 통합",
                    "conclusion": "지속적 개선 방향"
                },
                "metrics_targets": {
                    "intro": "주요 지표 및 목표 설정 배경",
                    "body": "Scope별 배출량, AAL 추이, 재생에너지 현황, 목표 대비 진척도",
                    "conclusion": "2030/2040 목표 달성 로드맵"
                }
            },
            "formatting_rules": {
                "headings": "1. 제목 (굵은 글씨, 좌측 정렬)",
                "subheadings": "1.1, 1.2 형식 (중간 굵기)",
                "lists": "- 불릿 포인트 (주요 항목), 1) 2) 3) 번호 (세부 항목)",
                "emphasis": "**굵은 글씨** (핵심 수치/용어), *이탤릭* (정의 첫 등장)",
                "data_presentation": "표(비교 데이터), 차트(추이/분포), 히트맵(리스크 분포)",
                "spacing": "섹션 간 2줄, 문단 간 1줄",
                "citations": "[출처명, 연도] 형식, 각주 활용"
            },
            "report_years": [2023, 2024, 2025],
            "esg_structure": {
                "E": [
                    "기후변화 (TCFD)",
                    "에너지 관리 (RE100)",
                    "수자원 관리",
                    "폐기물 관리",
                    "환경오염 방지"
                ],
                "S": [
                    "인권 및 다양성",
                    "임직원 안전보건",
                    "지역사회 참여",
                    "공급망 관리"
                ],
                "G": [
                    "이사회 구조 및 독립성",
                    "윤리경영 및 컴플라이언스",
                    "리스크 관리",
                    "정보보안"
                ]
            },
            "tcfd_structure": {
                "governance": {
                    "board_oversight": [
                        "이사회 ESG 위원회 운영 (분기별)",
                        "기후변화 리스크 안건 상정 및 의결",
                        "외부 전문가 자문 활용"
                    ],
                    "management_role": [
                        "CEO 직속 ESG 전담 조직",
                        "CFO 재무적 영향 평가 책임",
                        "사업부별 리스크 관리 책임자 지정"
                    ]
                },
                "strategy": {
                    "risk_identification": [
                        "9가지 물리적 리스크 (하천범람, 태풍, 도시침수, 극심한고온, 해수면상승, 가뭄, 산사태, 산불, 한파)",
                        "전환 리스크 (탄소세, 규제 강화, 시장 변화)",
                        "기회 (녹색 금융, ESG 평가 개선)"
                    ],
                    "scenario_analysis": [
                        "SSP1-2.6: 지속가능 발전 (2100년 AAL 45%)",
                        "SSP2-4.5: 중간 경로 (2100년 AAL 68%)",
                        "SSP3-7.0: 지역 경쟁 (2100년 AAL 78%)",
                        "SSP5-8.5: 화석연료 집약 (2100년 AAL 92%)"
                    ],
                    "impact_assessment": [
                        "재무적 영향: AAL 기반 손실액 산정",
                        "운영적 영향: 사업 중단 일수, 복구 비용",
                        "자산 영향: 건물/설비 손상 비율"
                    ],
                    "response_strategy": [
                        "단기 (1-2년): 물리적 보강, 매뉴얼 수립",
                        "중기 (3-5년): 설비 이전, 친환경 전환",
                        "장기 (5년 이상): 사업장 재배치, 포트폴리오 재구성"
                    ]
                },
                "risk_management": {
                    "identification": "연 2회 정기 평가, 외부 데이터 활용 (S&P Climanomics 등)",
                    "assessment": "AAL 산정, 시나리오별 민감도 분석",
                    "integration": "전사 리스크 관리 시스템 통합, 재무계획 반영"
                },
                "metrics_targets": {
                    "scope1_2_3": "Scope 1: 234 tCO2e, Scope 2: 1,000 tCO2e, Scope 3: 5,432 tCO2e",
                    "aal_trend": "2024년 52.9% → 2030년 목표 40% 이하",
                    "re100": "2024년 45% → 2025년 60% → 2040년 100%",
                    "net_zero": "2040년 탄소중립 달성 목표"
                }
            },
            "materiality": {
                "high": {
                    "issues": ["기후변화 물리적 리스크", "탄소 배출", "에너지 전환"],
                    "threshold": "AAL 10% 이상 또는 재무 영향 100억원 이상",
                    "rationale": "사업 연속성 및 재무 건전성에 직접 영향"
                },
                "medium": {
                    "issues": ["공급망 리스크", "물 사용", "생물다양성"],
                    "threshold": "AAL 3-10% 또는 재무 영향 10-100억원",
                    "rationale": "간접적 영향 또는 중장기 리스크"
                },
                "low": {
                    "issues": ["폐기물 관리", "포장재 사용"],
                    "threshold": "AAL 3% 미만",
                    "rationale": "현재 영향 미미하나 모니터링 필요"
                }
            },
            "benchmark_KPIs": {
                "AAL": {
                    "name": "연평균손실률 (Average Annual Loss)",
                    "unit": "%",
                    "scope": "전체 포트폴리오 (8개 사업장)",
                    "calculation": "(예상 손실액 합계) / (자산 가치 합계) × 100",
                    "baseline": "2024년 52.9%",
                    "visualization": "선 그래프 (시나리오별 추이)"
                },
                "GHG_Scope1": {
                    "name": "직접 배출량",
                    "unit": "tCO2e",
                    "scope": "자사 직접 소유 배출원",
                    "calculation": "연료 사용량 × 배출계수",
                    "target": "2030년 50% 감축 (2020년 대비)",
                    "visualization": "막대 그래프 (연도별 배출량)"
                },
                "GHG_Scope2": {
                    "name": "간접 배출량 (전력)",
                    "unit": "tCO2e",
                    "scope": "구매 전력 사용",
                    "calculation": "전력 사용량 × 전력 배출계수",
                    "target": "RE100을 통한 단계적 감축",
                    "visualization": "적층 그래프 (재생/비재생 구분)"
                },
                "RE100_rate": {
                    "name": "재생에너지 사용 비율",
                    "unit": "%",
                    "scope": "전체 전력 사용량",
                    "calculation": "(재생에너지 사용량) / (총 전력 사용량) × 100",
                    "target": "2040년 100%",
                    "visualization": "진척도 게이지 차트"
                }
            },
            "scenario_templates": {
                "SSP1-2.6": {
                    "name": "지속가능 발전 시나리오",
                    "description": "파리협정 목표 달성, 전 지구적 협력, 저탄소 전환 성공",
                    "temp_rise": "2100년 +1.5°C",
                    "intro_pattern": "지속가능한 발전 경로를 가정한 SSP1-2.6 시나리오 하에서는...",
                    "comparison_phrase": "가장 낙관적인 시나리오임에도 불구하고",
                    "aal_2100": "45.0%"
                },
                "SSP2-4.5": {
                    "name": "중간 경로 시나리오",
                    "description": "현재 정책 기조 유지, 점진적 변화",
                    "temp_rise": "2100년 +2.0-2.5°C",
                    "intro_pattern": "중간 수준의 배출 경로인 SSP2-4.5 시나리오에서는...",
                    "comparison_phrase": "현재 추세가 지속될 경우",
                    "aal_2100": "68.1%"
                },
                "SSP5-8.5": {
                    "name": "화석연료 집약 시나리오",
                    "description": "높은 경제 성장, 화석연료 의존 지속, 기후 대응 실패",
                    "temp_rise": "2100년 +4.0°C 이상",
                    "intro_pattern": "최악의 경우인 SSP5-8.5 시나리오 하에서는...",
                    "comparison_phrase": "기후 대응에 실패할 경우",
                    "aal_2100": "92.5%"
                }
            },
            "hazard_template_blocks": {
                "river_flood": {
                    "kr_name": "하천 범람",
                    "description_pattern": "[사업장명]은 [하천명]으로부터 [거리]m 떨어져 있어 하천 범람 시 침수 위험에 노출되어 있습니다.",
                    "metrics": ["AAL (%)", "침수 깊이 (m)", "영향 범위 (m²)", "복구 기간 (일)"],
                    "financial_impact": "예상 손실액: [금액]억원 (AAL × 자산 가치)",
                    "operational_impact": "사업 중단 예상 기간: [일수]일, 복구 비용: [금액]억원",
                    "asset_impact": "건물 1층 및 지하층 침수, 전산 설비 손상 우려",
                    "mitigation_short": "배수 펌프 증설, 방수벽 설치, 중요 설비 고층 이전",
                    "mitigation_mid": "침수 방지 시스템 고도화, 비상 전원 확보",
                    "mitigation_long": "사업장 이전 검토, 기후 회복력 설계 반영"
                },
                "typhoon": {
                    "kr_name": "태풍",
                    "description_pattern": "[사업장명]은 해안 [거리]km 지역에 위치하여 태풍 시 강풍 및 폭우 피해 가능성이 있습니다.",
                    "metrics": ["AAL (%)", "최대 풍속 (m/s)", "강수량 (mm)", "피해액 (억원)"],
                    "financial_impact": "건물 외벽 및 창호 손상, 설비 파손 예상",
                    "operational_impact": "태풍 통과 후 점검 및 복구 기간: [일수]일",
                    "asset_impact": "외벽, 지붕, 창호, 외부 설비 손상 위험",
                    "mitigation_short": "내풍 성능 점검, 고정 강화, 비상 대응 훈련",
                    "mitigation_mid": "내풍 구조 보강, 방풍 설비 설치",
                    "mitigation_long": "건물 리모델링 시 강풍 기준 상향"
                },
                "urban_flood": {
                    "kr_name": "도시 침수",
                    "description_pattern": "도심 집중호우 시 배수 능력 부족으로 [사업장명] 지하층 침수 위험이 있습니다.",
                    "metrics": ["AAL (%)", "침수 확률", "지하층 규모 (m²)"],
                    "financial_impact": "지하 전산실 및 기계실 침수 시 막대한 복구 비용",
                    "operational_impact": "IT 시스템 중단, 데이터 손실 위험",
                    "asset_impact": "지하 중요 설비 (전산실, 발전기, 변전실) 침수",
                    "mitigation_short": "배수 펌프 증설, 침수 감지 센서 설치",
                    "mitigation_mid": "중요 설비 고층 이전, 방수문 설치",
                    "mitigation_long": "지하층 용도 변경 검토"
                }
            },
            "reusable_paragraphs": [
                "우리는 TCFD(Task Force on Climate-related Financial Disclosures) 권고안에 따라 기후변화 관련 재무 정보를 투명하게 공개하고 있습니다.",
                "4가지 SSP(Shared Socioeconomic Pathway) 시나리오를 기반으로 2100년까지의 물리적 리스크를 정량적으로 분석했습니다.",
                "8개 주요 사업장에 대한 포트폴리오 AAL(Average Annual Loss)은 2024년 기준 52.9%로 산정되었으며, 이는 연간 예상 손실액이 자산 가치의 절반 이상임을 의미합니다.",
                "이사회 산하 ESG 위원회는 분기별로 기후변화 리스크 평가 결과를 검토하며, 중요 사안은 이사회에 상정되어 의결됩니다.",
                "경영진은 기후변화 대응을 핵심 경영 과제로 인식하고, 2040년 Net Zero 달성을 위한 구체적인 실행 계획을 수립했습니다.",
                "9가지 물리적 리스크(하천범람, 태풍, 도시침수, 극심한고온, 해수면상승, 가뭄, 산사태, 산불, 한파) 중 AAL 기준 상위 5개 리스크(P1-P5)에 대해 심층 분석을 수행했습니다.",
                "각 리스크별로 재무적 영향, 운영적 영향, 자산 영향을 평가하고, 단기(1-2년), 중기(3-5년), 장기(5년 이상) 대응 전략을 마련했습니다.",
                "Scope 1, 2, 3 온실가스 배출량을 측정하고 있으며, 2030년까지 2020년 대비 50% 감축을 목표로 하고 있습니다.",
                "RE100(Renewable Energy 100%) 이니셔티브에 참여하여 2040년까지 사용 전력의 100%를 재생에너지로 전환할 계획입니다.",
                "기후변화 대응 역량 강화를 위해 향후 5년간 총 [금액]억원을 투자하며, 기후 회복력 강화와 탄소 감축을 동시에 추진합니다.",
                "리스크 평가는 6개월마다 재수행되며, 외부 전문 기관의 데이터와 방법론을 활용하여 객관성과 신뢰성을 확보합니다.",
                "AAL 10% 이상의 고위험 리스크는 경영진에 즉시 보고되며, 긴급 대응 계획이 수립됩니다.",
                "우리는 투명한 공시를 통해 투자자 및 이해관계자의 신뢰를 확보하고, ESG 경영을 지속적으로 강화하겠습니다."
            ]
        }, ensure_ascii=False, indent=2)


class RealLLM:
    """실제 OpenAI API 클라이언트"""

    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 환경변수를 설정해주세요")

        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("pip install openai 를 먼저 실행해주세요")

    async def ainvoke(self, prompt: str) -> str:
        """실제 OpenAI API 호출"""
        print(f"\n🚀 OpenAI API 호출 중... (모델: {self.model})")
        print(f"  - 프롬프트 길이: {len(prompt):,} 글자")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an elite ESG report structure analyst specializing in TCFD."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        result = response.choices[0].message.content

        print(f"✅ API 응답 완료")
        print(f"  - 응답 길이: {len(result):,} 글자")
        print(f"  - 토큰 사용: {response.usage.total_tokens:,} tokens")

        return result


async def main():
    """메인 실행"""
    print("\n" + "="*80)
    print("🧪 Node 1 Template Loading v2 - 실제 PDF 테스트")
    print("="*80)

    # PDF 파일 경로
    pdf_path = Path(__file__).parent / "2025_SK_Inc._Sustainability_Report_KOR.pdf"

    if not pdf_path.exists():
        print(f"\n❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")
        print(f"다음 경로에 PDF를 배치해주세요:")
        print(f"  {pdf_path}")
        return

    # 1. PDF 텍스트 추출
    print("\n" + "="*80)
    print("STEP 1: PDF 텍스트 추출")
    print("="*80)

    # 전체 PDF 읽기 (또는 최대 페이지 제한)
    max_pages = int(os.getenv("MAX_PAGES", "0")) or None  # 0이면 전체

    pdf_data = extract_text_from_pdf(str(pdf_path), max_pages=max_pages)

    # 2. TCFD 섹션 추출
    print("\n" + "="*80)
    print("STEP 2: TCFD 섹션 추출")
    print("="*80)

    tcfd_text = find_tcfd_section(pdf_data["full_text"])

    # 텍스트 미리보기
    print(f"\n📝 추출된 텍스트 미리보기 (처음 500자):")
    print("-" * 80)
    print(tcfd_text[:500])
    print("-" * 80)

    # 3. Node 1 실행
    print("\n" + "="*80)
    print("STEP 3: Node 1 Template Loading 실행")
    print("="*80)

    # 절대 import로 변경 (프로젝트 루트를 sys.path에 추가)
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from ai_agent.agents.tcfd_report.node_1_template_loading_v2 import TemplateLoadingNode

    # LLM 선택
    use_real = os.getenv("USE_REAL_LLM", "false").lower() == "true"

    if use_real:
        print("\n🚀 실제 OpenAI API 사용")
        llm = RealLLM()
    else:
        print("\n🤖 Mock LLM 사용 (빠른 테스트)")
        llm = MockLLM()

    # Node 1 초기화
    node = TemplateLoadingNode(llm_client=llm)

    # INIT 모드 실행
    print(f"\n▶ INIT 모드 실행 중...")

    result = await node.execute(
        company_name="SK Inc.",
        past_reports=[tcfd_text],
        mode="init"
    )

    # 4. 결과 분석
    print("\n" + "="*80)
    print("STEP 4: 결과 분석")
    print("="*80)

    template = result["report_template_profile"]

    print(f"\n✅ Node 1 실행 완료!")
    print(f"\n📊 결과 요약:")
    print(f"  - 필수 필드: {len(template)}/12")
    print(f"  - RAG 참조: {len(result.get('style_references', []))}개")
    print(f"  - Citations: {len(result.get('citations', []))}개")

    # 필드별 상세 분석
    print(f"\n📋 필드별 데이터 상세:")
    print("=" * 80)

    for key, value in template.items():
        if isinstance(value, dict):
            size = len(value)
            status = f"Dict ({size} keys)"
            filled = "✅" if size > 0 else "❌"

            print(f"\n{filled} [{key}] - {status}")

            # Dict 내용 미리보기
            if size > 0 and size <= 5:
                for k, v in list(value.items())[:3]:
                    v_str = str(v)[:60] + "..." if len(str(v)) > 60 else str(v)
                    print(f"    - {k}: {v_str}")
            elif size > 5:
                for k, v in list(value.items())[:2]:
                    v_str = str(v)[:60] + "..." if len(str(v)) > 60 else str(v)
                    print(f"    - {k}: {v_str}")
                print(f"    ... 외 {size - 2}개 항목")

        elif isinstance(value, list):
            size = len(value)
            status = f"List ({size} items)"
            filled = "✅" if size > 0 else "❌"

            print(f"\n{filled} [{key}] - {status}")

            # List 내용 미리보기
            if size > 0:
                for i, item in enumerate(value[:3], 1):
                    item_str = str(item)[:70] + "..." if len(str(item)) > 70 else str(item)
                    print(f"    {i}. {item_str}")
                if size > 3:
                    print(f"    ... 외 {size - 3}개 항목")

        else:
            filled = "✅" if value else "❌"
            print(f"\n{filled} [{key}] - {type(value).__name__}: {value}")

    # 5. 결과 저장
    print("\n" + "="*80)
    print("STEP 5: 결과 저장")
    print("="*80)

    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON 파일 저장
    json_file = output_dir / f"node1_pdf_result_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON 저장: {json_file}")

    # 추출된 텍스트 저장
    text_file = output_dir / f"pdf_extracted_text_{timestamp}.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(f"PDF 파일: {pdf_path.name}\n")
        f.write(f"총 페이지: {pdf_data['total_pages']}\n")
        f.write(f"추출 페이지: {pdf_data['extracted_pages']}\n")
        f.write(f"텍스트 길이: {len(tcfd_text):,} 글자\n")
        f.write("\n" + "="*80 + "\n")
        f.write("TCFD 섹션 텍스트:\n")
        f.write("="*80 + "\n\n")
        f.write(tcfd_text)

    print(f"✅ 텍스트 저장: {text_file}")

    # 템플릿 요약 레포트 생성
    summary_file = output_dir / f"template_summary_{timestamp}.md"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(f"# Node 1 Template Loading 결과 요약\n\n")
        f.write(f"**생성 일시:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**PDF 파일:** {pdf_path.name}\n")
        f.write(f"**회사명:** SK Inc.\n\n")

        f.write(f"## 📊 통계\n\n")
        f.write(f"- PDF 총 페이지: {pdf_data['total_pages']}\n")
        f.write(f"- 추출 페이지: {pdf_data['extracted_pages']}\n")
        f.write(f"- 텍스트 길이: {len(tcfd_text):,} 글자\n")
        f.write(f"- 필수 필드 완성: {len(template)}/12\n\n")

        f.write(f"## 📋 템플릿 구조\n\n")

        for key, value in template.items():
            f.write(f"### {key}\n\n")

            if isinstance(value, dict):
                f.write(f"**타입:** Dict ({len(value)} keys)\n\n")
                if len(value) > 0:
                    f.write("```json\n")
                    f.write(json.dumps(value, ensure_ascii=False, indent=2)[:500])
                    if len(json.dumps(value)) > 500:
                        f.write("\n... (truncated)")
                    f.write("\n```\n\n")

            elif isinstance(value, list):
                f.write(f"**타입:** List ({len(value)} items)\n\n")
                if len(value) > 0:
                    for i, item in enumerate(value[:5], 1):
                        f.write(f"{i}. {str(item)[:100]}\n")
                    if len(value) > 5:
                        f.write(f"... 외 {len(value) - 5}개\n")
                f.write("\n")

            else:
                f.write(f"**타입:** {type(value).__name__}\n")
                f.write(f"**값:** {value}\n\n")

    print(f"✅ 요약 저장: {summary_file}")

    # 완료
    print("\n" + "="*80)
    print("✅ 모든 작업 완료!")
    print("="*80)

    print(f"\n📁 생성된 파일:")
    print(f"  1. {json_file.name} - 전체 결과 (JSON)")
    print(f"  2. {text_file.name} - 추출된 텍스트")
    print(f"  3. {summary_file.name} - 요약 레포트 (Markdown)")

    if not use_real:
        print(f"\n💡 실제 OpenAI API로 테스트하려면:")
        print(f"   1. set OPENAI_API_KEY=your_key")
        print(f"   2. set USE_REAL_LLM=true")
        print(f"   3. python -m ai_agent.agents.tcfd_report.test_node1_with_pdf")


if __name__ == "__main__":
    asyncio.run(main())
