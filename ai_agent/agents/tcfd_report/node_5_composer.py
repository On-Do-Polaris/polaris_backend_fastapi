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
        appendix_section = self._create_appendix_section()
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
        Governance 섹션 생성 (SK ESG 2025 참조)

        Returns:
            Dict: Governance 섹션
        """
        blocks = [
            {
                "type": "text",
                "subheading": "1.1 이사회의 감독",
                "content": (
                    "이사회는 '전략·ESG위원회'를 통해 기후변화 전략 방향과 이행 계획을 검토하고 "
                    "리스크를 감독합니다.\n\n"
                    "**주요 감독 활동:**\n"
                    "- **정기 보고**: 분기별로 ESG 대응 현황, 공시/규제 동향 등의 안건을 논의합니다.\n"
                    "- **전략 승인**: 기후 관련 주요 투자 및 Net Zero 이행 계획을 검토하고 승인합니다.\n"
                    "- **성과 보상 연계**: CEO 및 임원의 KPI에 Net Zero, RE100, TCFD 정보 공개 성과를 반영하여 "
                    "보상과 연계합니다.\n\n"
                    "전략·ESG위원회는 사외이사를 중심으로 구성되어 있으며, "
                    "외부 전문가 자문을 통해 최신 기후 과학 및 정책 동향을 반영하고 있습니다."
                )
            },
            {
                "type": "text",
                "subheading": "1.2 경영진의 역할",
                "content": (
                    "경영진은 기후 관련 리스크 및 기회를 일상적인 경영 활동에 통합하며, "
                    "다음과 같은 역할을 수행합니다.\n\n"
                    "**경영진 체계:**\n"
                    "- **CEO**: 환경사업위원회 위원장을 겸직하며 주요 안건을 결정합니다.\n"
                    "- **CSO(Chief Sustainability Officer)**: 기후 리스크 관리 실무를 총괄합니다.\n"
                    "- **사업부 리스크 담당자**: CSO와 협력하여 통합 대응 전략을 실행합니다.\n\n"
                    "**보고 체계:**\n"
                    "- 분기별 기후 리스크 현황을 이사회에 보고합니다.\n"
                    "- 중대한 기후 이벤트 발생 시 즉시 보고 및 대응 절차를 가동합니다."
                )
            }
        ]

        return {
            "section_id": "governance",
            "title": "1. Governance",
            "page_start": 3,
            "page_end": 4,
            "blocks": blocks
        }

    def _create_risk_management_section(self, mitigation_strategies: List[Dict]) -> Dict:
        """
        Risk Management 섹션 생성 (하드코딩 + Node 2-C 일부 활용)

        Args:
            mitigation_strategies: Node 2-C 출력 (대응 전략)

        Returns:
            Dict: Risk Management 섹션
        """
        blocks = []

        # 3.1 리스크 식별 및 평가 프로세스
        blocks.append({
            "type": "text",
            "subheading": "3.1 리스크 식별 및 평가 프로세스",
            "content": (
                "우리는 다음과 같은 체계적인 프로세스를 통해 기후 관련 리스크를 식별하고 평가합니다:\n\n"
                "1. **리스크 식별**: 9개 물리적 리스크(하천 홍수, 태풍, 도시 홍수, 극심한 고온, 해수면 상승, 가뭄, 물부족, 산불, 극심한 한파)를 "
                "IPCC 기후 시나리오(SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5) 기반으로 분석합니다.\n"
                "2. **리스크 평가**: H×E×V 프레임워크(Hazard × Exposure × Vulnerability)를 활용하여 "
                "각 사업장의 리스크를 정량화하고, AAL(Annual Average Loss)을 산출합니다.\n"
                "3. **우선순위 결정**: AAL 기준으로 Top 5 리스크를 선정하고, 재무적 영향도를 평가합니다.\n\n"
                "이 프로세스는 연 1회 정기적으로 수행되며, 중대한 기후 이벤트 발생 시 즉시 재평가를 실시합니다."
            )
        })

        # 3.2 전사적 리스크 관리 체계(ERM) 통합
        blocks.append({
            "type": "text",
            "subheading": "3.2 전사적 리스크 관리 체계(ERM) 통합",
            "content": (
                "기후 관련 리스크는 전사적 리스크 관리(ERM) 체계에 통합되어 있습니다.\n\n"
                "**통합 관리 체계:**\n"
                "- **리스크 위원회**: 분기별로 기후 리스크를 검토하고 대응 전략을 승인합니다.\n"
                "- **통합 보고**: 기후 리스크는 재무 리스크, 운영 리스크와 함께 통합 보고되며, "
                "경영진 및 이사회에 정기적으로 보고됩니다.\n"
                "- **모니터링**: 실시간 모니터링 시스템을 통해 기후 리스크 지표를 추적하고, "
                "임계값 초과 시 즉시 대응 절차가 작동합니다.\n\n"
                "**내부 탄소 가격(ICP) 제도:**\n"
                "- 투자 의사결정 시 ICP(톤당 50,000원~100,000원)를 적용하여 기후 비용을 내재화합니다.\n"
                "- 신규 사업장 설립 시 기후 리스크 AAL과 ICP를 종합 평가하여 투자 적정성을 검토합니다.\n\n"
                "ERM 시스템은 기후 리스크를 재무적 중요도(AAL)와 전략적 중요도(사업 연속성)로 평가하여 우선순위를 결정합니다."
            )
        })

        # 3.3 주요 대응 전략 (Node 2-C 요약)
        if mitigation_strategies:
            mitigation_summary_parts = ["우리는 다음과 같은 기후 리스크 대응 전략을 수립하고 있습니다:\n"]

            for i, strategy in enumerate(mitigation_strategies[:3], 1):  # Top 3만 삽입
                risk_type = strategy.get('risk_type', f'risk_{i}')
                risk_name_kr = self.risk_name_mapping.get(risk_type, risk_type)
                priority = strategy.get('priority', '중간')
                short_term = strategy.get('short_term', [])

                mitigation_summary_parts.append(f"\n**P{i}. {risk_name_kr}** (우선순위: {priority})")
                if short_term:
                    mitigation_summary_parts.append(f"- {short_term[0]}")  # 첫 번째 단기 조치만
                else:
                    mitigation_summary_parts.append("- 대응 전략 수립 중")

            mitigation_summary = "\n".join(mitigation_summary_parts)

            blocks.append({
                "type": "text",
                "subheading": "3.3 주요 대응 전략 요약",
                "content": mitigation_summary + "\n\n상세한 대응 전략은 Strategy 섹션에서 확인하실 수 있습니다."
            })

        return {
            "section_id": "risk_management",
            "title": "3. Risk Management",
            "page_start": 13,
            "page_end": 15,
            "blocks": blocks
        }

    def _create_metrics_section(self, scenarios: Dict) -> Dict:
        """
        Metrics & Targets 섹션 생성 (템플릿 + LineChartBlock)

        Args:
            scenarios: Node 2-A 출력 (시나리오 분석 결과)

        Returns:
            Dict: Metrics & Targets 섹션
        """
        blocks = []

        # 4.1 AAL 지표
        blocks.append({
            "type": "text",
            "subheading": "4.1 주요 지표: 연평균 손실(AAL)",
            "content": (
                "우리는 기후 관련 재무 영향을 측정하기 위해 AAL(Annual Average Loss)을 핵심 지표로 사용합니다.\n\n"
                "AAL은 각 리스크가 발생할 확률과 예상 손실액을 곱하여 산출한 연평균 손실액으로, "
                "장기적인 재무 계획 수립 및 보험 전략 수립에 활용됩니다.\n\n"
                "**AAL 산출 방식:**\n"
                "- AAL = Σ (리스크 발생 확률 × 예상 손실액)\n"
                "- 9개 물리적 리스크에 대해 개별 AAL을 산출 후 포트폴리오 AAL 집계\n"
                "- 4개 기후 시나리오별로 2025년~2100년 AAL 추이 분석"
            )
        })

        # 4.2 AAL 추이 차트 (LineChartBlock 생성)
        aal_chart = self._create_aal_trend_chart(scenarios)
        blocks.append(aal_chart)

        # 4.3 목표 및 이행 계획
        blocks.append({
            "type": "text",
            "subheading": "4.3 목표 및 이행 계획",
            "content": (
                "다음과 같은 기후 관련 목표를 설정하고 이행하고 있습니다.\n\n"
                "**1. 단기 목표 (2026년)**\n"
                "- Top 5 리스크 AAL 10% 감소\n"
                "- 우선순위 대응 조치 실행 (침수 방지 시설, 비상 대응 매뉴얼)\n"
                "- 분기별 AAL 모니터링 및 진행 상황 보고\n\n"
                "**2. 중기 목표 (2030년)**\n"
                "- 포트폴리오 AAL 25% 감소\n"
                "- RE100 달성: 재생에너지 100% 사용\n"
                "- 구조적 리스크 저감 투자 (방수벽, 냉각 시스템 업그레이드)\n"
                "- 신규 사업장 기후 회복력 기준 적용\n\n"
                "**3. 장기 목표 (2040년)**\n"
                "- Net Zero 2040 달성: Scope 1, 2 온실가스 배출 넷제로\n"
                "- Scope 3 배출 50% 감축 (2019년 대비)\n"
                "- 고위험 사업장 재배치 또는 기후 적응 완료\n\n"
                "**4. 궁극적 목표 (2050년)**\n"
                "- 기후 중립 포트폴리오 달성\n"
                "- Scope 3 포함 전 가치사슬 넷제로\n"
                "- 탄소 네거티브 사업 모델 전환\n\n"
                "이러한 목표는 정기적으로 검토되며, IPCC 최신 보고서 및 국가 NDC 변화에 따라 조정됩니다."
            )
        })

        return {
            "section_id": "metrics_targets",
            "title": "4. Metrics and Targets",
            "page_start": 16,
            "page_end": 18,
            "blocks": blocks
        }

    def _create_aal_trend_chart(self, scenarios: Dict) -> Dict:
        """
        AAL 추이 차트 생성 (LineChartBlock)

        Args:
            scenarios: Node 2-A 출력 (포트폴리오 시나리오 데이터)

        Returns:
            Dict: LineChartBlock JSON
        """
        # Timeline: [2025, 2030, 2040, 2050, 2100]
        timeline = [2025, 2030, 2040, 2050, 2100]

        # 시나리오별 색상
        scenario_colors = {
            "ssp1_2.6": "#4CAF50",  # Green
            "ssp2_4.5": "#FFC107",  # Yellow
            "ssp3_7.0": "#FF9800",  # Orange
            "ssp5_8.5": "#F44336"   # Red
        }

        # 시나리오별 데이터 추출
        series = []
        for scenario_key in ["ssp1_2.6", "ssp2_4.5", "ssp3_7.0", "ssp5_8.5"]:
            if scenario_key in scenarios:
                scenario_data = scenarios[scenario_key]
                scenario_name_kr = scenario_data.get("scenario_name_kr", scenario_key.upper())
                aal_values = scenario_data.get("aal_values", [0] * len(timeline))

                series.append({
                    "name": scenario_name_kr,
                    "color": scenario_colors.get(scenario_key, "#999999"),
                    "data": aal_values[:len(timeline)]  # Timeline 길이에 맞춤
                })

        # Y축 최대값 계산 (가장 큰 AAL 값 기준)
        max_aal = 100.0
        if series:
            max_aal = max([max(s["data"]) for s in series if s["data"]]) * 1.1  # 10% 여유

        chart = {
            "type": "line_chart",
            "title": "포트폴리오 AAL 추이 (2025-2100)",
            "data": {
                "x_axis": {
                    "label": "연도",
                    "categories": timeline
                },
                "y_axis": {
                    "label": "AAL",
                    "min": 0,
                    "max": round(max_aal, 1),
                    "unit": "%"
                },
                "series": series
            }
        }

        return chart

    def _create_appendix_section(self) -> Dict:
        """
        Appendix 섹션 생성 (완전 하드코딩)

        Returns:
            Dict: Appendix 섹션
        """
        blocks = [
            {
                "type": "text",
                "subheading": "A1. 시나리오 설명",
                "content": (
                    "본 보고서에서 사용한 기후 시나리오는 IPCC의 SSP(Shared Socioeconomic Pathways)를 기반으로 합니다:\n\n"
                    "- **SSP1-2.6 (저탄소 시나리오)**: 지속 가능한 발전 경로, 2100년 온도 상승 1.5-2°C. "
                    "강력한 기후 정책과 재생에너지 전환으로 탄소 배출이 빠르게 감소하는 시나리오입니다.\n\n"
                    "- **SSP2-4.5 (중간 시나리오)**: 현재 정책 기조 유지, 2100년 온도 상승 2-3°C. "
                    "점진적인 기후 정책 강화와 기술 발전이 이루어지는 중간 경로 시나리오입니다.\n\n"
                    "- **SSP3-7.0 (높은 배출 시나리오)**: 지역 경쟁 및 분열 경로, 2100년 온도 상승 3-4°C. "
                    "기후 정책 협력 실패와 화석연료 의존 지속으로 배출이 증가하는 시나리오입니다.\n\n"
                    "- **SSP5-8.5 (최악 시나리오)**: 화석연료 의존 경로, 2100년 온도 상승 4-5°C. "
                    "기후 정책 부재와 화석연료 사용 급증으로 최대 배출이 발생하는 시나리오입니다."
                )
            },
            {
                "type": "text",
                "subheading": "A2. 리스크 정의",
                "content": (
                    "본 보고서에서 평가한 9개 물리적 리스크는 다음과 같습니다:\n\n"
                    "1. **하천 홍수 (River Flood)**: 하천 범람으로 인한 침수 피해\n"
                    "2. **태풍 (Typhoon)**: 강풍 및 폭우로 인한 피해\n"
                    "3. **도시 홍수 (Urban Flood)**: 내수 범람으로 인한 침수\n"
                    "4. **극심한 고온 (Extreme Heat)**: 폭염으로 인한 운영 중단 및 냉방 부하 증가\n"
                    "5. **해수면 상승 (Sea Level Rise)**: 해안 침수 및 염해\n"
                    "6. **가뭄 (Drought)**: 수자원 부족으로 인한 운영 차질\n"
                    "7. **물부족 (Water Stress)**: 장기적 물 공급 불안정\n"
                    "8. **산불 (Wildfire)**: 산림 화재로 인한 피해\n"
                    "9. **극심한 한파 (Extreme Cold)**: 극저온으로 인한 시설 동파 및 운영 중단"
                )
            },
            {
                "type": "text",
                "subheading": "A3. 방법론",
                "content": (
                    "본 보고서는 다음과 같은 방법론을 사용했습니다:\n\n"
                    "**1. H×E×V 프레임워크**\n"
                    "- Hazard(위험): 기후 이벤트의 강도 및 빈도\n"
                    "- Exposure(노출): 사업장의 지리적 위치 및 자산 규모\n"
                    "- Vulnerability(취약성): 물리적 방어 시설 및 대응 역량\n"
                    "- 종합 리스크 = H × E × V\n\n"
                    "**2. AAL 산출**\n"
                    "- 각 리스크의 발생 확률과 예상 손실액을 곱하여 연평균 손실액 계산\n"
                    "- 포트폴리오 AAL = Σ (사업장별 AAL × 자산 가중치)\n\n"
                    "**3. 시나리오 분석**\n"
                    "- 4개 기후 시나리오별로 2025년~2100년 AAL 추이 분석\n"
                    "- IPCC AR6 및 국가 기후 시나리오 데이터 활용\n\n"
                    "**4. 대응 전략 수립**\n"
                    "- Top 5 리스크에 대해 단기(2026), 중기(2026-2030), 장기(2020-2050년대) 대응 전략 수립\n"
                    "- 비용-효과 분석을 통한 우선순위 결정"
                )
            }
        ]

        return {
            "section_id": "appendix",
            "title": "5. Appendix",
            "page_start": 19,
            "page_end": 22,
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
