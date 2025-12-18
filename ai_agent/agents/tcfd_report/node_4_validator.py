"""
Node 4: Validator & Refiner v2.1
최종 수정일: 2025-12-17
버전: v2.1 - LENGTH VALIDATION ADDED

개요:
    Node 4: TCFD 검증 및 품질 관리 노드

    - TCFD 7대 원칙 검증: Relevant, Specific, Clear, Consistent, Comparable, Reliable, Timely
    - 데이터 일관성 검증
    - 품질 점수 산출
    - Critical 이슈 발생 시 1회 재생성 (무한 루프 방지)

주요 기능:
    1. 필수 섹션 완성도 검증
    2. 데이터 일관성 검증 (AAL 합계, 리스크 순위 등)
    3. TCFD 7대 원칙 검증
    4. 품질 점수 산출 (0-100점)
    5. Critical 이슈 발생 시 피드백 제공

입력:
    - strategy: Dict (Node 3 출력)
    - report_template: Dict (Node 1 출력)
    - scenario_analysis: Dict (Node 2-A 출력)
    - impact_analyses: List[Dict] (Node 2-B 출력)

출력:
    - validation_result: Dict (is_valid, quality_score, issues, feedback)
    - validated: bool
"""

import json
import re
from typing import Dict, Any, List, Optional


