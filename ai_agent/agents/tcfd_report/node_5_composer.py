"""
Node 5: Composer & Template Generator (통합 노드)
Risk Management + Governance + Appendix + Metrics & Targets + Composer

작성일: 2025-12-14
버전: v01 (7-Node Structure)
"""

from typing import Dict, Any, List
from datetime import datetime


class ComposerNode:
    """
    Node 5: Composer & Template Generator

    통합 역할:
    1. Risk Management 섹션 (하드코딩 + Node 2-C 일부 삽입)
    2. Governance 섹션 (하드코딩)
    3. Appendix 섹션 (하드코딩)
    4. Metrics & Targets 섹션 (템플릿 + LineChartBlock 생성)
    5. 전체 조립 (Composer)
    6. 목차 생성 (TOC)
    7. 페이지 번호 매기기

    입력:
        - strategy_section: Dict (Node 3 출력)
        - scenarios: Dict (Node 2-A 출력)
        - mitigation_strategies: List[Dict] (Node 2-C 출력)
        - validated_sections: Dict (Node 4 출력)

    출력:
        - report: Dict (TCFDReport 객체)
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def execute(
        self,
        strategy_section: Dict,
        scenarios: Dict,
        mitigation_strategies: List[Dict],
        validated_sections: Dict
    ) -> Dict[str, Any]:
        """
        메인 실행 함수
        """
        # 1. Risk Management 섹션 생성
        risk_management_section = self._create_risk_management_section(mitigation_strategies)

        # 2. Governance 섹션 생성 (하드코딩)
        governance_section = self._create_governance_section()

        # 3. Metrics & Targets 섹션 생성 (AAL 추이 차트 포함)
        metrics_section = self._create_metrics_section(scenarios)

        # 4. Appendix 섹션 생성 (하드코딩)
        appendix_section = self._create_appendix_section()

        # 5. 전체 섹션 조립
        sections = [
            strategy_section,  # Node 3에서 생성 (Executive Summary 포함)
            governance_section,
            risk_management_section,
            metrics_section,
            appendix_section
        ]

        # 6. 목차 생성
        table_of_contents = self._generate_toc(sections)

        # 7. 메타데이터 생성
        meta = self._generate_meta(sections)

        # 8. 최종 보고서 조립
        report = {
            "report_id": f"tcfd_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "meta": meta,
            "table_of_contents": table_of_contents,
            "sections": sections
        }

        return {"report": report}

    def _create_risk_management_section(self, mitigation_strategies: List[Dict]) -> Dict:
        """
        Risk Management 섹션 생성 (하드코딩 + Node 2-C 일부 활용)
        """
        blocks = []

        # 3.1 리스크 식별 및 평가 프로세스 (하드코딩)
        blocks.append({
            "type": "text",
            "subheading": "3.1 리스크 식별 및 평가 프로세스",
            "content": (
                "우리는 다음과 같은 체계적인 프로세스를 통해 기후 관련 리스크를 식별하고 평가합니다:\n\n"
                "1. **리스크 식별**: 9개 물리적 리스크(하천범람, 태풍, 도시침수, 극심한고온, 해수면상승 등)를 "
                "IPCC 기후 시나리오(SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5) 기반으로 분석합니다.\n"
                "2. **리스크 평가**: H×E×V 프레임워크(Hazard × Exposure × Vulnerability)를 활용하여 "
                "각 사업장의 리스크를 정량화하고, AAL(Annual Average Loss)을 산출합니다.\n"
                "3. **우선순위 결정**: AAL 기준으로 Top 5 리스크를 선정하고, 재무적 영향도를 평가합니다."
            )
        })

        # 3.2 리스크 관리 통합 (하드코딩)
        blocks.append({
            "type": "text",
            "subheading": "3.2 전사적 리스크 관리 체계(ERM) 통합",
            "content": (
                "기후 관련 리스크는 우리의 전사적 리스크 관리(ERM) 체계에 통합되어 있습니다:\n\n"
                "- **리스크 위원회**: 분기별로 기후 리스크를 검토하고 대응 전략을 승인합니다.\n"
                "- **통합 보고**: 기후 리스크는 재무 리스크, 운영 리스크와 함께 통합 보고되며, "
                "경영진 및 이사회에 정기적으로 보고됩니다.\n"
                "- **모니터링**: 실시간 모니터링 시스템을 통해 기후 리스크 지표를 추적하고, "
                "임계값 초과 시 즉시 대응 절차가 작동합니다."
            )
        })

        # 3.3 주요 대응 전략 (Node 2-C 활용)
        # TODO: Node 2-C의 mitigation_strategies를 여기에 삽입
        if mitigation_strategies:
            mitigation_summary = "우리는 다음과 같은 기후 리스크 대응 전략을 수립하고 있습니다:\n\n"
            for i, strategy in enumerate(mitigation_strategies[:3], 1):  # Top 3만 삽입
                risk_name = strategy.get('risk_name', f'Risk {i}')
                short_term = strategy.get('short_term', '단기 전략 미정')
                mitigation_summary += f"{i}. **{risk_name}**: {short_term}\n"

            blocks.append({
                "type": "text",
                "subheading": "3.3 주요 대응 전략",
                "content": mitigation_summary
            })

        return {
            "section_id": "risk_management",
            "title": "3. Risk Management",
            "page_start": 12,  # TODO: 실제 페이지 계산
            "page_end": 14,
            "blocks": blocks
        }

    def _create_governance_section(self) -> Dict:
        """
        Governance 섹션 생성 (완전 하드코딩)
        """
        blocks = [
            {
                "type": "text",
                "subheading": "1.1 이사회의 감독",
                "content": (
                    "이사회는 기후 관련 리스크 및 기회에 대한 최종 책임을 지며, "
                    "다음과 같은 방식으로 감독합니다:\n\n"
                    "- **정기 보고**: 분기별로 기후 관련 리스크 및 대응 현황을 보고받습니다.\n"
                    "- **전략 승인**: 기후 관련 주요 투자 및 대응 전략을 검토하고 승인합니다.\n"
                    "- **성과 평가**: 기후 목표 달성 여부를 경영진 평가에 반영합니다."
                )
            },
            {
                "type": "text",
                "subheading": "1.2 경영진의 역할",
                "content": (
                    "경영진은 기후 관련 리스크 및 기회를 일상적인 경영 활동에 통합하며, "
                    "다음과 같은 역할을 수행합니다:\n\n"
                    "- **리스크 식별**: 사업부별로 기후 리스크를 식별하고 평가합니다.\n"
                    "- **대응 실행**: 이사회 승인 전략을 실행하고 진행 상황을 모니터링합니다.\n"
                    "- **보고 체계**: 정기적으로 이사회에 기후 관련 성과를 보고합니다."
                )
            }
        ]

        return {
            "section_id": "governance",
            "title": "1. Governance",
            "page_start": 3,  # TODO: 실제 페이지 계산
            "page_end": 4,
            "blocks": blocks
        }

    def _create_metrics_section(self, scenarios: Dict) -> Dict:
        """
        Metrics & Targets 섹션 생성 (템플릿 + LineChartBlock)
        """
        blocks = []

        # 4.1 AAL 지표 (Node 2-A 활용)
        blocks.append({
            "type": "text",
            "subheading": "4.1 주요 지표: 연평균 손실(AAL)",
            "content": (
                "우리는 기후 관련 재무 영향을 측정하기 위해 AAL(Annual Average Loss)을 핵심 지표로 사용합니다.\n\n"
                "AAL은 각 리스크가 발생할 확률과 예상 손실액을 곱하여 산출한 연평균 손실액으로, "
                "장기적인 재무 계획 수립에 활용됩니다."
            )
        })

        # 4.2 AAL 추이 차트 (LineChartBlock 생성)
        # TODO: Node 2-A의 scenarios 데이터를 활용하여 LineChartBlock 생성
        aal_chart = self._create_aal_trend_chart(scenarios)
        blocks.append(aal_chart)

        # 4.3 목표 (하드코딩)
        blocks.append({
            "type": "text",
            "subheading": "4.3 목표 및 이행 계획",
            "content": (
                "우리는 다음과 같은 기후 관련 목표를 설정하고 있습니다:\n\n"
                "1. **단기 목표 (2025-2030)**: AAL 10% 감소\n"
                "2. **중기 목표 (2030-2040)**: AAL 25% 감소\n"
                "3. **장기 목표 (2050)**: Net-Zero 달성\n\n"
                "이러한 목표는 정기적으로 검토되며, 필요 시 조정됩니다."
            )
        })

        return {
            "section_id": "metrics_targets",
            "title": "4. Metrics and Targets",
            "page_start": 15,  # TODO: 실제 페이지 계산
            "page_end": 18,
            "blocks": blocks
        }

    def _create_aal_trend_chart(self, scenarios: Dict) -> Dict:
        """
        AAL 추이 차트 생성 (LineChartBlock)
        """
        # TODO: 실제 Node 2-A의 scenarios 데이터를 활용
        # 임시 더미 데이터
        chart = {
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
                        "data": [52.9, 55.3, 58.7, 63.5, 68.1]
                    },
                    {
                        "name": "SSP3-7.0",
                        "color": "#FF9800",
                        "data": [52.9, 57.1, 65.2, 73.8, 85.3]
                    },
                    {
                        "name": "SSP5-8.5",
                        "color": "#F44336",
                        "data": [52.9, 58.7, 67.3, 78.2, 92.5]
                    }
                ]
            }
        }
        return chart

    def _create_appendix_section(self) -> Dict:
        """
        Appendix 섹션 생성 (완전 하드코딩)
        """
        blocks = [
            {
                "type": "text",
                "subheading": "A1. 시나리오 설명",
                "content": (
                    "본 보고서에서 사용한 기후 시나리오는 IPCC의 SSP(Shared Socioeconomic Pathways)를 기반으로 합니다:\n\n"
                    "- **SSP1-2.6**: 지속 가능한 발전 경로, 2100년 온도 상승 1.5-2°C\n"
                    "- **SSP2-4.5**: 중간 경로, 2100년 온도 상승 2-3°C\n"
                    "- **SSP3-7.0**: 지역 경쟁 경로, 2100년 온도 상승 3-4°C\n"
                    "- **SSP5-8.5**: 화석연료 의존 경로, 2100년 온도 상승 4-5°C"
                )
            },
            {
                "type": "text",
                "subheading": "A2. 리스크 정의",
                "content": (
                    "본 보고서에서 평가한 9개 물리적 리스크는 다음과 같습니다:\n\n"
                    "1. **하천범람**: 하천 범람으로 인한 침수 피해\n"
                    "2. **태풍**: 강풍 및 폭우로 인한 피해\n"
                    "3. **도시침수**: 내수 범람으로 인한 침수\n"
                    "4. **극심한고온**: 폭염으로 인한 운영 중단\n"
                    "5. **해수면상승**: 해안 침수 및 염해\n"
                    "6. **가뭄**: 수자원 부족\n"
                    "7. **산사태**: 산지 붕괴\n"
                    "8. **산불**: 산림 화재\n"
                    "9. **한파**: 극저온으로 인한 피해"
                )
            },
            {
                "type": "text",
                "subheading": "A3. 방법론",
                "content": (
                    "본 보고서는 다음과 같은 방법론을 사용했습니다:\n\n"
                    "- **H×E×V 프레임워크**: Hazard(위험), Exposure(노출), Vulnerability(취약성)를 곱하여 리스크를 정량화\n"
                    "- **AAL 산출**: 각 리스크의 발생 확률과 손실액을 곱하여 연평균 손실액 계산\n"
                    "- **시나리오 분석**: 4개 기후 시나리오별로 AAL 추이를 분석"
                )
            }
        ]

        return {
            "section_id": "appendix",
            "title": "Appendix",
            "page_start": 19,  # TODO: 실제 페이지 계산
            "page_end": 22,
            "blocks": blocks
        }

    def _generate_toc(self, sections: List[Dict]) -> List[Dict]:
        """
        목차 생성
        """
        toc = []
        for section in sections:
            toc.append({
                "title": section.get("title", "Unknown Section"),
                "page": section.get("page_start", 1)
            })
        return toc

    def _generate_meta(self, sections: List[Dict]) -> Dict:
        """
        메타데이터 생성
        """
        total_pages = max([s.get("page_end", 1) for s in sections])

        return {
            "title": "TCFD 보고서",
            "generated_at": datetime.now().isoformat(),
            "llm_model": "gpt-4-1106-preview",  # TODO: 실제 모델명으로 대체
            "site_count": 8,  # TODO: 실제 사업장 수로 대체
            "total_pages": total_pages,
            "total_aal": 163.8,  # TODO: 실제 AAL 합계로 대체
            "version": "2.0"
        }
