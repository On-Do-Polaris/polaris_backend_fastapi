"""
파일명: node_2c_mitigation_strategies_v2.py
최종 수정일: 2025-12-15
버전: v2.0

개요:
    Node 2-C: Mitigation Strategies (대응 전략)

    Node 2-B의 영향 분석 결과를 기반으로
    Top 5 물리적 리스크에 대한 대응 전략을 3단계 시간축으로 생성합니다:
    1. 단기 조치 (향후 1년 - 2026년)
    2. 중기 조치 (향후 5년 - 2026/2027/2028/2029/2030년)
    3. 장기 조치 (2050년까지 10년 단위 평균 - 2020년대/2030년대/2040년대/2050년대)

주요 기능:
    1. Node 2-B 영향 분석 결과 기반 우선순위 결정
    2. Node 1 템플릿 참조하여 보고서 스타일 유지
    3. 병렬 LLM 분석 (5개 리스크 동시 처리, ~30초)
    4. TextBlock x5 생성 (P1~P5 대응 전략 텍스트)
    5. 실행 가능한 구체적 조치 제시

입력:
    - impact_analyses: List[dict] (Node 2-B 출력)
    - report_template: Dict (Node 1 출력)
    - company_context: Optional[dict] (회사 정보, 예산 등)

출력:
    - mitigation_strategies: List[dict] (5개 리스크별 대응 전략)
    - mitigation_blocks: List[TextBlock] (P1~P5 텍스트 블록)
    - implementation_roadmap: Dict (전체 실행 로드맵)

설계 철학 (Node 1과 동일):
    "처음부터 완벽하게 분석하면 재분석은 필요 없다"
    - EXHAUSTIVE 프롬프트로 실행 가능한 대응 전략 생성
    - 단기/중기/장기 균형있는 대응 방안
    - 비용 효율성 및 우선순위 고려

작성일: 2025-12-15 (v2 Refactoring)
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from .schemas import TextBlock


class MitigationStrategiesNode:
    """
    Node 2-C: 대응 전략 생성 노드 v2

    역할:
        - Top 5 물리적 리스크에 대한 대응 전략 생성
        - 단기/중기/장기 시간축으로 구조화
          * 단기: 향후 1년 (2026년)
          * 중기: 향후 5년 (2026-2030년)
          * 장기: 2050년까지 10년 단위 평균 (2020/2030/2040/2050년대)
        - Node 1 템플릿과 Node 2-B 영향 분석 결과 참조

    의존성:
        - Node 2-B 완료 필수 (영향 분석 결과 사용)
        - Node 1 완료 필수 (템플릿 참조)
    """

    def __init__(self, llm_client):
        """
        Node 초기화

        Args:
            llm_client: ainvoke 메서드를 지원하는 LLM 클라이언트
        """
        self.llm = llm_client

        # 리스크 한글 이름 매핑
        self.risk_name_mapping = {
            "river_flood": "하천 범람",
            "typhoon": "태풍",
            "urban_flood": "도시 침수",
            "extreme_heat": "극심한 고온",
            "sea_level_rise": "해수면 상승",
            "drought": "가뭄",
            "landslide": "산사태",
            "wildfire": "산불",
            "cold_wave": "한파"
        }

    async def execute(
        self,
        impact_analyses: List[Dict],
        report_template: Dict[str, Any],
        building_data: Optional[Dict[int, Dict]] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        company_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        Args:
            impact_analyses: Node 2-B 영향 분석 결과
            report_template: Node 1 보고서 템플릿
            building_data: BC Agent 결과 (site_id -> building analysis)
                          agent_guidelines 내 mitigation_recommendations 활용
            additional_data: AD Agent 결과 (Excel 추가 데이터)
                            site_specific_guidelines 활용
            company_context: 회사 컨텍스트 (optional)

        Returns:
            Dict containing:
                - mitigation_strategies: 대응 전략 리스트
                - mitigation_blocks: TextBlock x5
                - implementation_roadmap: 전체 실행 로드맵
        """
        print("\n" + "="*80)
        print("🔄 Node 2-C: Mitigation Strategies v2 실행 시작")
        print("="*80)

        # building_data 정보 출력
        if building_data:
            print(f"📊 Building Data 활용: {len(building_data)}개 사업장")
        else:
            print("⚠️  Building Data 없음 - 기본 분석 진행")

        # additional_data 정보 출력
        if additional_data and additional_data.get("site_specific_guidelines"):
            print(f"📋 Additional Data 활용: {len(additional_data.get('site_specific_guidelines', {}))}개 사업장")
        else:
            print("⚠️  Additional Data 없음")

        # Step 1: LLM 기반 대응 전략 생성 (병렬)
        print("\n[1/3] LLM 기반 대응 전략 생성 중 (병렬 처리)...")
        mitigation_strategies = await self._generate_strategies_parallel(
            impact_analyses,
            report_template,
            building_data,
            additional_data,
            company_context
        )
        print(f"✅ 대응 전략 생성 완료")

        # Step 2: TextBlock x5 생성
        print("\n[2/3] TextBlock x5 생성 중...")
        mitigation_blocks = self._create_mitigation_text_blocks(
            mitigation_strategies,
            report_template
        )
        print(f"✅ TextBlock 생성 완료")

        # Step 3: 전체 실행 로드맵 생성
        print("\n[3/3] 전체 실행 로드맵 생성 중...")
        implementation_roadmap = self._create_implementation_roadmap(mitigation_strategies)
        print(f"✅ 실행 로드맵 생성 완료")

        print("\n" + "="*80)
        print("✅ Node 2-C 실행 완료!")
        print("="*80)

        return {
            "mitigation_strategies": mitigation_strategies,
            "mitigation_blocks": mitigation_blocks,
            "implementation_roadmap": implementation_roadmap
        }

    async def _generate_strategies_parallel(
        self,
        impact_analyses: List[Dict],
        report_template: Dict,
        building_data: Optional[Dict[int, Dict]],
        additional_data: Optional[Dict[str, Any]],
        company_context: Optional[Dict]
    ) -> List[Dict]:
        """
        Top 5 리스크 병렬 대응 전략 생성 (~30초)

        Args:
            impact_analyses: 영향 분석 결과
            report_template: Node 1 템플릿
            building_data: BC Agent 결과
            additional_data: AD Agent 결과 (Excel 추가 데이터)
            company_context: 회사 컨텍스트

        Returns:
            List[Dict]: 5개 리스크별 대응 전략
        """
        tasks = [
            self._generate_single_risk_strategy(
                impact, report_template, building_data, additional_data, company_context
            )
            for impact in impact_analyses
        ]
        strategies = await asyncio.gather(*tasks)
        return strategies

    async def _generate_single_risk_strategy(
        self,
        impact: Dict,
        report_template: Dict,
        building_data: Optional[Dict[int, Dict]],
        additional_data: Optional[Dict[str, Any]],
        company_context: Optional[Dict]
    ) -> Dict:
        """
        단일 리스크 대응 전략 생성 (EXHAUSTIVE 프롬프트 + Building Data + Additional Data)

        Args:
            impact: 영향 분석 결과 (Node 2-B 출력)
            report_template: Node 1 템플릿
            building_data: BC Agent 결과 (site_id -> building analysis)
            additional_data: AD Agent 결과 (Excel 추가 데이터)
            company_context: 회사 컨텍스트

        Returns:
            Dict: {
                "risk_type": str,
                "rank": int,
                "short_term": List[str],
                "mid_term": List[str],
                "long_term": List[str],
                "priority": str,
                "estimated_cost": str,
                "expected_benefit": str
            }
        """
        risk_type = impact["risk_type"]
        risk_name_kr = self.risk_name_mapping.get(risk_type, risk_type)
        rank = impact["rank"]
        total_aal = impact["total_aal"]

        # Node 1 템플릿에서 참조할 정보 추출
        reusable_paragraphs = report_template.get("reusable_paragraphs", [])
        tone = report_template.get("tone", {})

        # 영향 분석 요약
        impact_summary = self._format_impact_summary(impact)

        # 건물 특성 기반 대응 전략 가이드 추출
        building_mitigation_guide = self._extract_building_mitigation_guide(building_data, risk_type)

        # 영향받는 사업장 목록 추출 (additional_data 컨텍스트용)
        affected_sites = impact.get("affected_sites", [])
        additional_context = self._extract_additional_data_context(additional_data, affected_sites)

        # EXHAUSTIVE 프롬프트 작성
        prompt = f"""
<ROLE>
You are an ELITE climate adaptation strategist specializing in TCFD disclosures.
Your task is to develop **actionable mitigation strategies** for **{risk_name_kr} ({risk_type})** risk.
</ROLE>

<CRITICAL_STRATEGY_REQUIREMENTS>

1. **SHORT-TERM ACTIONS (향후 1년 - 2026년)** - Immediate Response
   - Focus on quick wins and urgent vulnerabilities
   - Low-cost, high-impact measures that can be implemented within 1 year
   - Actions that can be implemented within current budget cycles
   - Timeline: 2026년 (1년 단위)
   - Examples: emergency response plans, monitoring systems, minor infrastructure improvements
   - Provide 3-5 specific actions

2. **MID-TERM ACTIONS (향후 5년 - 2026-2030년)** - Structural Improvements
   - Requires capital investment and planning
   - Infrastructure upgrades and retrofits over 5-year period
   - Process redesign and capacity building
   - Timeline: 2026/2027/2028/2029/2030년 (연도별 구체적 계획)
   - Examples: flood barriers, cooling system upgrades, site hardening
   - Provide 2-4 specific actions with year-by-year milestones

3. **LONG-TERM ACTIONS (2050년까지 10년 단위 평균)** - Transformational Change
   - Strategic decisions with long payback periods
   - Major capital investments or site relocations
   - Systemic resilience building across decades
   - Timeline: 2020년대/2030년대/2040년대/2050년대 (10년 단위 평균)
   - Examples: site relocation, climate-proof design, portfolio diversification
   - Provide 2-3 specific actions with decadal milestones

4. **PRIORITIZATION**
   - Assess priority as: "매우 높음", "높음", "중간"
   - Based on: AAL severity, affected assets, feasibility, cost-benefit ratio
   - Justify the priority level

5. **COST-BENEFIT ANALYSIS**
   - Estimate total investment needed (KRW billion won)
   - Break down by short/mid/long term
   - Estimate expected AAL reduction (%)
   - Calculate ROI or payback period if possible

6. **STAKEHOLDER COMMUNICATION**
   - Frame strategies in business terms (risk reduction, asset protection, ROI)
   - Address feasibility and resource requirements
   - Highlight co-benefits (e.g., energy efficiency, regulatory compliance)

</CRITICAL_STRATEGY_REQUIREMENTS>

<INPUT_DATA>

**Risk Information:**
- Risk Type: {risk_name_kr} ({risk_type})
- Rank: P{rank} (Top {rank} out of 9 risks)
- Total AAL: {total_aal}%

**Impact Analysis Summary:**
{impact_summary}

**Building-Specific Mitigation Recommendations:**
{building_mitigation_guide}

**Additional Site-Specific Context (from Excel data):**
{additional_context}

**Company Context:**
{self._format_company_context(company_context)}

**Reference Template (from previous reports):**

Tone: {json.dumps(tone, ensure_ascii=False, indent=2)}

Sample Paragraphs (for style reference):
{self._format_sample_paragraphs(reusable_paragraphs[:3])}

</INPUT_DATA>

<OUTPUT_REQUIREMENTS>

Generate a **comprehensive mitigation strategy** in Korean as a JSON object with:

{{
  "short_term": [
    "구체적 조치 1 (예: 침수 취약 지역 배수 펌프 설치)",
    "구체적 조치 2",
    ...
  ],
  "mid_term": [
    "구체적 조치 1 (예: 데이터센터 방수벽 2m 높이 증축)",
    "구체적 조치 2",
    ...
  ],
  "long_term": [
    "구체적 조치 1 (예: 침수 위험 높은 사업장 재배치 검토)",
    "구체적 조치 2",
    ...
  ],
  "priority": "매우 높음" or "높음" or "중간",
  "priority_justification": "우선순위 선정 근거 (2-3 문장)",
  "estimated_cost": "단기: X억원, 중기: Y억원, 장기: Z억원, 총: N억원",
  "expected_benefit": "AAL X%p 감소 예상, 자산 보호 효과 Y억원",
  "implementation_considerations": "실행 시 고려사항 (2-3 bullet points)"
}}

**Quality Standards:**
- Each action must be SPECIFIC and ACTIONABLE (not generic like "improve resilience")
- Include technical details where relevant (e.g., "install 500kW backup generator")
- Consider interdependencies between short/mid/long term actions
- Ensure cost estimates are realistic (based on typical infrastructure costs)

</OUTPUT_REQUIREMENTS>

<QUALITY_CHECKLIST>
Before submitting, verify:
- [ ] All 3 time horizons (short/mid/long) have specific actions
- [ ] Actions are concrete and implementation-ready
- [ ] Priority level is justified with clear reasoning
- [ ] Cost estimates are provided for all time horizons
- [ ] Expected benefits are quantified (AAL reduction, asset protection)
- [ ] Tone matches the reference template style
- [ ] Output is valid JSON format
</QUALITY_CHECKLIST>

Now, generate the mitigation strategy as a JSON object:
"""

        # LLM 호출
        try:
            response = await self.llm.ainvoke(prompt)

            # JSON 파싱 (마크다운 코드 블록 처리)
            json_str = self._extract_json_from_response(response)
            if json_str:
                parsed = json.loads(json_str)
                return {
                    "risk_type": risk_type,
                    "rank": rank,
                    "total_aal": total_aal,
                    "short_term": parsed.get("short_term", []),
                    "mid_term": parsed.get("mid_term", []),
                    "long_term": parsed.get("long_term", []),
                    "priority": parsed.get("priority", "중간"),
                    "priority_justification": parsed.get("priority_justification", ""),
                    "estimated_cost": parsed.get("estimated_cost", "산정 중"),
                    "expected_benefit": parsed.get("expected_benefit", "산정 중"),
                    "implementation_considerations": parsed.get("implementation_considerations", "")
                }
            else:
                # 텍스트 응답인 경우 파싱 시도
                return self._parse_text_strategy(response, risk_type, rank, total_aal)

        except Exception as e:
            print(f"⚠️  리스크 {risk_type} 전략 생성 실패: {e}")
            # Fallback
            return self._generate_fallback_strategy(impact)

    def _format_impact_summary(self, impact: Dict) -> str:
        """영향 분석 결과 요약"""
        lines = []

        lines.append("**재무적 영향:**")
        financial = self._ensure_string(impact.get("financial_impact", "N/A"))
        lines.append(financial[:200] + "..." if len(financial) > 200 else financial)
        lines.append("")

        lines.append("**운영적 영향:**")
        operational = self._ensure_string(impact.get("operational_impact", "N/A"))
        lines.append(operational[:200] + "..." if len(operational) > 200 else operational)
        lines.append("")

        lines.append("**자산 영향:**")
        asset = self._ensure_string(impact.get("asset_impact", "N/A"))
        lines.append(asset[:200] + "..." if len(asset) > 200 else asset)

        return "\n".join(lines)

    def _ensure_string(self, value: Any) -> str:
        """
        값을 문자열로 변환 (dict/list인 경우 JSON 문자열로)
        """
        if value is None:
            return "N/A"
        if isinstance(value, str):
            return value
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    def _format_company_context(self, company_context: Optional[Dict]) -> str:
        """회사 컨텍스트 포맷팅"""
        if not company_context:
            return "N/A"

        return json.dumps(company_context, ensure_ascii=False, indent=2)

    def _format_sample_paragraphs(self, paragraphs: List[str]) -> str:
        """샘플 문단 포맷팅"""
        if not paragraphs:
            return "N/A"

        formatted = []
        for i, para in enumerate(paragraphs[:3], 1):
            formatted.append(f"{i}. {para}")

        return "\n".join(formatted)

    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """
        LLM 응답에서 JSON 문자열 추출 (마크다운 코드 블록 처리)

        Args:
            response: LLM 응답 문자열

        Returns:
            Optional[str]: 추출된 JSON 문자열 또는 None
        """
        import re

        # 1. 마크다운 코드 블록에서 JSON 추출 (```json ... ``` 또는 ``` ... ```)
        json_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        matches = re.findall(json_block_pattern, response)

        if matches:
            # 첫 번째 코드 블록 내용 확인
            for match in matches:
                content = match.strip()
                if content.startswith('{') and content.endswith('}'):
                    return content

        # 2. 코드 블록 없이 직접 JSON인 경우
        response_stripped = response.strip()
        if response_stripped.startswith('{') and response_stripped.endswith('}'):
            return response_stripped

        # 3. 응답 내에서 { ... } 패턴 찾기
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, response)
        if match:
            return match.group(0)

        return None

    def _extract_building_mitigation_guide(
        self,
        building_data: Optional[Dict[int, Dict]],
        risk_type: str
    ) -> str:
        """건물 특성 기반 대응 전략 가이드 추출 (BC Agent agent_guidelines 활용)"""
        if not building_data:
            return "건물 특성 기반 가이드 없음 (기본 분석 수행)"

        guides = []

        for site_id, bd in building_data.items():
            agent_guidelines = bd.get("agent_guidelines", {})

            if not agent_guidelines:
                continue

            # mitigation_recommendations 섹션 추출 (BC Agent v08 형식: 딕셔너리 배열)
            mitigation_recs = agent_guidelines.get("mitigation_recommendations", {})
            if mitigation_recs:
                site_name = bd.get("site_name", f"Site {site_id}")
                guide_parts = [f"**{site_name}** (구조등급: {bd.get('structural_grade', 'N/A')}):"]

                # 단기 권장사항 (딕셔너리 배열 또는 문자열 배열 호환)
                short_term = mitigation_recs.get("short_term", [])
                if short_term:
                    actions = [
                        item.get("action", item) if isinstance(item, dict) else item
                        for item in short_term[:3]
                    ]
                    guide_parts.append(f"  - 단기 권장: {', '.join(actions)}")

                # 중기 권장사항
                mid_term = mitigation_recs.get("mid_term", [])
                if mid_term:
                    actions = [
                        item.get("action", item) if isinstance(item, dict) else item
                        for item in mid_term[:3]
                    ]
                    guide_parts.append(f"  - 중기 권장: {', '.join(actions)}")

                # 장기 권장사항
                long_term = mitigation_recs.get("long_term", [])
                if long_term:
                    actions = [
                        item.get("action", item) if isinstance(item, dict) else item
                        for item in long_term[:3]
                    ]
                    guide_parts.append(f"  - 장기 권장: {', '.join(actions)}")

                guides.append("\n".join(guide_parts))

        if not guides:
            return "건물 특성 기반 가이드 없음 (기본 분석 수행)"

        return "\n\n".join(guides[:5])  # 최대 5개 사업장

    def _extract_additional_data_context(
        self,
        additional_data: Optional[Dict[str, Any]],
        affected_sites: List[Dict]
    ) -> str:
        """
        Excel 추가 데이터에서 사업장별 컨텍스트 추출 (AD Agent site_specific_guidelines 활용)

        Args:
            additional_data: AD Agent 결과
            affected_sites: 영향받는 사업장 목록 (site_id, site_name 포함)

        Returns:
            str: LLM 프롬프트에 삽입할 추가 컨텍스트 텍스트
        """
        if not additional_data:
            return "추가 데이터 없음"

        # AD Agent 출력에서 site_specific_guidelines 추출
        site_guidelines = additional_data.get("site_specific_guidelines", {})

        if not site_guidelines:
            return "추가 데이터 없음"

        context_parts = []

        # 영향받는 사업장들에 대해서만 가이드라인 추출
        for site_info in affected_sites:
            site_id = site_info.get("site_id")
            site_name = site_info.get("site_name", f"Site {site_id}")

            # site_id를 키로 조회 (int 또는 str 모두 처리)
            guideline = site_guidelines.get(site_id) or site_guidelines.get(str(site_id))

            if guideline:
                guideline_text = guideline.get("guideline", "")
                key_insights = guideline.get("key_insights", [])

                site_context = f"**{site_name}**:\n"
                if guideline_text:
                    # 가이드라인 텍스트가 너무 길면 축약
                    if len(guideline_text) > 500:
                        site_context += f"{guideline_text[:500]}...\n"
                    else:
                        site_context += f"{guideline_text}\n"

                if key_insights:
                    site_context += f"핵심 인사이트: {', '.join(key_insights[:3])}\n"

                context_parts.append(site_context)

        if not context_parts:
            return "영향받는 사업장에 대한 추가 데이터 없음"

        return "\n".join(context_parts)

    def _parse_text_strategy(self, response: str, risk_type: str, rank: int, total_aal: float) -> Dict:
        """텍스트 응답을 구조화된 전략으로 파싱"""
        # 간단한 키워드 기반 파싱
        return {
            "risk_type": risk_type,
            "rank": rank,
            "total_aal": total_aal,
            "short_term": ["텍스트 파싱 필요"],
            "mid_term": ["텍스트 파싱 필요"],
            "long_term": ["텍스트 파싱 필요"],
            "priority": "중간",
            "priority_justification": "",
            "estimated_cost": "산정 중",
            "expected_benefit": "산정 중",
            "implementation_considerations": ""
        }

    def _generate_fallback_strategy(self, impact: Dict) -> Dict:
        """LLM 실패 시 기본 대응 전략 생성"""
        risk_type = impact["risk_type"]
        risk_name_kr = self.risk_name_mapping.get(risk_type, risk_type)
        rank = impact["rank"]
        total_aal = impact["total_aal"]

        return {
            "risk_type": risk_type,
            "rank": rank,
            "total_aal": total_aal,
            "short_term": [
                f"{risk_name_kr} 리스크 모니터링 시스템 구축",
                "비상 대응 매뉴얼 수립",
                "취약 지점 긴급 점검"
            ],
            "mid_term": [
                "물리적 방어 시설 설치",
                "설비 보강 공사 실시"
            ],
            "long_term": [
                "장기적 리스크 저감 계획 수립",
                "기후 회복력 강화 투자"
            ],
            "priority": "높음" if rank <= 2 else "중간",
            "priority_justification": f"Top {rank} 리스크로 식별되어 우선 대응이 필요합니다.",
            "estimated_cost": "산정 중",
            "expected_benefit": f"AAL {total_aal}% 리스크 저감",
            "implementation_considerations": "예산 확보 및 실행 계획 수립 필요"
        }

    def _create_mitigation_text_blocks(
        self,
        mitigation_strategies: List[Dict],
        report_template: Dict
    ) -> List[Dict]:
        """
        P1~P5 대응 전략 TextBlock 생성

        Args:
            mitigation_strategies: 대응 전략 리스트
            report_template: Node 1 템플릿

        Returns:
            List[Dict]: TextBlock x5
        """
        mitigation_blocks = []

        for i, strategy in enumerate(mitigation_strategies, 1):
            risk_type = strategy.get("risk_type", "Unknown")
            risk_name_kr = self.risk_name_mapping.get(risk_type, risk_type)
            total_aal = strategy.get("total_aal", 0)

            # 대응 전략 내용 조합
            content_parts = []

            # 우선순위 및 근거
            priority = self._ensure_string(strategy.get("priority", "중간"))
            priority_justification = self._ensure_string(strategy.get("priority_justification", ""))
            content_parts.append(f"**우선순위:** {priority}")
            if priority_justification:
                content_parts.append(priority_justification)
            content_parts.append("")

            # 예상 비용 및 효과
            estimated_cost = self._ensure_string(strategy.get("estimated_cost", "산정 중"))
            expected_benefit = self._ensure_string(strategy.get("expected_benefit", "산정 중"))
            content_parts.append(f"**예상 비용:** {estimated_cost}")
            content_parts.append(f"**예상 효과:** {expected_benefit}")
            content_parts.append("")

            # 단기 조치
            content_parts.append("### 단기 조치 (향후 1년 - 2026년)")
            short_term = strategy.get("short_term", [])
            if short_term:
                for action in short_term:
                    content_parts.append(f"- {self._ensure_string(action)}")
            else:
                content_parts.append("- 검토 중")
            content_parts.append("")

            # 중기 조치
            content_parts.append("### 중기 조치 (향후 5년 - 2026-2030년)")
            mid_term = strategy.get("mid_term", [])
            if mid_term:
                for action in mid_term:
                    content_parts.append(f"- {self._ensure_string(action)}")
            else:
                content_parts.append("- 검토 중")
            content_parts.append("")

            # 장기 조치
            content_parts.append("### 장기 조치 (2050년까지 10년 단위)")
            long_term = strategy.get("long_term", [])
            if long_term:
                for action in long_term:
                    content_parts.append(f"- {self._ensure_string(action)}")
            else:
                content_parts.append("- 검토 중")
            content_parts.append("")

            # 실행 고려사항
            impl_considerations = self._ensure_string(strategy.get("implementation_considerations", ""))
            if impl_considerations:
                content_parts.append("### 실행 시 고려사항")
                content_parts.append(impl_considerations)

            content = "\n".join(content_parts)

            # TextBlock 생성
            text_block = {
                "type": "text",
                "subheading": f"P{i}. {risk_name_kr} 대응 전략 (AAL {total_aal}%)",
                "content": content
            }

            mitigation_blocks.append(text_block)

        return mitigation_blocks

    def _create_implementation_roadmap(self, mitigation_strategies: List[Dict]) -> Dict:
        """
        전체 실행 로드맵 생성

        Args:
            mitigation_strategies: 대응 전략 리스트

        Returns:
            Dict: {
                "timeline": {...},
                "total_cost": str,
                "priority_actions": List[str]
            }
        """
        # 우선순위별 분류
        high_priority = []
        medium_priority = []

        # 전체 비용 집계
        total_cost_estimate = "산정 중"

        # 우선순위 액션 추출
        for strategy in mitigation_strategies:
            risk_name_kr = self.risk_name_mapping.get(strategy["risk_type"], strategy["risk_type"])
            priority = strategy.get("priority", "중간")

            if priority in ["매우 높음", "높음"]:
                high_priority.append({
                    "risk": risk_name_kr,
                    "rank": strategy["rank"],
                    "short_term_actions": strategy.get("short_term", [])
                })
            else:
                medium_priority.append({
                    "risk": risk_name_kr,
                    "rank": strategy["rank"],
                    "short_term_actions": strategy.get("short_term", [])
                })

        # 우선순위 액션 리스트
        priority_actions = []
        for item in high_priority:
            for action in item["short_term_actions"][:2]:  # 상위 2개만
                priority_actions.append(f"[P{item['rank']} {item['risk']}] {action}")

        return {
            "timeline": {
                "short_term": "2026년 (향후 1년)",
                "mid_term": "2026-2030년 (향후 5년, 연도별)",
                "long_term": "2020년대/2030년대/2040년대/2050년대 (10년 단위 평균)"
            },
            "total_cost": total_cost_estimate,
            "priority_actions": priority_actions,
            "high_priority_risks": [item["risk"] for item in high_priority],
            "medium_priority_risks": [item["risk"] for item in medium_priority]
        }


# ============================================================
# Utility Functions
# ============================================================

def validate_text_block(text_block: Dict) -> bool:
    """
    TextBlock이 schemas.py 구조를 준수하는지 검증

    Args:
        text_block: 검증할 TextBlock JSON

    Returns:
        bool: 유효하면 True
    """
    try:
        TextBlock(**text_block)
        return True
    except Exception as e:
        print(f"❌ TextBlock 검증 실패: {e}")
        return False
