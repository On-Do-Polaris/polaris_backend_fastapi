"""
Node 5: Composer & Template Generator v2
최종 수정일: 2025-12-15
버전: v2.0

개요:
    Node 5: Composer 노드 (전체 보고서 조립)

    통합 역할:
    1. Governance 섹션 생성 (하드코딩)
    2. Risk Management 섹션 생성 (하드코딩 + Node 2-C 요약)
    3. Metrics & Targets 섹션 생성 (LineChartBlock 포함)
    4. Appendix 섹션 생성 (하드코딩)
    5. 전체 섹션 조립 (Strategy + Governance + Risk Mgmt + Metrics + Appendix)
    6. 목차 생성
    7. 메타데이터 생성

주요 기능:
    1. TCFD 4대 섹션 생성 (Strategy는 Node 3에서 생성)
    2. LineChartBlock 생성 (AAL 추이 차트)
    3. 전체 보고서 조립
    4. 목차 및 메타데이터 생성

입력:
    - strategy_section: Dict (Node 3 출력)
    - scenarios: Dict (Node 2-A 출력)
    - mitigation_strategies: List[Dict] (Node 2-C 출력)
    - sites_data: List[Dict] (Node 0 출력)
    - impact_analyses: List[Dict] (Node 2-B 출력)

출력:
    - report: Dict (TCFDReport 객체)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class ComposerNode:
    """
    Node 5: Composer & Template Generator v2

    역할:
        - Governance, Risk Management, Metrics & Targets, Appendix 섹션 생성
        - 전체 보고서 조립
        - 목차 및 메타데이터 생성

    의존성:
        - Node 3 (Strategy Section) 완료 필수
        - Node 2-A, 2-C (차트 및 요약 데이터)
    """

    def __init__(self, llm_client=None):
        """
        Node 초기화

        Args:
            llm_client: ainvoke 메서드를 지원하는 LLM 클라이언트 (optional)
        """
        self.llm_client = llm_client

        # 리스크 한글 이름 매핑
        self.risk_name_mapping = {
            "extreme_heat": "극심한 고온",
            "extreme_cold": "극심한 한파",
            "wildfire": "산불",
            "drought": "가뭄",
            "water_stress": "물부족",
            "sea_level_rise": "해수면 상승",
            "river_flood": "하천 홍수",
            "urban_flood": "도시 홍수",
            "typhoon": "태풍"
        }

    async def execute(
        self,
        strategy_section: Dict,
        scenarios: Dict,
        mitigation_strategies: List[Dict],
        sites_data: List[Dict],
        impact_analyses: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        Args:
            strategy_section: Node 3 출력 (Strategy 섹션)
            scenarios: Node 2-A 출력 (시나리오 분석)
            mitigation_strategies: Node 2-C 출력 (대응 전략)
            sites_data: Node 0 출력 (사업장 데이터)
            impact_analyses: Node 2-B 출력 (optional, 메타데이터용)

        Returns:
            Dict: 전체 보고서
        """
        print("\n" + "="*80)
        print("▶ Node 5: Composer 전체 보고서 조립 시작")
        print("="*80)

        # 1. Governance 섹션 생성 (하드코딩)
        print("\n[Step 1/6] Governance 섹션 생성...")
        governance_section = self._create_governance_section()
        print(f"  ✅ Governance 섹션 생성 완료")

        # 2. Risk Management 섹션 생성 (하드코딩 + Node 2-C 요약)
        print("\n[Step 2/6] Risk Management 섹션 생성...")
        risk_management_section = self._create_risk_management_section(mitigation_strategies)
        print(f"  ✅ Risk Management 섹션 생성 완료")

        # 3. Metrics & Targets 섹션 생성 (LineChartBlock 포함)
        print("\n[Step 3/6] Metrics & Targets 섹션 생성...")
        metrics_section = self._create_metrics_section(scenarios)
        print(f"  ✅ Metrics & Targets 섹션 생성 완료")

        # 4. Appendix 섹션 생성 (하드코딩)
        print("\n[Step 4/6] Appendix 섹션 생성...")
        appendix_section = self._create_appendix_section(impact_analyses)
        print(f"  ✅ Appendix 섹션 생성 완료")

        # 5. 전체 섹션 조립 (순서: Governance → Strategy → Risk Mgmt → Metrics → Appendix)
        print("\n[Step 5/6] 전체 섹션 조립...")
        sections = [
            governance_section,
            strategy_section,  # Node 3에서 생성
            risk_management_section,
            metrics_section,
            appendix_section
        ]

        # 6. 목차 및 메타데이터 생성
        print("\n[Step 6/6] 목차 및 메타데이터 생성...")
        table_of_contents = self._generate_toc(sections)
        meta = self._generate_meta(sections, sites_data, impact_analyses)
        print(f"  ✅ 목차 및 메타데이터 생성 완료")

        # 7. 최종 보고서 조립
        report = {
            "report_id": f"tcfd_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "meta": meta,
            "table_of_contents": table_of_contents,
            "sections": sections
        }

        print("\n" + "="*80)
        print(f"✅ Node 5: Composer 완료 (총 {len(sections)}개 섹션, {meta['total_pages']}페이지)")
        print("="*80)

        return {"report": report}

    def _create_governance_section(self) -> Dict:
        """
        Governance 섹션 생성 (docs/hard_coding/Governance.md 참조)

        Returns:
            Dict: Governance 섹션
        """
        blocks = [
            # [subheading] 기후변화 이슈 관리 및 감독
            {
                "type": "text",
                "subheading": "기후변화 이슈 관리 및 감독",
                "content": "이사회 산하 전략·ESG위원회는 회사의 중장기 지속가능한 성장을 추진하기 위해 설치되었으며, 기후변화 관련 주제를 관리·감독하고 기후변화 대응 전략방향과 이행계획을 검토합니다. 기후변화 관련 주제는 전략·ESG위원회에서 연 1회 이상 논의됩니다. 2024년에는 기후변화 대응 현황, 기후 관련 국내외 규제/정책 동향 및 기후 공시 의무화 대응 방향성 등을 보고했습니다."
            },
            # [table_title] 위원 구성
            {
                "type": "table",
                "title": "위원 구성",
                "headers": [
                    {"text": "구분", "value": "category"},
                    {"text": "위원", "value": "members"}
                ],
                "items": [
                    {"category": "사외이사", "members": "이관영(위원장), 윤치원, 박현주, 김선희, 정종호"},
                    {"category": "사내이사", "members": "장용호"}
                ]
            },
            # [table_title] 2024년 기후변화 관련 보고 안건
            {
                "type": "table",
                "title": "2024년 기후변화 관련 보고 안건",
                "headers": [
                    {"text": "안건명", "value": "agenda"},
                    {"text": "개최 시기", "value": "date"},
                    {"text": "이사회 참석 현황", "value": "attendance"}
                ],
                "items": [
                    {"agenda": "ESG 대응 현황 및 향후 계획(지속가능경영보고서 포함)", "date": "2024년 9월 25일", "attendance": "6명/6명"},
                    {"agenda": "ESG 공시/규제 동향 및 대응 방향", "date": "2024년 9월 25일", "attendance": "6명/6명"}
                ]
            },
            # (마커 없음) 환경적 책임 텍스트
            {
                "type": "text",
                "content": "전략·ESG위원회는 회사의 중장기 지속가능한 성장을 추진하기 위해 설치되었으며, 기후변화 관련 주제를 관리·감독하고 기후변화 대응 전략방향과 이행계획을 검토합니다."
            },
            # [subheading] ESG 경영성과 모니터링 및 감독
            {
                "type": "text",
                "subheading": "ESG 경영성과 모니터링 및 감독",
                "content": "CEO는 SK그룹 최고 협의기구인 SUPEX추구협의회의 환경사업위원회 위원장을 겸직하고 있으며, 기후변화 대응을 비롯한 ESG 주요 안건을 논의 및 결정합니다. CEO는 기후변화 대응이 투자자, 고객, 정부 등 주요 이해관계자에게 미치는 영향을 중요하게 인식하고, 친환경 비즈니스 확장 및 비즈니스 모델을 발굴하여 전사적 협력을 주도하며, 기후변화 대응 성과가 금전적 보상으로 연결되도록 성과 모니터링 프로세스를 통한 인센티브 제도 관리 및 감독을 수행합니다. 또한 환경경영시스템(ISO 14001) 하에서 사업장의 환경 리스크 및 영향 평가, 내부 심사 결과를 정기적으로 보고받아 조직 성과를 통합 관리합니다."
            },
            # (마커 없음) 비재무적 Risk 관리 텍스트
            {
                "type": "text",
                "content": "CSO(Chief Sustainability Officer)는 ESG 및 지속가능성 이슈를 총괄하며, 기후변화 대응을 포함한 ESG 관련 목표 및 성과, ESG/기후 정보 공시 등을 관리·감독합니다."
            },
            # [subheading] 중장기 전략 및 연간 경영계획 검토
            {
                "type": "text",
                "subheading": "중장기 전략 및 연간 경영계획 검토",
                "content": "KPI에 기후변화 대응 관련 지표를 포함하고 있으며, 기후변화 대응 성과를 보상 정책과 연계하고 있습니다. 인센티브 제도를 통해 기후변화 대응 목표 달성을 촉진하고 기업의 지속 가능성을 높이며, ESG 경영 수준 향상에 기여합니다."
            },
            # [table_title] 기후변화 대응 성과 보상 체계
            {
                "type": "table",
                "title": "기후변화 대응 성과 보상 체계",
                "headers": [
                    {"text": "대상", "value": "target"},
                    {"text": "내용", "value": "description"},
                    {"text": "규모", "value": "scale"},
                    {"text": "KPI 지표", "value": "kpi"}
                ],
                "items": [
                    {
                        "target": "CEO",
                        "description": "Net Zero, RE100 등의 글로벌 기후변화 이니셔티브 참여, TCFD 정보 공개 등 주요 전략과제 추진 성과와 대외 이해관계자 평가 결과까지 인센티브 결정 반영",
                        "scale": "전사/조직/개인별 목표 대비 성과 평가에 따라 결정",
                        "kpi": "온실가스 감축 목표, 온실가스 감축 프로젝트, 에너지 효율 향상 목표, 공급망 Engagement, 기후변화 관련 지속가능성 Index 등"
                    },
                    {
                        "target": "CFO, ESG 추진 임원 및 전사 임원",
                        "description": "CEO의 KPI와 연계하여 전사 ESG 관리 책임에 관한 KPI 목표 설정",
                        "scale": "전사/조직/개인별 목표 대비 성과 평가에 따라 결정",
                        "kpi": "온실가스 감축 목표, 온실가스 감축 프로젝트, 에너지 효율 향상 목표, 공급망 Engagement, 기후변화 관련 지속가능성 Index 등"
                    },
                    {
                        "target": "구성원",
                        "description": "구성원 상여금은 연말 개인 성과 평가와 KPI 달성 결과에 따라 차등 지급되며, Net Zero 목표 달성 수준과 ESG 지표 달성 정도가 가감점 요소로 적용됨",
                        "scale": "전사/조직/개인별 목표 대비 성과 평가에 따라 결정",
                        "kpi": "온실가스 감축 목표, 온실가스 감축 프로젝트, 에너지 효율 향상 목표, 공급망 Engagement, 기후변화 관련 지속가능성 Index 등"
                    }
                ]
            },
            # [table_title] 기후변화 관련 KPI 주요 과제
            {
                "type": "table",
                "title": "기후변화 관련 KPI 주요 과제",
                "headers": [
                    {"text": "KPI 과제명", "value": "task"},
                    {"text": "상세", "value": "detail"}
                ],
                "items": [
                    {"task": "ESG 안건 이사회 보고 확대", "detail": "기후변화 대응 포함 ESG 안건 이사회(전략·ESG 위원회) 보고 확대"},
                    {"task": "ESG 대외 평가 Top 수준 유지", "detail": "기후변화 대응 포함 ESG 대외 평가 Top 수준 유지"},
                    {"task": "Net Zero 실행력 강화", "detail": "온실가스 배출량 감축 (2030년까지 Base year 대비 60% 감축)"}
                ]
            },
            # (마커 없음) 주요 활동 관리 텍스트
            {
                "type": "text",
                "content": "기후변화 대응과 관련된 주요 활동을 지속적으로 관리 및 감독하여 회사의 중장기 전략 달성을 지원합니다."
            }
        ]

        return {
            "section_id": "governance",
            "title": "Governance",
            "page_start": 3,
            "page_end": 6,
            "blocks": blocks
        }

    def _create_risk_management_section(self, mitigation_strategies: List[Dict]) -> Dict:
        """
        Risk Management 섹션 생성 (docs/hard_coding/risk_management.md 참조)

        Args:
            mitigation_strategies: Node 2-C 출력 (대응 전략) - 현재 미사용

        Returns:
            Dict: Risk Management 섹션
        """
        blocks = [
            # [subheading] 환경 리스크 통합관리
            {
                "type": "text",
                "subheading": "환경 리스크 통합관리",
                "content": "환경경영시스템(ISO 14001) 하에서 전사 통합 리스크 관리 체계(ISO 31000)와 연계, 기후 리스크를 사전 식별·평가하고 자가발전, 재생에너지 전환, 냉방 효율 개선 등 선제적 대응 수단을 활용한 예방 활동을 병행하는 통합 프로세스를 운영합니다. 연 1회 이상 내·외부 심사를 통해 리스크 평가의 적합성과 효과성을 검증합니다. 전사 리스크 관리 체계의 적격성을 확보하고 ESG 및 사업 리스크를 '식별-분석-대응-평가 및 개선' 프로세스를 기반으로 통합 관리합니다. 과학적 데이터 기반의 체계적인 기후 리스크 식별 및 모니터링 체계를 구축·운영합니다. 국내외 정책 환경과 기후 이슈, 산업 내 벤치마킹 사례, 이해관계자(고객사, 정부, 투자자 등) 요구사항 등을 종합적으로 반영합니다. 리스크 관리 협의체를 통해 발생 가능성, 심각성, 업무 영향도 등을 종합적으로 고려하여 리스크 성향(Risk Appetite) 설정 및 대응 전략을 수립합니다. 중대 환경·기후 리스크는 CEO 및 이사회에 보고하여 전사 차원의 대응 체계를 확보하고 주요 의사결정에 반영합니다."
            },
            # (마커 없음) 기후 리스크 관리 프로세스
            {
                "type": "text",
                "content": "전사 통합 리스크 관리체계와 연계하여 기후 리스크 관리 프로세스를 운영합니다. 이해관계자 중대성 평가에서 환경이슈 사항을 확인하고, 인권영향평가에서 환경권 대응 현황을 검토합니다. 준법경영시스템에서 환경 법규를 확인한 후, 환경 리스크 평가(ISO 14001)를 통해 내외부 이슈, 이해관계자 Needs, 준법사항을 바탕으로 리스크와 기회를 식별합니다. 기후변화 시나리오 기반(TCFD)의 BAU vs 1.5°C 시나리오를 활용하여 고유 리스크를 분석합니다. 전환리스크(정책, 법률, 기술, 시장, 명성)와 전환 기회(자원효율, 제품 시장 등), 물리적 리스크(급성, 만성)를 평가합니다. 현 대응수준 평가 후 잔여 리스크를 분석하고, 잔여 리스크 처리 및 효과성을 평가합니다. 신규 사업장(New Operation)을 포함하여 진행하며, 중대한 리스크에 대해서는 CEO 및 이사회에 보고합니다."
            },
            # [subheading] Value Chain 기후 리스크 관리
            {
                "type": "text",
                "subheading": "Value Chain 기후 리스크 관리",
                "content": "전환 리스크, 물리적 리스크 요인을 식별하고 Scope 3 배출량 관리와 제품·서비스의 환경성과 개선 활동을 통해 공급업체, 고객, 투자기업 대상의 기후 리스크 관리를 강화합니다. 환경 리스크 영향도 범위 확대를 통한 환경 리스크 관리 시스템 고도화 기반을 마련합니다."
            },
            # [table_title] Value Chain 기후 리스크 관리 현황
            {
                "type": "table",
                "title": "Value Chain 기후 리스크 관리 현황",
                "headers": [
                    {"text": "구분", "value": "category"},
                    {"text": "Upstream (공급업체)", "value": "upstream"},
                    {"text": "Downstream (투자기업)", "value": "downstream"}
                ],
                "items": [
                    {
                        "category": "활동 1",
                        "upstream": "협력사 ESG 행동강령 및 업체 ESG 수준진단 자문 등 협력사의 환경관리 수준 향상을 위한 지원활동 추진",
                        "downstream": "2022년부터 투자기업 대상으로 기후 리스크 노출도 관리 시작"
                    },
                    {
                        "category": "활동 2",
                        "upstream": "Upstream 주요배출원 HW/NW 장비 제조를 중점으로 온실가스 감축 Engagement 활동 시행",
                        "downstream": "감축목표 이행에 필요한 비용 및 시장에서의 가격/원가 구조를 반영한 실질 리스크 비용에 대한 영업 이익률 비교 등 재무적인 분석 진행"
                    },
                    {
                        "category": "활동 3",
                        "upstream": "2023년에는 기후 리스크 관리 체계 기반 친환경제품 인증 및 LCA 정보 및 기후리스크에 대한 BCP(사업연속성계획) 요구",
                        "downstream": "관리 범위 확대 및 방법론 강화를 통한 지속적인 Downstream 기후 리스크 관리 고도화 목표"
                    }
                ]
            }
        ]

        return {
            "section_id": "risk_management",
            "title": "Risk Management",
            "page_start": 13,
            "page_end": 15,
            "blocks": blocks
        }

    def _create_metrics_section(self, scenarios: Dict) -> Dict:
        """
        Metrics & Targets 섹션 생성 (docs/hard_coding/Metrics_Targets.md 참조)

        Args:
            scenarios: Node 2-A 출력 (시나리오 분석 결과) - 현재 미사용

        Returns:
            Dict: Metrics & Targets 섹션
        """
        blocks = [
            # [subheading] 온실가스 배출량 및 감축 목표
            {
                "type": "text",
                "subheading": "온실가스 배출량 및 감축 목표",
                "content": "SK주식회사는 Scope 1과 Scope 2 배출량을 관리하고, Scope 2 배출량은 지역기반과 시장기반으로 구분하여 산정합니다. 산정 기준의 신뢰성 및 정확도 확보를 위해 제3자 검증(연 1회) 수행합니다. 온실가스 배출량의 약 98%가 전력 사용(Scope 2)에서 발생하고 있으며, 그 중 데이터 센터가 전체 전력 사용량의 90% 이상을 차지합니다. 온실가스 배출량 및 에너지 사용량 산정 기준으로 '국가 온실가스 인벤토리 작성을 위한 IPCC 2006 가이드라인'과 '온실가스 배출권거래제의 배출량 보고 및 인증에 관한 지침'을 준수하며, 제3자 검증기관을 통한 적정성 검증을 수행합니다."
            },
            # [table_title] Scope 1 & 2 온실가스 배출량 추이
            {
                "type": "table",
                "title": "Scope 1 & 2 온실가스 배출량 추이",
                "headers": [
                    {"text": "구분", "value": "category"},
                    {"text": "2021년", "value": "y2021"},
                    {"text": "2022년", "value": "y2022"},
                    {"text": "2023년", "value": "y2023"},
                    {"text": "2024년", "value": "y2024"}
                ],
                "items": [
                    {"category": "Scope 1+2 배출량 (합계)", "y2021": "86,109", "y2022": "109,213", "y2023": "126,641", "y2024": "136,665"},
                    {"category": "Scope 1", "y2021": "1,432", "y2022": "1,431", "y2023": "1,434", "y2024": "1,283"},
                    {"category": "Scope 2 (지역기반)", "y2021": "84,677", "y2022": "107,782", "y2023": "125,207", "y2024": "135,382"},
                    {"category": "Scope 2 (시장기반)", "y2021": "-", "y2022": "-", "y2023": "102,604", "y2024": "102,626"}
                ],
                "footnote": "(단위: tCO₂eq)"
            },
            # (마커 없음) Scope 1 및 Scope 2 관리 강화
            {
                "type": "text",
                "content": "데이터 센터 전력 사용량의 재생에너지 전환 비중을 핵심지표로 설정하고, RE100 로드맵에 따라 매년 전환 비중 확대 중입니다. 재생에너지 조달 방법으로 자가발전을 최우선으로 고려하고, 데이터 센터 가용부지 내 태양광 자가발전 설비를 최대로 가동(2024년 0.83 GWh)합니다. 장기적으로 안정적인 재생 에너지 확보를 위해 PPA(Power Purchase Agreement) 도입을 검토 중이며, 국내 재생에너지 시장의 불확실성을 고려하여 조달 가능한 재생 에너지의 수단별 경제성 분석을 기반으로 한 최적의 조달 방안을 확보할 예정입니다. 데이터 센터의 지속적인 에너지 효율화를 위해 전력 소비량을 핵심지표로 설정하고, 매년 전력 수요량 예측 및 효율화 실적을 관리하고 있습니다."
            },
            # (마커 없음) Scope 3 배출량
            {
                "type": "text",
                "content": "SK주식회사는 업스트림(카테고리 1~7)과 다운스트림(카테고리 11, 12, 15)으로 구분하여 관리하고, Scope 3 배출량 정교화를 위해 제3자 검증 수행합니다. 출퇴근, 출장, 제품 사용 등 당사에 적용되는 모든 카테고리의 배출량을 산정합니다. Scope 3 배출량의 약 90%가 카테고리 15(투자 항목)에서 발생합니다. 산정 기준으로 GHG Protocol: Corporate Value Chain(Scope 3) Accounting and Reporting Standard를 적용합니다."
            },
            # [table_title] Scope 3 카테고리별 배출량 추이
            {
                "type": "table",
                "title": "Scope 3 카테고리별 배출량 추이",
                "headers": [
                    {"text": "구분", "value": "group"},
                    {"text": "카테고리", "value": "category"},
                    {"text": "2021년", "value": "y2021"},
                    {"text": "2022년", "value": "y2022"},
                    {"text": "2023년", "value": "y2023"},
                    {"text": "2024년", "value": "y2024"}
                ],
                "items": [
                    {"group": "합계", "category": "Scope 3 전체 배출량", "y2021": "13,391,021", "y2022": "11,529,818", "y2023": "13,860,200", "y2024": "14,210,016"},
                    {"group": "Upstream", "category": "카테고리 1 구매 제품 및 서비스", "y2021": "7,480", "y2022": "7,854", "y2023": "8,307", "y2024": "22,533"},
                    {"group": "Upstream", "category": "카테고리 2 자본재", "y2021": "2,588", "y2022": "1,840", "y2023": "1,701", "y2024": "351"},
                    {"group": "Upstream", "category": "카테고리 3 Scope 1, 2 미포함 연료 및 에너지", "y2021": "84", "y2022": "8,402", "y2023": "9,877", "y2024": "21,016"},
                    {"group": "Upstream", "category": "카테고리 6 출장", "y2021": "896", "y2022": "2,129", "y2023": "3,013", "y2024": "2,596"},
                    {"group": "Upstream", "category": "카테고리 7 직원 출퇴근", "y2021": "3,324", "y2022": "1,900", "y2023": "942", "y2024": "743"},
                    {"group": "Downstream", "category": "카테고리 11 제품의 사용", "y2021": "56,442", "y2022": "61,926", "y2023": "65,500", "y2024": "111,791"},
                    {"group": "Downstream", "category": "카테고리 15 투자", "y2021": "13,319,899", "y2022": "11,445,468", "y2023": "13,770,532", "y2024": "14,050,684"}
                ],
                "footnote": "(단위: tCO₂eq)"
            },
            # (마커 없음) Scope 3 관리 범위 확대 + Upstream Engagement
            {
                "type": "text",
                "content": "주요 Scope 3 카테고리에 대해 GHG Protocol 기준에 따라 산정하고, 제3자 검증을 수행합니다. 현재까지 총 10개 카테고리의 배출량을 산정하고 있으며, 지속적으로 관리 범위를 확대 중입니다. Scope 3 Category 1, 2에 해당하는 온실가스 배출량의 70% 이상이 HW/NW 장비 업체에서 발생합니다. 구매 제품의 LCA(제품 전 생애 주기 평가) 기반 배출량 산정을 위한 공급업체 데이터 수집 및 구매 관리 시스템 고도화를 추진합니다."
            },
            # (마커 없음) 온실가스 감축 목표 - Scope 1+2
            {
                "type": "text",
                "content": "SK주식회사는 'Net Zero 로드맵 목표 배출량'을 핵심 KPI로 설정하고, 매월 사업장별 온실가스 배출량을 점검합니다. 데이터센터 RE 전환율 확대, 냉방설비 고효율화 및 지열히트펌프 시스템 점검 검토 등 저탄소 전략 투자를 단계적으로 확대 중이며, 감축 기여량은 정기적으로 평가합니다."
            },
            # [table_title] Scope 1+2 감축 목표
            {
                "type": "table",
                "title": "Scope 1+2 감축 목표",
                "headers": [
                    {"text": "구분", "value": "category"},
                    {"text": "내용", "value": "content"}
                ],
                "items": [
                    {"category": "Long-Term Target", "content": "2040년 Scope 1+2 Net Zero 달성 (Base year 2023년)"},
                    {"category": "Near-Term Target", "content": "2025년 30% 달성 목표, 2030년(Near-Term) 60% 달성 목표 (Base year 2023년)"}
                ]
            },
            # (마커 없음) Scope 3 감축 목표 텍스트
            {
                "type": "text",
                "content": "2022년부터 자사에 해당하는 Scope 3 주요 카테고리(총 10개)에 대해 배출량을 산정하고 외부에 공시합니다. Scope 3 배출량 중 약 90%를 차지하는 투자기업, 구매 제품, 사용 및 폐기 과정에 대해 정량 진단, 공급사 설문 및 감축 목표 유도 등의 정밀 관리 체계를 운영합니다."
            },
            # [table_title] Scope 3 감축 목표
            {
                "type": "table",
                "title": "Scope 3 감축 목표",
                "headers": [
                    {"text": "구분", "value": "category"},
                    {"text": "내용", "value": "content"}
                ],
                "items": [
                    {"category": "Long-Term Target", "content": "2050년 Scope 3 총 배출량 2021년 대비 90% 감축 목표"},
                    {"category": "Near-Term Target", "content": "2030년까지 2021년 대비 Category15(투자) 배출량의 30% 감축"}
                ]
            },
            # (마커 없음) 글로벌 이니셔티브 + RE100
            {
                "type": "text",
                "content": "국제적 온실가스 감축 가속화에 동참하고자, 2020년 12월 Global RE100 Initiative 멤버십 가입하였습니다. 1.5℃ 파리기후협약 기준에 부합하는 RE100 2040 로드맵을 수립하였으며, Net Zero 2040 선언(Scope 1, 2 기준) 완료하였습니다. 2021년부터 매년 온실가스 감축 실적을 대외 공시하여 넷제로 목표관리 투명성 제고 노력하고 있습니다."
            },
            # [table_title] RE100 목표
            {
                "type": "table",
                "title": "RE100 목표",
                "headers": [
                    {"text": "구분", "value": "category"},
                    {"text": "내용", "value": "content"}
                ],
                "items": [
                    {"category": "Long-Term Target", "content": "2040년 전력 사용량 100%를 재생에너지 기반으로 전환"},
                    {"category": "Short-Term Target", "content": "2025년까지 전력 사용량 30% 재생에너지 기반으로 전환, 2030년까지 전력 사용량 60% 재생에너지 기반으로 전환"}
                ]
            },
            # [table_title] RE100 이행 성과
            {
                "type": "table",
                "title": "RE100 이행 성과",
                "headers": [
                    {"text": "연도", "value": "year"},
                    {"text": "목표", "value": "target"},
                    {"text": "실적", "value": "actual"}
                ],
                "items": [
                    {"year": "2023년", "target": "16%", "actual": "18.1%"},
                    {"year": "2024년", "target": "23%", "actual": "24.7%"},
                    {"year": "2025년", "target": "30%", "actual": "-"},
                    {"year": "2030년", "target": "60%", "actual": "-"},
                    {"year": "2040년", "target": "100%", "actual": "-"}
                ]
            },
            # (마커 없음) SK그룹 Net Zero 목표
            {
                "type": "text",
                "content": "2021년 SK는 국내 기업 최초로 그룹 차원의 Net Zero 선언, 국가 탄소중립 목표인 2050년보다 더 이른 시점(2050-)까지 온실가스 순 배출량 제로 달성 목표를 수립했습니다. 멤버사별 사업 특성을 반영하여 탈탄소화 전략을 추진하고 있으며, Net Zero 목표 이행 수준을 사별 KPI에 반영하여 경영진 성과평가·보상과 연계합니다. SK주식회사는 멤버사별 Net Zero 목표 이행 현황을 주기적으로 점검하고 있으며, 2024년 8월 SK그룹 차원에서 Net Zero 관리 시스템을 구축하여 Net Zero 데이터 관리 및 이행 성과 모니터링 수행합니다."
            }
        ]

        return {
            "section_id": "metrics_targets",
            "title": "Metrics and Targets",
            "page_start": 16,
            "page_end": 20,
            "blocks": blocks
        }

    def _create_appendix_section(self, impact_analyses: Optional[List[Dict]] = None) -> Dict:
        """
        Appendix 섹션 생성 (docs/hard_coding/appendix.md 참조)

        Args:
            impact_analyses: Node 2-B 출력 (optional)
                - None이거나 빈 리스트면 추가 데이터 미사용으로 판단

        Returns:
            Dict: Appendix 섹션
        """
        # 추가 데이터 사용 여부 확인
        has_additional_data = impact_analyses is not None and len(impact_analyses) > 0

        blocks = [
            # [subheading] 물리적 리스크 평가 방법론
            {
                "type": "text",
                "subheading": "물리적 리스크 평가 방법론",
                "content": "Polaris의 물리적 리스크 평가는 H×E×V (Hazard × Exposure × Vulnerability) 프레임워크를 기반으로 합니다. 각 리스크 유형별로 위험요소(Hazard), 노출도(Exposure), 취약성(Vulnerability)을 정량화하여 종합 리스크 점수를 산출합니다. 물리적 리스크 점수 = Hazard Score × Exposure Score × Vulnerability Score. 각 구성요소는 0-100점 척도로 평가되며, 최종 점수는 정규화되어 5단계 등급(Very Low, Low, Medium, High, Very High)으로 분류됩니다."
            },
            # [subheading] 9대 물리적 리스크 유형
            {
                "type": "text",
                "subheading": "9대 물리적 리스크 유형",
                "content": "TCFD 권고안에 따라 9가지 주요 물리적 리스크를 평가합니다."
            },
            # [table_title] 9대 물리적 리스크 유형 및 평가 지표
            {
                "type": "table",
                "title": "9대 물리적 리스크 유형 및 평가 지표",
                "headers": [
                    {"text": "리스크 유형", "value": "risk_type"},
                    {"text": "TCFD 분류", "value": "tcfd_class"},
                    {"text": "Hazard 지표", "value": "hazard"},
                    {"text": "Exposure 지표", "value": "exposure"},
                    {"text": "Vulnerability 지표", "value": "vulnerability"}
                ],
                "items": [
                    {"risk_type": "Extreme Heat (극한 고온)", "tcfd_class": "Chronic", "hazard": "Heat-related Climate Index (HCI)", "exposure": "건물 수, 인구 밀도", "vulnerability": "노인 인구 비율, 에어컨 보급률"},
                    {"risk_type": "Extreme Cold (극한 저온)", "tcfd_class": "Acute", "hazard": "Cold-related Climate Index (CCI)", "exposure": "건물 수, 인구 밀도", "vulnerability": "노인 인구 비율, 난방 시설"},
                    {"risk_type": "Wildfire (산불)", "tcfd_class": "Acute", "hazard": "Fire Weather Index (FWI)", "exposure": "산림 면적, 건물 수", "vulnerability": "산림 밀도, 소방 인프라"},
                    {"risk_type": "Drought (가뭄)", "tcfd_class": "Chronic", "hazard": "Standardized Precipitation-Evapotranspiration Index (SPEI)", "exposure": "농경지 면적, 인구", "vulnerability": "관개 시설, 물 저장 능력"},
                    {"risk_type": "Water Stress (물 부족)", "tcfd_class": "Chronic", "hazard": "Water Stress Index (WSI)", "exposure": "물 수요량, 인구", "vulnerability": "대체 수자원, 물 재활용률"},
                    {"risk_type": "Sea Level Rise (해수면 상승)", "tcfd_class": "Chronic", "hazard": "해수면 상승 높이", "exposure": "해안 저지대 면적, 인구", "vulnerability": "방조제, 배수 시스템"},
                    {"risk_type": "River Flood (하천 홍수)", "tcfd_class": "Acute", "hazard": "강수량, 하천 유량", "exposure": "범람원 내 자산, 인구", "vulnerability": "제방, 배수 시스템"},
                    {"risk_type": "Urban Flood (도시 홍수)", "tcfd_class": "Acute", "hazard": "극한 강수 빈도", "exposure": "불투수 면적, 건물 수", "vulnerability": "배수 인프라, 빗물 관리"},
                    {"risk_type": "Typhoon (태풍)", "tcfd_class": "Acute", "hazard": "Tropical Cyclone Index (TCI)", "exposure": "해안 지역 자산, 인구", "vulnerability": "건축물 강도, 대피 시설"}
                ]
            },
            # [subheading] TCFD 리스크 분류
            {
                "type": "text",
                "subheading": "TCFD 리스크 분류",
                "content": "TCFD는 물리적 리스크를 급성(Acute)과 만성(Chronic)으로 분류합니다."
            },
            # [table_title] TCFD 리스크 분류 체계
            {
                "type": "table",
                "title": "TCFD 리스크 분류 체계",
                "headers": [
                    {"text": "분류", "value": "classification"},
                    {"text": "한국어", "value": "korean"},
                    {"text": "특징", "value": "feature"},
                    {"text": "해당 리스크", "value": "risks"}
                ],
                "items": [
                    {"classification": "Acute", "korean": "급성 리스크", "feature": "단기간에 발생하는 극한 기상 이벤트", "risks": "Extreme Cold, Wildfire, River Flood, Urban Flood, Typhoon"},
                    {"classification": "Chronic", "korean": "만성 리스크", "feature": "장기간에 걸쳐 점진적으로 진행되는 기후 변화", "risks": "Extreme Heat, Drought, Water Stress, Sea Level Rise"}
                ]
            },
            # [subheading] 기후 시나리오
            {
                "type": "text",
                "subheading": "기후 시나리오",
                "content": "Polaris는 IPCC SSP (Shared Socioeconomic Pathways) 시나리오를 활용하여 미래 기후 리스크를 평가합니다. SSP1-2.6: 지속 가능한 발전 경로. 2100년까지 지구 평균 온도 상승을 1.5-2°C로 제한하는 시나리오입니다. 강력한 기후 정책과 저탄소 기술 확산을 가정합니다. SSP2-4.5: 중간 경로. 현재 추세가 지속되며, 일부 기후 정책이 시행되는 시나리오입니다. 2100년까지 약 2-3°C 상승을 전망합니다. SSP3-7.0: 지역 분열 경로. 국가 간 협력이 부족하고 기후 정책 시행이 미흡한 시나리오입니다. 2100년까지 약 3-4°C 상승을 전망합니다. SSP5-8.5: 화석연료 집약 발전 경로. 기후 정책 없이 화석연료 사용이 지속되는 최악의 시나리오입니다. 2100년까지 4°C 이상 상승을 전망합니다."
            },
            # [subheading] 데이터 출처
            {
                "type": "text",
                "subheading": "데이터 출처",
                "content": "물리적 리스크 평가에 사용된 데이터 출처는 다음과 같습니다."
            },
            # [table_title] 물리적 리스크 평가 데이터 출처
            {
                "type": "table",
                "title": "물리적 리스크 평가 데이터 출처",
                "headers": [
                    {"text": "데이터 유형", "value": "data_type"},
                    {"text": "출처", "value": "source"},
                    {"text": "설명", "value": "description"}
                ],
                "items": [
                    {"data_type": "기후 데이터", "source": "CMIP6 (Coupled Model Intercomparison Project Phase 6)", "description": "IPCC 6차 평가보고서 기반 기후 모델 데이터"},
                    {"data_type": "인구 데이터", "source": "WorldPop, GPWv4", "description": "고해상도 인구 분포 데이터"},
                    {"data_type": "토지 이용", "source": "ESA CCI Land Cover", "description": "글로벌 토지 피복 분류 데이터"},
                    {"data_type": "지형 데이터", "source": "SRTM DEM", "description": "90m 해상도 디지털 고도 모델"},
                    {"data_type": "해수면 상승", "source": "NASA Sea Level Projection", "description": "NASA 해수면 상승 시나리오"},
                    {"data_type": "강수 데이터", "source": "CHIRPS, ERA5", "description": "일별 강수량 데이터"},
                    {"data_type": "온도 데이터", "source": "ERA5, CMIP6", "description": "일별 최고/최저 기온 데이터"},
                    {"data_type": "산불 위험", "source": "GFWED", "description": "Global Fire Weather Database"}
                ]
            },
            # [subheading] 전환 리스크 평가 방법론
            {
                "type": "text",
                "subheading": "전환 리스크 평가 방법론",
                "content": "TCFD는 기후변화와 관련된 리스크를 물리적 리스크(Physical Risk)와 전환 리스크(Transition Risk) 두 가지로 분류합니다. 전환 리스크는 저탄소 경제로의 전환 과정에서 발생하는 리스크로, 정책 변화, 기술 발전, 시장 변화, 평판 리스크 등을 포함합니다. 전환 리스크 평가는 시나리오 분석을 통해 수행되며, IEA NZE (Net Zero Emissions), NGFS (Network for Greening the Financial System) 시나리오 등을 활용합니다."
            },
            # [table_title] 전환 리스크 유형 및 평가 요소
            {
                "type": "table",
                "title": "전환 리스크 유형 및 평가 요소",
                "headers": [
                    {"text": "리스크 유형", "value": "risk_type"},
                    {"text": "설명", "value": "description"},
                    {"text": "주요 평가 요소", "value": "factors"},
                    {"text": "영향", "value": "impact"}
                ],
                "items": [
                    {"risk_type": "정책 및 규제 리스크", "description": "탄소세, 배출권거래제, 환경 규제 강화", "factors": "탄소가격, 규제 준수 비용, 법적 책임", "impact": "운영 비용 증가, 자산 가치 하락"},
                    {"risk_type": "기술 리스크", "description": "저탄소 기술 발전과 기존 기술의 대체", "factors": "기술 경쟁력, R&D 투자, 기술 전환 비용", "impact": "좌초자산, 경쟁력 상실"},
                    {"risk_type": "시장 리스크", "description": "소비자 선호 변화, 원자재 가격 변동", "factors": "제품 수요 변화, 공급망 안정성", "impact": "매출 감소, 시장 점유율 하락"},
                    {"risk_type": "평판 리스크", "description": "이해관계자의 기후변화 대응 평가", "factors": "ESG 평가, 투자자 인식, 고객 신뢰", "impact": "브랜드 가치 하락, 투자 유치 어려움"}
                ]
            },
            # [subheading] 리스크 등급 분류 기준
            {
                "type": "text",
                "subheading": "리스크 등급 분류 기준",
                "content": "물리적 리스크 점수는 0-100점 범위로 산출되며, 5단계 등급으로 분류됩니다. 등급 분류는 각 리스크 유형별로 독립적으로 수행되며, 포트폴리오 전체의 종합 리스크 점수도 동일한 기준으로 분류됩니다."
            },
            # [table_title] 물리적 리스크 등급 분류 기준
            {
                "type": "table",
                "title": "물리적 리스크 등급 분류 기준",
                "headers": [
                    {"text": "등급", "value": "grade"},
                    {"text": "점수 범위", "value": "range"},
                    {"text": "설명", "value": "description"},
                    {"text": "권장 조치", "value": "action"}
                ],
                "items": [
                    {"grade": "Very Low", "range": "0-20", "description": "리스크가 매우 낮음. 기후변화 영향이 미미한 수준", "action": "정기 모니터링"},
                    {"grade": "Low", "range": "21-40", "description": "리스크가 낮음. 일부 영향 가능성 존재", "action": "예방적 대응 계획 수립"},
                    {"grade": "Medium", "range": "41-60", "description": "중간 수준의 리스크. 상당한 영향 예상", "action": "적응 전략 수립 및 이행"},
                    {"grade": "High", "range": "61-80", "description": "리스크가 높음. 심각한 영향 예상", "action": "즉각적인 적응 조치 필요"},
                    {"grade": "Very High", "range": "81-100", "description": "리스크가 매우 높음. 치명적 영향 가능성", "action": "긴급 대응 및 회복력 강화 필수"}
                ]
            },
            # [subheading] 용어 정의
            {
                "type": "text",
                "subheading": "용어 정의",
                "content": "기후 리스크 평가에 사용된 주요 용어를 정의합니다."
            },
            # [table_title] 주요 용어 정의
            {
                "type": "table",
                "title": "주요 용어 정의",
                "headers": [
                    {"text": "용어", "value": "term"},
                    {"text": "전체 명칭", "value": "full_name"},
                    {"text": "설명", "value": "description"}
                ],
                "items": [
                    {"term": "TCFD", "full_name": "Task Force on Climate-related Financial Disclosures", "description": "기후변화 재무정보공개 태스크포스. FSB 주도로 2015년 설립"},
                    {"term": "H×E×V", "full_name": "Hazard × Exposure × Vulnerability", "description": "리스크 평가 프레임워크. 위험요소, 노출도, 취약성의 곱으로 리스크 산출"},
                    {"term": "SSP", "full_name": "Shared Socioeconomic Pathways", "description": "공통 사회경제 경로. IPCC가 사용하는 기후 시나리오 체계"},
                    {"term": "AAL", "full_name": "Average Annual Loss", "description": "연평균 손실. 기후 리스크로 인한 예상 연간 재무 손실"},
                    {"term": "IPCC", "full_name": "Intergovernmental Panel on Climate Change", "description": "기후변화에 관한 정부간 협의체"},
                    {"term": "Acute Risk", "full_name": "급성 리스크", "description": "단기간에 발생하는 극한 기상 이벤트 (태풍, 홍수 등)"},
                    {"term": "Chronic Risk", "full_name": "만성 리스크", "description": "장기간에 걸쳐 점진적으로 진행되는 기후 변화 (온난화, 해수면 상승 등)"}
                ]
            },
            # [subheading] AAL (연평균 손실) 평가 방법론
            {
                "type": "text",
                "subheading": "AAL (연평균 손실) 평가 방법론",
                "content": "AAL (Annual Average Loss)은 기후변화 리스크로 인한 연평균 자산 손실률을 정량화하는 확률 기반 평가 지표입니다. Polaris는 9개 주요 기후 리스크에 대해 강도지표, 발생확률, 손상률, 취약성을 통합하여 사이트별 AAL을 산출합니다. AAL 평가는 취약성 점수를 반영한 맞춤형 손실 예측을 제공하며, SSP 시나리오 기반 미래 기후 시뮬레이션을 지원합니다. AAL 계산 공식은 AAL_r(j) = Σ P_r[i] × DR_r[i,j] × (1 - IR_r)입니다."
            },
            # [table_title] AAL 계산 대상 리스크
            {
                "type": "table",
                "title": "AAL 계산 대상 리스크",
                "headers": [
                    {"text": "번호", "value": "number"},
                    {"text": "리스크", "value": "risk"},
                    {"text": "코드명", "value": "code"},
                    {"text": "강도지표", "value": "indicator"},
                    {"text": "데이터 소스", "value": "source"}
                ],
                "items": [
                    {"number": "1", "risk": "극심한 고온", "code": "extreme_heat", "indicator": "WSDI (Warm Spell Duration Index)", "source": "KMA 연간 극값 지수"},
                    {"number": "2", "risk": "극심한 한파", "code": "extreme_cold", "indicator": "CSDI (Cold Spell Duration Index)", "source": "KMA 연간 극값 지수"},
                    {"number": "3", "risk": "산불", "code": "wildfire", "indicator": "FWI (Fire Weather Index)", "source": "KMA 기상 데이터"},
                    {"number": "4", "risk": "가뭄", "code": "drought", "indicator": "SPEI12 (12개월 누적)", "source": "KMA SPEI12"},
                    {"number": "5", "risk": "물부족", "code": "water_stress", "indicator": "WSI (Water Stress Index)", "source": "WAMIS + Aqueduct 4.0"},
                    {"number": "6", "risk": "내륙 홍수", "code": "river_flood", "indicator": "RX1DAY (연 최대 일강수량)", "source": "KMA RX1DAY"},
                    {"number": "7", "risk": "도시 집중 홍수", "code": "urban_flood", "indicator": "침수심", "source": "KMA RAIN80 + DEM"},
                    {"number": "8", "risk": "해수면 상승", "code": "sea_level_rise", "indicator": "침수심", "source": "CMIP6 zos"},
                    {"number": "9", "risk": "열대성 태풍", "code": "typhoon", "indicator": "누적 노출 지수 S_tc", "source": "KMA Best Track"}
                ]
            },
            # [table_title] AAL 핵심 파라미터
            {
                "type": "table",
                "title": "AAL 핵심 파라미터",
                "headers": [
                    {"text": "파라미터", "value": "parameter"},
                    {"text": "설명", "value": "description"},
                    {"text": "비고", "value": "note"}
                ],
                "items": [
                    {"parameter": "X_r(t)", "description": "강도지표 (Intensity Indicator)", "note": "리스크별 물리량 (WSDI, FWI, SPEI12 등)"},
                    {"parameter": "bin_r[i]", "description": "강도 구간", "note": "3-5단계 분류 (예: Low, Moderate, High, Very High, Extreme)"},
                    {"parameter": "P_r[i]", "description": "bin별 발생확률", "note": "KDE 또는 카운트 기반 계산"},
                    {"parameter": "DR_intensity_r[i]", "description": "bin별 기본 손상률", "note": "취약성 미반영 상태"},
                    {"parameter": "V_score_r(j)", "description": "취약성 점수", "note": "0-1 범위, Vulnerability Agent 출력"},
                    {"parameter": "F_vuln_r(j)", "description": "취약성 스케일 계수", "note": "0.7-1.3 범위 (30% 증감)"},
                    {"parameter": "DR_r[i,j]", "description": "최종 손상률", "note": "DR_intensity × F_vuln"},
                    {"parameter": "IR_r", "description": "보험 보전율", "note": "선택적 파라미터 (기본값 0)"},
                    {"parameter": "AAL_r(j)", "description": "연평균 손실률", "note": "최종 출력 지표"}
                ]
            }
        ]

        # 조건부: 추가 데이터 사용 시에만 문구 추가
        if has_additional_data:
            blocks.append({
                "type": "text",
                "content": "본 보고서에는 추가 데이터가 활용되었습니다."
            })

        # [table_title] 2025 SK주식회사 지속가능경영보고서 (항상 포함)
        blocks.append({
            "type": "table",
            "title": "2025 SK주식회사 지속가능경영보고서",
            "headers": [
                {"text": "항목", "value": "category"},
                {"text": "내용", "value": "content"}
            ],
            "items": [
                {"category": "발간", "content": "SK주식회사(www.sk-inc.com)"},
                {"category": "발간일자", "content": "2025년 8월 13일"},
                {"category": "보고서 제작", "content": "Brand관리담당(투자부문), ESG전략담당(사업부문)"},
                {"category": "문의", "content": "sustainability@sk.com"}
            ]
        })

        return {
            "section_id": "appendix",
            "title": "Appendix",
            "page_start": 21,
            "page_end": 25,
            "blocks": blocks
        }

    def _generate_toc(self, sections: List[Dict]) -> List[Dict]:
        """
        목차 생성

        Args:
            sections: 섹션 리스트

        Returns:
            List[Dict]: 목차 항목 리스트
        """
        toc = []
        for section in sections:
            toc.append({
                "title": section.get("title", "Unknown Section"),
                "page": section.get("page_start", 1)
            })
        return toc

    def _generate_meta(
        self,
        sections: List[Dict],
        sites_data: List[Dict],
        impact_analyses: Optional[List[Dict]] = None
    ) -> Dict:
        """
        메타데이터 생성

        Args:
            sections: 섹션 리스트
            sites_data: 사업장 데이터
            impact_analyses: 영향 분석 (optional, AAL 계산용)

        Returns:
            Dict: 메타데이터
        """
        # 총 페이지 수 계산
        total_pages = max([s.get("page_end", 1) for s in sections])

        # 총 AAL 계산
        total_aal = 0.0
        if impact_analyses:
            total_aal = sum([ia.get("total_aal", 0.0) for ia in impact_analyses])

        return {
            "title": "TCFD 보고서",
            "generated_at": datetime.now().isoformat(),
            "llm_model": "gpt-4o",  # TODO: 실제 모델명으로 대체
            "site_count": len(sites_data),
            "total_pages": total_pages,
            "total_aal": round(total_aal, 1),
            "version": "2.0"
        }
