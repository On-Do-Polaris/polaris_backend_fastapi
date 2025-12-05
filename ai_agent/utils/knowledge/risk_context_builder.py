"""
파일명: risk_context_builder.py
최종 수정일: 2025-12-05
버전: v01
파일 개요: Risk Insight 데이터를 Agent별로 추출하고 포맷팅하는 Helper 클래스

주요 기능:
    1. 리스크 타입별 데이터 추출
    2. Agent별 필요한 컨텍스트 생성 (Impact Analysis, Strategy Generation, Report Composer)
    3. LLM 프롬프트용 텍스트 포맷팅
    4. Selective Knowledge Injection 패턴 지원

변경 이력:
    - v01 (2025-12-05): 초기 버전 생성
"""

import json
from typing import Dict, Any, List, Optional
from .risk_insight import risk_insight


class RiskContextBuilder:
    """
    Risk Insight 데이터를 Agent별로 추출하고 포맷팅하는 Helper 클래스

    Selective Knowledge Injection 패턴:
        - LLM에게 필요한 모든 정보를 제공
        - LLM이 스스로 필요한 정보를 선택하여 사용
        - 불필요한 정보는 무시
    """

    def __init__(self):
        self.risk_data = risk_insight

        # 리스크 타입 매핑 (한글 ↔ 영문)
        self.risk_type_map = {
            "극심한 고온": "extreme_heat",
            "극심한 한파": "extreme_cold",
            "산불": "wildfire",
            "가뭄": "drought",
            "물 부족": "water_stress",
            "해수면 상승": "sea_level_rise",
            "하천 홍수": "river_flood",
            "도시 홍수": "urban_flood",
            "태풍": "typhoon"
        }

        # 역방향 매핑
        self.risk_id_to_korean = {v: k for k, v in self.risk_type_map.items()}

    # =========================================================================
    # 기본 데이터 추출
    # =========================================================================

    def get_risk_data(self, risk_type: str) -> Optional[Dict[str, Any]]:
        """
        특정 리스크 타입의 전체 데이터 추출

        Args:
            risk_type: 리스크 타입 (한글 또는 영문 ID)

        Returns:
            리스크 데이터 딕셔너리 또는 None
        """
        # 영문 ID인 경우 한글로 변환
        if risk_type in self.risk_id_to_korean:
            risk_type = self.risk_id_to_korean[risk_type]

        return self.risk_data.get(risk_type)

    def get_aal_data(self, risk_type: str) -> Optional[Dict[str, Any]]:
        """
        특정 리스크 타입의 AAL 데이터만 추출

        Args:
            risk_type: 리스크 타입 (한글 또는 영문 ID)

        Returns:
            AAL 데이터 딕셔너리 또는 None
        """
        risk_data = self.get_risk_data(risk_type)
        if risk_data:
            return risk_data.get("aal_data", {})
        return None

    def get_risk_score_data(self, risk_type: str) -> Optional[Dict[str, Any]]:
        """
        특정 리스크 타입의 Risk Score 데이터만 추출

        Args:
            risk_type: 리스크 타입 (한글 또는 영문 ID)

        Returns:
            Risk Score 데이터 딕셔너리 또는 None
        """
        risk_data = self.get_risk_data(risk_type)
        if risk_data:
            return risk_data.get("risk_score_data", {})
        return None

    def get_all_risk_types(self) -> List[str]:
        """
        모든 리스크 타입 목록 반환 (한글명)

        Returns:
            리스크 타입 리스트
        """
        return list(self.risk_data.keys())

    # =========================================================================
    # Agent별 컨텍스트 생성
    # =========================================================================

    def get_impact_context(self, risk_types: List[str]) -> Dict[str, Any]:
        """
        Impact Analysis Agent (2번)를 위한 컨텍스트 생성

        영향 분석에 필요한 정보:
            - AAL 데이터 (재무 손실 추정)
            - Risk Score 데이터 (HEV 프레임워크)
            - 임계값 해석
            - 영향 범위

        Args:
            risk_types: 분석할 리스크 타입 리스트

        Returns:
            Impact Analysis용 컨텍스트 딕셔너리
        """
        context = {
            "purpose": "impact_analysis",
            "risks": {}
        }

        for risk_type in risk_types:
            risk_data = self.get_risk_data(risk_type)
            if not risk_data:
                continue

            context["risks"][risk_type] = {
                "risk_id": risk_data.get("risk_id"),
                "aal_data": risk_data.get("aal_data", {}),
                "risk_score_data": risk_data.get("risk_score_data", {}),
                "threshold_interpretation": self._extract_threshold_info(risk_data),
                "impact_scope": self._extract_impact_scope(risk_data)
            }

        return context

    def get_strategy_context(self, risk_types: List[str]) -> Dict[str, Any]:
        """
        Strategy Generation Agent (3번)를 위한 컨텍스트 생성

        전략 수립에 필요한 정보:
            - 리스크 정의 및 과학적 근거
            - 완화 키워드 (대응 방안 힌트)
            - AAL 데이터 (투자 우선순위)
            - 데이터 소스

        Args:
            risk_types: 전략 수립할 리스크 타입 리스트

        Returns:
            Strategy Generation용 컨텍스트 딕셔너리
        """
        context = {
            "purpose": "strategy_generation",
            "risks": {}
        }

        for risk_type in risk_types:
            risk_data = self.get_risk_data(risk_type)
            if not risk_data:
                continue

            context["risks"][risk_type] = {
                "risk_id": risk_data.get("risk_id"),
                "definition": self._extract_definitions(risk_data),
                "scientific_evidence": self._extract_scientific_evidence(risk_data),
                "mitigation_keywords": self._extract_mitigation_keywords(risk_data),
                "aal_summary": self._extract_aal_summary(risk_data),
                "data_sources": self._extract_data_sources(risk_data)
            }

        return context

    def get_report_context(self, risk_types: List[str]) -> Dict[str, Any]:
        """
        Report Composer Agent (4번)를 위한 컨텍스트 생성

        보고서 작성에 필요한 정보:
            - 전체 데이터 (포괄적 정보)
            - 단위 및 측정 기준
            - Bin 설명 (정성적 해석)
            - 영향 대상

        Args:
            risk_types: 보고서에 포함할 리스크 타입 리스트

        Returns:
            Report Composer용 컨텍스트 딕셔너리
        """
        context = {
            "purpose": "report_composition",
            "risks": {}
        }

        for risk_type in risk_types:
            risk_data = self.get_risk_data(risk_type)
            if not risk_data:
                continue

            context["risks"][risk_type] = {
                "risk_id": risk_data.get("risk_id"),
                "full_data": risk_data,  # 전체 데이터 제공
                "unit_info": self._extract_unit_info(risk_data),
                "bin_descriptions": self._extract_bin_descriptions(risk_data),
                "impacts_on": self._extract_impacts_on(risk_data)
            }

        return context

    def get_validation_context(self, risk_types: List[str]) -> Dict[str, Any]:
        """
        Validation Agent (5번)를 위한 컨텍스트 생성

        검증에 필요한 정보:
            - 데이터 소스 (신뢰성 확인)
            - 단위 정보 (정확성 확인)
            - 임계값 기준 (타당성 확인)

        Args:
            risk_types: 검증할 리스크 타입 리스트

        Returns:
            Validation용 컨텍스트 딕셔너리
        """
        context = {
            "purpose": "validation",
            "risks": {}
        }

        for risk_type in risk_types:
            risk_data = self.get_risk_data(risk_type)
            if not risk_data:
                continue

            context["risks"][risk_type] = {
                "risk_id": risk_data.get("risk_id"),
                "data_sources": self._extract_data_sources(risk_data),
                "unit_info": self._extract_unit_info(risk_data),
                "threshold_ranges": self._extract_threshold_info(risk_data)
            }

        return context

    # =========================================================================
    # LLM 프롬프트용 포맷팅
    # =========================================================================

    def format_for_prompt(
        self,
        context: Dict[str, Any],
        format_type: str = "json"
    ) -> str:
        """
        컨텍스트를 LLM 프롬프트에 삽입 가능한 텍스트로 포맷팅

        Args:
            context: get_*_context() 메서드로 생성한 컨텍스트
            format_type: 'json' 또는 'markdown'

        Returns:
            포맷팅된 텍스트
        """
        if format_type == "json":
            return json.dumps(context, indent=2, ensure_ascii=False)

        elif format_type == "markdown":
            return self._format_as_markdown(context)

        else:
            raise ValueError(f"Unsupported format_type: {format_type}")

    def _format_as_markdown(self, context: Dict[str, Any]) -> str:
        """컨텍스트를 마크다운 형식으로 포맷팅"""
        purpose = context.get("purpose", "unknown")
        risks = context.get("risks", {})

        md_text = f"## Risk Context for {purpose.replace('_', ' ').title()}\n\n"

        for risk_type, risk_info in risks.items():
            md_text += f"### {risk_type} ({risk_info.get('risk_id', 'N/A')})\n\n"

            for key, value in risk_info.items():
                if key == "risk_id":
                    continue

                md_text += f"**{key.replace('_', ' ').title()}:**\n"

                if isinstance(value, dict):
                    md_text += "```json\n"
                    md_text += json.dumps(value, indent=2, ensure_ascii=False)
                    md_text += "\n```\n\n"
                elif isinstance(value, list):
                    for item in value:
                        md_text += f"- {item}\n"
                    md_text += "\n"
                else:
                    md_text += f"{value}\n\n"

        return md_text

    # =========================================================================
    # 내부 Helper 메서드 (데이터 추출)
    # =========================================================================

    def _extract_definitions(self, risk_data: Dict[str, Any]) -> Dict[str, str]:
        """AAL 및 Risk Score 데이터에서 definition 추출"""
        definitions = {}

        aal_data = risk_data.get("aal_data", {})
        for var_name, var_info in aal_data.items():
            if "definition" in var_info:
                definitions[var_name] = var_info["definition"]

        risk_score_data = risk_data.get("risk_score_data", {})
        for var_name, var_info in risk_score_data.items():
            if "definition" in var_info:
                definitions[var_name] = var_info["definition"]

        return definitions

    def _extract_scientific_evidence(self, risk_data: Dict[str, Any]) -> List[str]:
        """Risk Score 데이터에서 scientific_evidence 추출"""
        evidence = []

        risk_score_data = risk_data.get("risk_score_data", {})
        for var_info in risk_score_data.values():
            if "scientific_evidence" in var_info:
                evidence.append(var_info["scientific_evidence"])

        return evidence

    def _extract_mitigation_keywords(self, risk_data: Dict[str, Any]) -> List[str]:
        """Risk Score 데이터에서 mitigation_keyword 추출"""
        keywords = []

        risk_score_data = risk_data.get("risk_score_data", {})
        for var_info in risk_score_data.values():
            if "mitigation_keyword" in var_info:
                keywords.extend(var_info["mitigation_keyword"])

        return list(set(keywords))  # 중복 제거

    def _extract_threshold_info(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Risk Score 데이터에서 threshold_interpretation 추출"""
        thresholds = {}

        risk_score_data = risk_data.get("risk_score_data", {})
        for var_name, var_info in risk_score_data.items():
            if "threshold_interpretation" in var_info:
                thresholds[var_name] = var_info["threshold_interpretation"]

        return thresholds

    def _extract_impact_scope(self, risk_data: Dict[str, Any]) -> List[str]:
        """AAL 데이터에서 impacts_on 추출"""
        impacts = []

        aal_data = risk_data.get("aal_data", {})
        for var_info in aal_data.values():
            if "impacts_on" in var_info:
                impacts.extend(var_info["impacts_on"])

        return list(set(impacts))  # 중복 제거

    def _extract_aal_summary(self, risk_data: Dict[str, Any]) -> Dict[str, str]:
        """AAL 데이터의 요약 정보 추출"""
        summary = {}

        aal_data = risk_data.get("aal_data", {})
        for var_name, var_info in aal_data.items():
            summary[var_name] = {
                "full_name": var_info.get("full_name", ""),
                "unit": var_info.get("unit", ""),
                "definition": var_info.get("definition", "")
            }

        return summary

    def _extract_data_sources(self, risk_data: Dict[str, Any]) -> List[str]:
        """모든 데이터 소스 추출"""
        sources = []

        aal_data = risk_data.get("aal_data", {})
        for var_info in aal_data.values():
            if "data_source" in var_info:
                sources.append(var_info["data_source"])

        risk_score_data = risk_data.get("risk_score_data", {})
        for var_info in risk_score_data.values():
            if "data_source" in var_info:
                sources.append(var_info["data_source"])

        return list(set(sources))  # 중복 제거

    def _extract_unit_info(self, risk_data: Dict[str, Any]) -> Dict[str, str]:
        """모든 변수의 단위 정보 추출"""
        units = {}

        aal_data = risk_data.get("aal_data", {})
        for var_name, var_info in aal_data.items():
            if "unit" in var_info:
                units[var_name] = var_info["unit"]

        risk_score_data = risk_data.get("risk_score_data", {})
        for var_name, var_info in risk_score_data.items():
            if "unit" in var_info:
                units[var_name] = var_info["unit"]

        return units

    def _extract_bin_descriptions(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """모든 변수의 bin_descriptions 추출"""
        bins = {}

        aal_data = risk_data.get("aal_data", {})
        for var_name, var_info in aal_data.items():
            if "bin_descriptions" in var_info:
                bins[var_name] = var_info["bin_descriptions"]

        risk_score_data = risk_data.get("risk_score_data", {})
        for var_name, var_info in risk_score_data.items():
            if "bin_descriptions" in var_info:
                bins[var_name] = var_info["bin_descriptions"]

        return bins

    def _extract_impacts_on(self, risk_data: Dict[str, Any]) -> List[str]:
        """AAL 데이터에서 impacts_on 추출"""
        impacts = []

        aal_data = risk_data.get("aal_data", {})
        for var_info in aal_data.values():
            if "impacts_on" in var_info:
                impacts.extend(var_info["impacts_on"])

        return list(set(impacts))  # 중복 제거