class ValidatorNode:
    """
    Node 4: Validator & Refiner 노드 v2

    역할:
        - TCFD 보고서 품질 검증
        - 7대 원칙 준수 여부 확인
        - 데이터 일관성 검증
        - 품질 점수 산출

    의존성:
        - Node 3 (Strategy Section) 완료 필수
        - Node 2-A, 2-B (데이터 일관성 검증용)
    """

    def __init__(self, llm_client=None):
        """
        Node 초기화

        Args:
            llm_client: ainvoke 메서드를 지원하는 LLM 클라이언트 (optional)
        """
        self.llm = llm_client

        # TCFD 7대 원칙
        self.tcfd_principles = [
            "Relevant",      # 관련성: 투자자에게 유용한 정보
            "Specific",      # 구체성: 정량적 데이터 포함
            "Clear",         # 명확성: 이해하기 쉬운 언어
            "Consistent",    # 일관성: 내부 데이터 일치
            "Comparable",    # 비교가능성: 시간/조직간 비교
            "Reliable",      # 신뢰성: 검증 가능한 데이터
            "Timely"         # 적시성: 최신 정보 반영
        ]

        # 길이 검증 기준 (v2.1 추가)
        self.length_requirements = {
            "executive_summary_min_words": 150,
            "executive_summary_max_words": 300,
            "total_content_min_words": 1500,
            "total_content_max_words": 3000,
            "per_risk_min_words": 200  # 리스크당 최소 단어 수
        }

    def _count_words(self, text: str) -> int:
        """
        텍스트의 단어 수 계산 (한글 + 영어 혼합 지원)

        Args:
            text: 분석할 텍스트

        Returns:
            int: 단어 수
        """
        if not text:
            return 0

        # 한글 단어 (연속된 한글 문자)
        korean_words = re.findall(r'[가-힣]+', text)

        # 영어 단어 (연속된 영문 알파벳)
        english_words = re.findall(r'[a-zA-Z]+', text)

        # 숫자 (연속된 숫자는 하나의 토큰으로)
        numbers = re.findall(r'\d+(?:\.\d+)?%?', text)

        return len(korean_words) + len(english_words) + len(numbers)

    async def execute(
        self,
        strategy_section: Dict,
        report_template: Optional[Dict] = None,
        scenario_analysis: Optional[Dict] = None,
        impact_analyses: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        Args:
            strategy_section: Node 3 출력 (Strategy 섹션)
            report_template: Node 1 출력 (optional, 데이터 검증용)
            scenario_analysis: Node 2-A 출력 (optional, 데이터 검증용)
            impact_analyses: Node 2-B 출력 (optional, 데이터 검증용)

        Returns:
            Dict: 검증 결과
        """
        print("\n" + "="*80)
        print("▶ Node 4: Validator 검증 시작")
        print("="*80)

        # 1. 필수 섹션 체크 + 길이 검증 (v2.1)
        print("\n[Step 1/6] 필수 요소 완성도 및 길이 검증...")
        completeness_issues = self._check_completeness(strategy_section)
        print(f"  ✅ 완성도/길이 검증 완료 ({len(completeness_issues)}개 이슈)")

        # 2. 데이터 일관성 검증
        print("\n[Step 2/6] 데이터 일관성 검증...")
        consistency_issues = self._check_data_consistency(
            strategy_section,
            scenario_analysis,
            impact_analyses
        )
        print(f"  ✅ 일관성 검증 완료 ({len(consistency_issues)}개 이슈)")

        # 3. TCFD 7대 원칙 검증
        print("\n[Step 3/6] TCFD 7대 원칙 검증...")
        principle_scores = self._check_tcfd_principles(strategy_section)
        print(f"  ✅ 원칙 검증 완료")

        # Rule-based 이슈 통합
        rule_based_issues = completeness_issues + consistency_issues
        critical_count = len([i for i in rule_based_issues if i["severity"] == "critical"])

        # 4. LLM 기반 의미적 품질 검증 (Critical 이슈가 없을 때만 실행 - 비용 최적화)
        print("\n[Step 4/6] LLM 기반 의미적 품질 검증...")
        semantic_issues = []
        if self.llm and critical_count == 0:
            print("  🔍 LLM semantic validation 실행 중...")
            semantic_issues = await self._check_semantic_quality(strategy_section)
            print(f"  ✅ LLM 검증 완료 ({len(semantic_issues)}개 이슈)")
        elif self.llm and critical_count > 0:
            print(f"  ⏭️  Rule-based Critical 이슈 발견 ({critical_count}건) - LLM 검증 스킵 (비용 절약)")
        else:
            print("  ⏭️  LLM 클라이언트 없음 - 스킵")

        # 5. 모든 이슈 통합
        print("\n[Step 5/6] 이슈 통합 및 품질 점수 산출...")
        all_issues = rule_based_issues + semantic_issues
        quality_score = self._calculate_quality_score(all_issues, principle_scores)
        print(f"  ✅ 품질 점수: {quality_score:.1f}/100")

        # 6. 실패한 노드 추출 (재실행 대상)
        print("\n[Step 6/6] 피드백 생성 및 재실행 노드 추출...")
        failed_nodes = []
        for issue in all_issues:
            if issue["severity"] == "critical" and "node" in issue:
                node = issue["node"]
                if node not in failed_nodes:
                    failed_nodes.append(node)

        # 노드 우선순위 정렬 (상위 노드부터 재실행)
        node_priority = [
            "node_2a_scenario_analysis",
            "node_2b_impact_analysis",
            "node_2c_mitigation_strategies",
            "node_3_strategy_section"
        ]
        failed_nodes = sorted(failed_nodes, key=lambda x: node_priority.index(x) if x in node_priority else 999)

        # 검증 통과 여부
        is_valid = len([i for i in all_issues if i["severity"] == "critical"]) == 0

        # LLM 기반 피드백 생성
        if self.llm:
            feedback = await self._generate_feedback_with_llm(all_issues, strategy_section, is_valid)
        else:
            feedback = {
                "summary": self._generate_feedback(all_issues, is_valid),
                "critical_fixes": [],
                "improvement_suggestions": [],
                "retry_guidance": {}
            }

        print(f"  ✅ 피드백 생성 완료")

        # retry_count는 state에서 가져오거나 0으로 초기화 (workflow에서 관리)
        retry_count = 0  # workflow에서 state.get("retry_count", 0)로 전달받아야 함

        # 검증 결과 조립
        validation_result = {
            "is_valid": is_valid,
            "quality_score": quality_score,
            "issues": all_issues,
            "principle_scores": principle_scores,
            "feedback": feedback,
            "failed_nodes": failed_nodes,  # NEW: 재실행 대상 노드 리스트
            "retry_count": retry_count      # NEW: 재시도 횟수 (workflow에서 관리)
        }

        print("\n" + "="*80)
        if is_valid:
            print(f"✅ Node 4: 검증 통과 (품질 점수: {quality_score:.1f})")
        else:
            critical_count = len([i for i in all_issues if i["severity"] == "critical"])
            print(f"⚠️  Node 4: Critical 이슈 발견 ({critical_count}건)")
            if failed_nodes:
                print(f"🔄 재실행 필요 노드: {', '.join(failed_nodes)}")
        print("="*80)

        return {
            "validation_result": validation_result,
            "validated": is_valid
        }

    def _check_completeness(self, strategy_section: Dict) -> List[Dict]:
        """
        필수 요소 완성도 검증

        Args:
            strategy_section: Node 3 출력

        Returns:
            List[Dict]: 이슈 리스트
        """
        issues = []

        # 0. None 체크 (방어적 코딩)
        if strategy_section is None:
            issues.append({
                "severity": "critical",
                "type": "completeness",
                "field": "strategy_section",
                "message": "strategy_section이 None입니다 (Node 3 실행 실패 가능성)"
            })
            return issues

        # 1. 필수 필드 체크
        required_fields = ["section_id", "title", "blocks"]
        for field in required_fields:
            if field not in strategy_section:
                issues.append({
                    "severity": "critical",
                    "type": "completeness",
                    "field": field,
                    "message": f"필수 필드 누락: {field}"
                })

        # 2. 블록 개수 체크 (최소 5개 이상 필요)
        blocks = strategy_section.get("blocks", [])
        if len(blocks) < 5:
            issues.append({
                "severity": "warning",
                "type": "completeness",
                "field": "blocks",
                "message": f"블록 개수 부족: {len(blocks)}개 (최소 5개 권장)"
            })

        # 3. Executive Summary 존재 여부 및 길이 검증 (v2.1 강화)
        has_exec_summary = False
        for block in blocks:
            if block.get("subheading") == "Executive Summary":
                has_exec_summary = True
                content = block.get("content", "")
                word_count = self._count_words(content)

                # 단어 수 기반 검증 (150-300 words)
                min_words = self.length_requirements["executive_summary_min_words"]
                max_words = self.length_requirements["executive_summary_max_words"]

                if word_count < min_words:
                    issues.append({
                        "severity": "critical",
                        "type": "length",
                        "field": "executive_summary",
                        "node": "node_3_strategy_section",
                        "message": f"Executive Summary가 너무 짧습니다 ({word_count} 단어, 최소 {min_words} 단어 필요)"
                    })
                elif word_count > max_words:
                    issues.append({
                        "severity": "warning",
                        "type": "length",
                        "field": "executive_summary",
                        "message": f"Executive Summary가 너무 깁니다 ({word_count} 단어, 권장 {max_words} 단어 이하)"
                    })
                break

        if not has_exec_summary:
            issues.append({
                "severity": "critical",
                "type": "completeness",
                "field": "executive_summary",
                "node": "node_3_strategy_section",
                "message": "Executive Summary 누락"
            })

        # 4-1. 전체 콘텐츠 길이 검증 (v2.1 추가)
        total_content = ""
        for block in blocks:
            if block.get("type") == "text":
                total_content += block.get("content", "") + " "
        total_word_count = self._count_words(total_content)

        min_total = self.length_requirements["total_content_min_words"]
        if total_word_count < min_total:
            issues.append({
                "severity": "critical",
                "type": "length",
                "field": "total_content",
                "node": "node_3_strategy_section",
                "message": f"Strategy 섹션 전체 길이가 부족합니다 ({total_word_count} 단어, 최소 {min_total} 단어 필요)"
            })

        # 4. HeatmapTableBlock 존재 여부
        has_heatmap = False
        for block in blocks:
            if block.get("type") == "heatmap_table":
                has_heatmap = True
                break

        if not has_heatmap:
            issues.append({
                "severity": "warning",
                "type": "completeness",
                "field": "heatmap_table",
                "message": "HeatmapTableBlock 누락 (권장)"
            })

        return issues

    def _check_data_consistency(
        self,
        strategy_section: Dict,
        scenario_analysis: Optional[Dict],
        impact_analyses: Optional[List[Dict]]
    ) -> List[Dict]:
        """
        데이터 일관성 검증

        Args:
            strategy_section: Node 3 출력
            scenario_analysis: Node 2-A 출력 (optional)
            impact_analyses: Node 2-B 출력 (optional)

        Returns:
            List[Dict]: 이슈 리스트
        """
        issues = []

        # 1. HeatmapTable과 Impact Analyses 일관성 체크
        if impact_analyses:
            heatmap_block = None
            for block in strategy_section.get("blocks", []):
                if block.get("type") == "heatmap_table":
                    heatmap_block = block
                    break

            if heatmap_block:
                # Heatmap 헤더의 리스크 개수 vs Impact Analyses 개수
                headers = heatmap_block.get("data", {}).get("headers", [])
                # 첫 번째는 "사업장", 마지막은 "Total AAL"이므로 제외
                risk_count_in_heatmap = len(headers) - 2
                impact_count = len(impact_analyses)

                if risk_count_in_heatmap != impact_count:
                    issues.append({
                        "severity": "warning",
                        "type": "consistency",
                        "field": "heatmap_risks",
                        "message": f"Heatmap 리스크 개수({risk_count_in_heatmap})와 Impact Analysis 개수({impact_count})가 불일치"
                    })

        # 2. Priority Actions Table과 Impact Analyses 일관성 체크
        priority_table = strategy_section.get("priority_actions_table")
        if priority_table and impact_analyses:
            rows = priority_table.get("data", {}).get("rows", [])
            if len(rows) != len(impact_analyses):
                issues.append({
                    "severity": "warning",
                    "type": "consistency",
                    "field": "priority_table",
                    "message": f"Priority Table 행 개수({len(rows)})와 Impact Analysis 개수({len(impact_analyses)})가 불일치"
                })

        # 3. AAL 값 범위 체크
        # 참고: total_aal은 멀티 사이트 합계이므로 100%를 초과할 수 있음 (정상)
        # 개별 사이트 AAL만 0-100% 범위 검증
        if impact_analyses:
            for i, impact in enumerate(impact_analyses, 1):
                # 개별 사이트별 AAL 검증 (site_aal_values가 있는 경우)
                site_aal_values = impact.get("site_aal_values", {})
                for site_name, aal in site_aal_values.items():
                    if aal < 0 or aal > 100:
                        issues.append({
                            "severity": "critical",
                            "type": "data_validity",
                            "field": f"impact_aal_p{i}_{site_name}",
                            "message": f"P{i} {site_name} AAL 값이 범위를 벗어남: {aal}% (0-100% 범위)"
                        })

                # total_aal이 음수인 경우만 에러 (합계 > 100%는 멀티사이트에서 정상)
                total_aal = impact.get("total_aal", 0.0)
                if total_aal < 0:
                    issues.append({
                        "severity": "critical",
                        "type": "data_validity",
                        "field": f"impact_aal_p{i}",
                        "message": f"P{i} AAL 값이 음수: {total_aal}%"
                    })

        return issues

    async def _check_semantic_quality(self, strategy_section: Dict) -> List[Dict]:
        """
        LLM 기반 의미적 품질 검증

        Args:
            strategy_section: Node 3 출력

        Returns:
            List[Dict]: 의미적 이슈 리스트
        """
        if not self.llm:
            return []  # LLM이 없으면 스킵

        # strategy_section을 JSON string으로 변환 (pretty print)
        section_json = json.dumps(strategy_section, indent=2, ensure_ascii=False)

        prompt = f"""You are a TCFD report quality validator. Check semantic quality of the report section.

<REPORT_SECTION>
{section_json}
</REPORT_SECTION>

<VALIDATION_CRITERIA>
1. **Logical Consistency**: Do risk levels match AAL values?
   - AAL 0-3%: Low risk
   - AAL 3-10%: Medium risk
   - AAL 10-30%: High risk
   - AAL 30%+: Very high risk

2. **TCFD Principles**:
   - Relevant: Is this useful for investors?
   - Specific: Are quantitative data meaningful?
   - Clear: Is language unambiguous?
   - Consistent: Do all sections align?

3. **Completeness**:
   - Does Executive Summary cover key findings?
   - Are mitigation strategies actionable?
   - Are timelines realistic?

4. **Data Interpretation**:
   - Are AAL values interpreted correctly?
   - Do risk rankings make sense?
   - Are mitigation costs reasonable?
</VALIDATION_CRITERIA>

<OUTPUT_FORMAT>
Generate JSON array of semantic issues found:

[
  {{
    "severity": "critical" | "warning",
    "type": "semantic",
    "category": "logical_consistency" | "tcfd_principle" | "completeness" | "data_interpretation",
    "message": "Brief description",
    "evidence": "Quote from report showing the issue",
    "suggestion": "How to fix",
    "node": "node_2b_impact_analysis" | "node_2c_mitigation_strategies" | "node_3_strategy_section"
  }}
]

**IMPORTANT**: The "node" field must indicate which node needs to be re-executed to fix the issue:
- "node_2a_scenario_analysis" - for scenario analysis issues
- "node_2b_impact_analysis" - for risk ranking, AAL interpretation issues
- "node_2c_mitigation_strategies" - for mitigation strategy issues
- "node_3_strategy_section" - for overall structure, Executive Summary issues

If no semantic issues found, return empty array: []

Output pure JSON only. No markdown, no code blocks.
</OUTPUT_FORMAT>"""

        try:
            result = await self.llm.ainvoke(prompt)

            # LLM 응답이 문자열인 경우 (대부분의 LLM)
            if isinstance(result, str):
                content = result
            # LangChain AIMessage 객체인 경우
            elif hasattr(result, 'content'):
                content = result.content
            else:
                content = str(result)

            # Markdown code block 제거 (```json ... ```)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # JSON 파싱
            issues = json.loads(content)

            # 결과 검증
            if not isinstance(issues, list):
                print(f"  ⚠️  LLM semantic validation returned non-list: {type(issues)}")
                return []

            return issues

        except json.JSONDecodeError as e:
            print(f"  ⚠️  LLM semantic validation JSON parse error: {e}")
            print(f"  Raw response: {content[:200]}...")
            return []
        except Exception as e:
            print(f"  ⚠️  LLM semantic validation error: {e}")
            return []

    def _check_tcfd_principles(self, strategy_section: Dict) -> Dict[str, float]:
        """
        TCFD 7대 원칙 검증

        Args:
            strategy_section: Node 3 출력

        Returns:
            Dict[str, float]: 원칙별 점수 (0-100)
        """
        scores = {}

        # 1. Relevant (관련성): Executive Summary 존재 여부
        has_exec_summary = any(
            b.get("subheading") == "Executive Summary"
            for b in strategy_section.get("blocks", [])
        )
        scores["Relevant"] = 100.0 if has_exec_summary else 50.0

        # 2. Specific (구체성): 정량적 데이터 포함 여부 (HeatmapTable, Priority Table)
        has_heatmap = any(
            b.get("type") == "heatmap_table"
            for b in strategy_section.get("blocks", [])
        )
        has_priority_table = strategy_section.get("priority_actions_table") is not None
        scores["Specific"] = 100.0 if (has_heatmap and has_priority_table) else 70.0

        # 3. Clear (명확성): 블록 구조화 여부
        blocks = strategy_section.get("blocks", [])
        has_structure = len(blocks) >= 5 and all(
            "type" in b for b in blocks
        )
        scores["Clear"] = 100.0 if has_structure else 70.0

        # 4. Consistent (일관성): 데이터 검증은 _check_data_consistency에서 수행
        scores["Consistent"] = 90.0  # 기본 점수 (데이터 일관성 이슈가 있으면 감점)

        # 5. Comparable (비교가능성): 시나리오/리스크 비교 가능 여부
        scores["Comparable"] = 85.0  # 기본 점수

        # 6. Reliable (신뢰성): 데이터 출처 명확성
        scores["Reliable"] = 90.0  # 기본 점수

        # 7. Timely (적시성): 최신 데이터 사용 여부
        scores["Timely"] = 95.0  # 기본 점수 (2025년 기준)

        return scores

    def _calculate_quality_score(
        self,
        issues: List[Dict],
        principle_scores: Dict[str, float]
    ) -> float:
        """
        품질 점수 산출 (0-100점)

        Args:
            issues: 이슈 리스트
            principle_scores: TCFD 원칙별 점수

        Returns:
            float: 품질 점수
        """
        # 1. 기본 점수 (TCFD 원칙 평균)
        base_score = sum(principle_scores.values()) / len(principle_scores)

        # 2. 이슈 감점
        deduction = 0.0
        for issue in issues:
            if issue["severity"] == "critical":
                deduction += 20.0  # Critical 이슈당 -20점
            elif issue["severity"] == "warning":
                deduction += 5.0   # Warning 이슈당 -5점

        # 3. 최종 점수 (최소 0점, 최대 100점)
        final_score = max(0.0, min(100.0, base_score - deduction))

        return final_score

    async def _generate_feedback_with_llm(
        self,
        issues: List[Dict],
        strategy_section: Dict,
        is_valid: bool
    ) -> Dict[str, Any]:
        """
        LLM 기반 피드백 생성 (구조화된 피드백)

        Args:
            issues: 이슈 리스트 (Rule + LLM 결합)
            strategy_section: Node 3 출력
            is_valid: 검증 통과 여부

        Returns:
            Dict: 구조화된 피드백
        """
        if not self.llm:
            # LLM이 없으면 기존 Rule-based 피드백 사용
            return {
                "summary": self._generate_feedback(issues, is_valid),
                "critical_fixes": [],
                "improvement_suggestions": [],
                "retry_guidance": {}
            }

        if is_valid:
            return {
                "summary": "✅ All validation checks passed.",
                "critical_fixes": [],
                "improvement_suggestions": [],
                "retry_guidance": {}
            }

        # Critical/Warning 이슈 분류
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        warning_issues = [i for i in issues if i["severity"] == "warning"]

        # strategy_section의 일부만 전달 (토큰 절약)
        section_excerpt = json.dumps(strategy_section, indent=2, ensure_ascii=False)[:2000]

        prompt = f"""You are a TCFD report validator. Generate specific, actionable feedback for validation issues.

<VALIDATION_ISSUES>
Critical Issues ({len(critical_issues)}):
{json.dumps(critical_issues, indent=2, ensure_ascii=False)}

Warnings ({len(warning_issues)}):
{json.dumps(warning_issues, indent=2, ensure_ascii=False)}
</VALIDATION_ISSUES>

<REPORT_EXCERPT>
{section_excerpt}
... (truncated)
</REPORT_EXCERPT>

<OUTPUT_FORMAT>
Generate structured feedback in JSON:

{{
  "summary": "Brief overview of validation status (2-3 sentences)",
  "critical_fixes": [
    {{
      "issue": "Issue description",
      "node": "node_2b_impact_analysis" | "node_2c_mitigation_strategies" | "node_3_strategy_section",
      "action": "Specific steps to fix (2-3 sentences)",
      "example": "Expected output example (1-2 sentences)"
    }}
  ],
  "improvement_suggestions": [
    "Suggestion 1 (for warning-level issues)",
    "Suggestion 2"
  ],
  "retry_guidance": {{
    "node_2a_scenario_analysis": "Guidance for this node (if needed)",
    "node_2b_impact_analysis": "Ensure risk ranking matches AAL values",
    "node_2c_mitigation_strategies": "Add financial estimates and timelines",
    "node_3_strategy_section": "Improve Executive Summary coverage"
  }}
}}

**IMPORTANT**:
- "critical_fixes": Only include issues with severity="critical"
- "improvement_suggestions": Include issues with severity="warning"
- "retry_guidance": Provide specific guidance for nodes that need re-execution
- Keep all text concise and actionable

Output pure JSON only. No markdown, no code blocks.
</OUTPUT_FORMAT>"""

        try:
            result = await self.llm.ainvoke(prompt)

            # LLM 응답 파싱 (동일한 로직)
            if isinstance(result, str):
                content = result
            elif hasattr(result, 'content'):
                content = result.content
            else:
                content = str(result)

            # Markdown code block 제거
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # JSON 파싱
            feedback = json.loads(content)

            # 결과 검증
            if not isinstance(feedback, dict):
                print(f"  ⚠️  LLM feedback returned non-dict: {type(feedback)}")
                return {
                    "summary": self._generate_feedback(issues, is_valid),
                    "critical_fixes": [],
                    "improvement_suggestions": [],
                    "retry_guidance": {}
                }

            return feedback

        except json.JSONDecodeError as e:
            print(f"  ⚠️  LLM feedback JSON parse error: {e}")
            print(f"  Raw response: {content[:200]}...")
            # Fallback to rule-based feedback
            return {
                "summary": self._generate_feedback(issues, is_valid),
                "critical_fixes": [],
                "improvement_suggestions": [],
                "retry_guidance": {}
            }
        except Exception as e:
            print(f"  ⚠️  LLM feedback generation error: {e}")
            # Fallback to rule-based feedback
            return {
                "summary": self._generate_feedback(issues, is_valid),
                "critical_fixes": [],
                "improvement_suggestions": [],
                "retry_guidance": {}
            }

    def _generate_feedback(self, issues: List[Dict], is_valid: bool) -> str:
        """
        피드백 메시지 생성

        Args:
            issues: 이슈 리스트
            is_valid: 검증 통과 여부

        Returns:
            str: 피드백 메시지
        """
        if is_valid and len(issues) == 0:
            return "✅ 모든 검증 항목을 통과했습니다. TCFD 보고서 품질이 우수합니다."

        feedback_parts = []

        if not is_valid:
            critical_issues = [i for i in issues if i["severity"] == "critical"]
            feedback_parts.append(f"⚠️  {len(critical_issues)}개의 Critical 이슈가 발견되었습니다:")
            for issue in critical_issues[:3]:  # 최대 3개만 표시
                feedback_parts.append(f"  - {issue['message']}")

        warning_issues = [i for i in issues if i["severity"] == "warning"]
        if warning_issues:
            feedback_parts.append(f"\n📋 {len(warning_issues)}개의 Warning이 있습니다:")
            for issue in warning_issues[:3]:  # 최대 3개만 표시
                feedback_parts.append(f"  - {issue['message']}")

        if not feedback_parts:
            return "검증이 완료되었습니다."

        return "\n".join(feedback_parts)
