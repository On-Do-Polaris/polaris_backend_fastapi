"""
TCFD Report State 정의
LangGraph State TypedDict

작성일: 2025-12-15
버전: v03 (Physical Risk Report 통합)

State 구조:
    - site_data: 사이트 기본 정보 (Application DB)
    - 5개 결과 테이블: 분리 저장 (Datawarehouse DB)
    - building_data: BC Agent 결과 (별도 필드)
    - additional_data: AD Agent 결과 (별도 필드)
    - use_additional_data: Excel 데이터 사용 여부 플래그 (default=False)
    - sites_risk_assessment: 물리적 리스크 평가 (Physical Risk Report용)
    - risk_table_status: 리스크 표 생성 상태
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated


def default_false(current: bool | None, new: bool | None) -> bool:
    """use_additional_data의 기본값을 False로 설정하는 reducer"""
    if new is not None:
        return new
    if current is not None:
        return current
    return False


class TCFDReportState(TypedDict):
    """
    TCFD Report 생성을 위한 LangGraph State (통합 버전)

    Fields:
        # ========== 입력 파라미터 ==========
        site_ids: 사업장 ID 리스트
        excel_file: Excel 파일 경로 (DEPRECATED - 미사용)
        user_id: 사용자 ID (Node 6 DB 저장용)

        # ========== Node 0 출력 (Data Preprocessing) ==========
        sites_data: 사이트 기본 정보 리스트 (Application DB)
        aal_scaled_results: AAL 최종 결과 (Vulnerability 반영)
        hazard_results: Hazard Score 결과
        exposure_results: Exposure Score 결과
        vulnerability_results: Vulnerability Score 결과
        probability_results: Probability P(H) 결과
        building_data: BC Agent 결과 (site_id를 키로 하는 Dict)
        additional_data: AD Agent 결과
        use_additional_data: Excel 추가 데이터 사용 여부 (default=False)

        # ========== Node 1 출력 (Template Loading) ==========
        templates: RAG 기반 템플릿
        rag_references: 유사 보고서 참조 데이터

        # ========== Node 2-A 출력 (Scenario Analysis) ==========
        scenarios: 시나리오별 AAL 추이 분석 결과
        scenario_comparison: 시나리오 비교 텍스트
        scenario_table: 시나리오 TableBlock

        # ========== Node 2-B 출력 (Impact Analysis) ==========
        top_risks: 전체 9개 리스크 리스트 (AAL 순위별)
        impact_analyses: 리스크별 영향 분석 결과 (9개)
        impact_blocks: 영향 분석 TextBlock x9

        # ========== Node 2-C 출력 (Mitigation Strategies) ==========
        mitigation_strategies: 리스크별 대응 전략 (9개)
        mitigation_blocks: 대응 전략 TextBlock x9

        # ========== Node 3 출력 (Strategy Section) ==========
        strategy_section: 전략 섹션 통합 결과
        heatmap_table_block: HeatmapTableBlock

        # ========== Node 4 출력 (Validator) ==========
        validated_sections: 검증 통과한 섹션
        validation_report: 검증 보고서
        validation_result: 검증 결과 상세
        validation_feedback: 재실행 시 피드백

        # ========== Node 5 출력 (Composer) ==========
        report: 최종 TCFD 보고서 JSON

        # ========== Node 6 출력 (Finalizer) ==========
        success: 보고서 생성 성공 여부
        report_id: DB 저장된 보고서 ID
        saved_at: 저장 시각

        # ========== 재실행 로직용 ==========
        retry_count: 재시도 횟수

        # ========== Physical Risk Report 전용 필드 ==========
        sites_risk_assessment: 사업장별 리스크 평가 및 표
        risk_table_status: 리스크 표 생성 상태
    """

    # ========== 입력 파라미터 ==========
    site_ids: List[int]
    excel_file: Optional[str]
    user_id: int

    # ========== Node 0 출력 (Data Preprocessing) ==========
    sites_data: Optional[List[Dict[str, Any]]]  # site_data → sites_data로 통일
    aal_scaled_results: Optional[List[Dict[str, Any]]]
    hazard_results: Optional[List[Dict[str, Any]]]
    exposure_results: Optional[List[Dict[str, Any]]]
    vulnerability_results: Optional[List[Dict[str, Any]]]
    probability_results: Optional[List[Dict[str, Any]]]
    building_data: Optional[Dict[int, Dict[str, Any]]]  # BC Agent 결과
    additional_data: Optional[Dict[str, Any]]           # AD Agent 결과
    use_additional_data: Annotated[bool, default_false]

    # ========== Node 1 출력 (Template Loading) ==========
    templates: Optional[Dict[str, Any]]
    rag_references: Optional[List[Dict[str, Any]]]

    # ========== Node 2-A 출력 (Scenario Analysis) ==========
    scenarios: Optional[Dict[str, Any]]
    scenario_comparison: Optional[str]
    scenario_table: Optional[Dict[str, Any]]  # TableBlock

    # ========== Node 2-B 출력 (Impact Analysis) ==========
    top_risks: Optional[List[Dict[str, Any]]]  # 전체 9개 리스크 (AAL 순위별)
    impact_analyses: Optional[List[Dict[str, Any]]]
    impact_blocks: Optional[List[Dict[str, Any]]]  # TextBlock x9

    # ========== Node 2-C 출력 (Mitigation Strategies) ==========
    mitigation_strategies: Optional[List[Dict[str, Any]]]
    mitigation_blocks: Optional[List[Dict[str, Any]]]  # TextBlock x9

    # ========== Node 3 출력 (Strategy Section) ==========
    strategy_section: Optional[Dict[str, Any]]
    heatmap_table_block: Optional[Dict[str, Any]]  # HeatmapTableBlock

    # ========== Node 4 출력 (Validator) ==========
    validated_sections: Optional[Dict[str, Any]]
    validation_report: Optional[Dict[str, Any]]
    validation_result: Optional[Dict[str, Any]]
    validation_feedback: Optional[Dict[str, Any]]  # 재실행 시 피드백

    # ========== Node 5 출력 (Composer) ==========
    report: Optional[Dict[str, Any]]  # 최종 TCFD 보고서 JSON

    # ========== Node 6 출력 (Finalizer) ==========
    success: Optional[bool]
    report_id: Optional[int]
    saved_at: Optional[str]

    # ========== 재실행 로직용 ==========
    retry_count: Optional[int]

    # ========== Physical Risk Report 전용 필드 ==========
    sites_risk_assessment: Optional[List[Dict[str, Any]]]
    risk_table_status: Optional[str]
