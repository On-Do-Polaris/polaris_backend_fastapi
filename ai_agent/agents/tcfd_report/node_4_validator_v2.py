"""
Node 4: Validator & Refiner v2
최종 수정일: 2025-12-15
버전: v2.0

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

        # 1. 필수 섹션 체크
        print("\n[Step 1/4] 필수 요소 완성도 검증...")
        completeness_issues = self._check_completeness(strategy_section)
        print(f"  ✅ 완성도 검증 완료 ({len(completeness_issues)}개 이슈)")

        # 2. 데이터 일관성 검증
        print("\n[Step 2/4] 데이터 일관성 검증...")
        consistency_issues = self._check_data_consistency(
            strategy_section,
            scenario_analysis,
            impact_analyses
        )
        print(f"  ✅ 일관성 검증 완료 ({len(consistency_issues)}개 이슈)")

        # 3. TCFD 7대 원칙 검증
        print("\n[Step 3/4] TCFD 7대 원칙 검증...")
        principle_scores = self._check_tcfd_principles(strategy_section)
        print(f"  ✅ 원칙 검증 완료")

        # 4. 품질 점수 산출
        print("\n[Step 4/4] 품질 점수 산출...")
        all_issues = completeness_issues + consistency_issues
        quality_score = self._calculate_quality_score(all_issues, principle_scores)
        print(f"  ✅ 품질 점수: {quality_score:.1f}/100")

        # 검증 결과 조립
        is_valid = len([i for i in all_issues if i["severity"] == "critical"]) == 0
        validation_result = {
            "is_valid": is_valid,
            "quality_score": quality_score,
            "issues": all_issues,
            "principle_scores": principle_scores,
            "feedback": self._generate_feedback(all_issues, is_valid)
        }

        print("\n" + "="*80)
        if is_valid:
            print(f"✅ Node 4: 검증 통과 (품질 점수: {quality_score:.1f})")
        else:
            print(f"⚠️  Node 4: Critical 이슈 발견 ({len([i for i in all_issues if i['severity'] == 'critical'])}건)")
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

        # 3. Executive Summary 존재 여부
        has_exec_summary = False
        for block in blocks:
            if block.get("subheading") == "Executive Summary":
                has_exec_summary = True
                # Executive Summary 길이 체크
                content = block.get("content", "")
                if len(content) < 200:
                    issues.append({
                        "severity": "warning",
                        "type": "completeness",
                        "field": "executive_summary",
                        "message": f"Executive Summary가 너무 짧습니다 ({len(content)} 글자, 최소 200 글자 권장)"
                    })
                break

        if not has_exec_summary:
            issues.append({
                "severity": "critical",
                "type": "completeness",
                "field": "executive_summary",
                "message": "Executive Summary 누락"
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
