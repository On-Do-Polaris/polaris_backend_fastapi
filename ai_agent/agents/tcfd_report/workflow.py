"""
TCFD Report Generation Workflow (LangGraph)
7개 노드 워크플로우 정의 (v2.1 Refactoring)

처리 순서:
- 순차 처리: Node 0 → 1 → 2-A → 2-B → 2-C → 3 → 4 → 5 → 6
- 병렬 처리: 각 노드 내부에서만 병렬 처리 (사업장별, 리스크별)

노드 통합 (v2.0 → v2.1):
- 구 Node 4, 5, 6, 8 → 신 Node 5 (Composer)로 통합
- 구 Node 7 → 신 Node 4 (Validator)
- 구 Node 9 → 신 Node 6 (Finalizer)

재실행 로직 (Node 4 Validator):
- Validation 실패 시 failed_nodes 기반 재실행
- 재실행 대상: 실패 노드 + 모든 downstream 노드
- 최대 재시도: 2회 (retry_count < 2)
"""

from langgraph.graph import StateGraph
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from qdrant_client import QdrantClient

# State 정의를 state.py에서 import
from .state import TCFDReportState


def route_after_validation(state: TCFDReportState) -> str:
    """
    Validator (Node 4) 이후 조건부 라우팅

    Returns:
        - "pass": Validation 통과 → Node 5 (Composer)
        - "retry_node_2a": Node 2-A부터 재실행
        - "retry_node_2b": Node 2-B부터 재실행
        - "retry_node_2c": Node 2-C부터 재실행
        - "retry_node_3": Node 3부터 재실행
        - "fail": 재시도 횟수 초과 → Node 6 (Finalizer) 실패 처리
    """
    validation = state.get("validation_result", {})

    # 1. Validation 통과
    if validation.get("is_valid"):
        print("\n✅ Validation 통과 → Node 5 (Composer)로 이동")
        return "pass"

    # 2. 재시도 횟수 확인
    retry_count = state.get("retry_count", 0)
    if retry_count >= 1:
        print(f"\n❌ 재시도 횟수 초과 ({retry_count}/1) → Node 6 (Finalizer) 실패 처리")
        return "fail"

    # 3. 실패한 노드 확인 및 우선순위 기반 재실행
    failed_nodes = validation.get("failed_nodes", [])

    # 피드백 추출 및 State에 저장 (재실행 시 노드에 전달)
    feedback = validation.get("feedback", {})
    if feedback:
        state["validation_feedback"] = feedback
        print(f"\n📝 피드백 추출 완료: {len(feedback.get('node_specific_guidance', {}))}개 노드 가이던스")

    # 노드 우선순위 정의 (상위 노드부터 재실행)
    node_priority = [
        "node_2a_scenario_analysis",
        "node_2b_impact_analysis",
        "node_2c_mitigation_strategies",
        "node_3_strategy_section"
    ]

    # 가장 상위 실패 노드로 재실행
    for node in node_priority:
        if node in failed_nodes:
            # 재시도 횟수 증가 (State 업데이트)
            state["retry_count"] = retry_count + 1
            print(f"\n🔄 재시도 {state['retry_count']}/1: {node}부터 재실행")
            # LangGraph 엣지명 매핑 (node_2a → retry_2a)
            route_name = f"retry_{node.split('_')[1]}"
            return route_name

    # 4. Failed nodes 없거나 매칭 안됨 → 실패 처리
    print(f"\n⚠️ 재실행 대상 노드 없음 (failed_nodes={failed_nodes}) → 실패 처리")
    return "fail"


def create_tcfd_workflow(
    db_session,
    llm: ChatOpenAI,
    qdrant_client: QdrantClient
):
    """
    TCFD 보고서 생성 워크플로우 생성 (v2.1 - 7-Node)

    Args:
        db_session: DatabaseManager instance
        llm: ChatOpenAI instance (GPT-4 Turbo)
        qdrant_client: QdrantClient instance (RAG)

    Returns:
        StateGraph: 컴파일된 LangGraph 워크플로우
    """
    # 전역 인스턴스 설정 (노드 함수에서 사용)
    _set_global_instances(db_session, llm, qdrant_client)

    workflow = StateGraph(TCFDReportState)

    # ===== 7개 노드 추가 =====
    workflow.add_node("node_0_data_preprocessing", node_0_func)
    workflow.add_node("node_1_template_loading", node_1_func)
    workflow.add_node("node_2a_scenario_analysis", node_2a_func)
    workflow.add_node("node_2b_impact_analysis", node_2b_func)
    workflow.add_node("node_2c_mitigation_strategies", node_2c_func)
    workflow.add_node("node_3_strategy_section", node_3_func)
    workflow.add_node("node_4_validator", node_4_func)
    workflow.add_node("node_5_composer", node_5_func)
    workflow.add_node("node_6_finalizer", node_6_func)

    # ===== 순차 엣지 (Node 0 → 1 → 2A → 2B → 2C → 3 → 4) =====
    workflow.set_entry_point("node_0_data_preprocessing")
    workflow.add_edge("node_0_data_preprocessing", "node_1_template_loading")
    workflow.add_edge("node_1_template_loading", "node_2a_scenario_analysis")
    workflow.add_edge("node_2a_scenario_analysis", "node_2b_impact_analysis")
    workflow.add_edge("node_2b_impact_analysis", "node_2c_mitigation_strategies")
    workflow.add_edge("node_2c_mitigation_strategies", "node_3_strategy_section")
    workflow.add_edge("node_3_strategy_section", "node_4_validator")

    # ===== 조건부 엣지 (Node 4 Validator → 재실행 OR 통과) =====
    workflow.add_conditional_edges(
        "node_4_validator",
        route_after_validation,
        {
            "pass": "node_5_composer",
            "retry_2a": "node_2a_scenario_analysis",
            "retry_2b": "node_2b_impact_analysis",
            "retry_2c": "node_2c_mitigation_strategies",
            "retry_3": "node_3_strategy_section",
            "fail": "node_6_finalizer"
        }
    )

    # ===== Node 5 → 6 엣지 =====
    workflow.add_edge("node_5_composer", "node_6_finalizer")

    # ===== 종료점 설정 =====
    workflow.set_finish_point("node_6_finalizer")

    # ===== 워크플로우 컴파일 =====
    print("\n🔧 TCFD Workflow v2.1 컴파일 중...")
    compiled_workflow = workflow.compile()
    print("✅ 워크플로우 컴파일 완료\n")

    return compiled_workflow


# ===== 각 노드 함수 구현 (v2.1 - 7-Node) =====

# Global instances (create_tcfd_workflow 호출 시 설정)
_db_session = None
_llm = None
_qdrant_client = None


def _set_global_instances(db_session, llm, qdrant_client):
    """전역 인스턴스 설정 (노드 함수에서 사용)"""
    global _db_session, _llm, _qdrant_client
    _db_session = db_session
    _llm = llm
    _qdrant_client = qdrant_client


async def node_0_func(state: TCFDReportState) -> TCFDReportState:
    """
    Node 0: Data Preprocessing
    - DB에서 사업장 데이터 조회
    - ModelOps 5개 결과 테이블 조회
    - AD/BC Agent 실행
    """
    print("\n" + "="*80)
    print("🔵 Node 0: Data Preprocessing 시작")
    print("="*80)

    from .node_0_data_preprocessing import DataPreprocessingNode
    from .llm_output_logger import reset_logger, get_logger

    # LLM Output Logger 초기화 (새 세션 시작)
    reset_logger()
    logger = get_logger()

    # DataPreprocessingNode는 환경변수에서 직접 DB 접속 정보를 가져옴
    node = DataPreprocessingNode(
        llm_client=_llm
    )

    result = await node.execute(
        state["site_ids"],
        state.get("excel_file"),  # DEPRECATED - 미사용
        target_years=None  # None이면 기본값 사용
    )

    # 재시도 횟수 초기화 (최초 실행 시)
    if state.get("retry_count") is None:
        result["retry_count"] = 0

    print(f"✅ Node 0 완료: sites_data={len(result.get('sites_data', []))}개")
    return {**state, **result}


async def node_1_func(state: TCFDReportState) -> TCFDReportState:
    """
    Node 1: Template Loading
    - RAG 기반 템플릿 로딩
    - 유사 보고서 참조 데이터 조회
    """
    print("\n" + "="*80)
    print("🔵 Node 1: Template Loading 시작")
    print("="*80)

    from .node_1_template_loading import TemplateLoadingNode

    node = TemplateLoadingNode(_llm)

    # sites_data에서 회사명 추출 (첫 번째 사업장 이름 사용)
    sites_data = state.get("sites_data", [])
    company_name = "Unknown Company"
    if sites_data and len(sites_data) > 0:
        company_name = sites_data[0].get("site_info", {}).get("name", "Unknown Company")

    # past_reports는 빈 리스트로 전달 (현재 과거 보고서 데이터 없음)
    past_reports = []

    result = await node.execute(
        company_name=company_name,
        past_reports=past_reports,
        mode="init"
    )

    # Node 1 결과를 templates 키로 매핑
    templates = result.get('report_template_profile', {})
    print(f"✅ Node 1 완료: templates={len(templates) if templates else 0}개 필드")

    return {
        **state,
        "templates": templates,
        "rag_references": result.get('style_references', []),
        "citations": result.get('citations', [])
    }


async def node_2a_func(state: TCFDReportState) -> TCFDReportState:
    """
    Node 2-A: Scenario Analysis
    - SSP 시나리오별 AAL 추이 분석
    - 시나리오 비교 텍스트 생성
    - TableBlock 생성
    """
    retry_count = state.get("retry_count", 0)
    is_retry = retry_count > 0

    print("\n" + "="*80)
    if is_retry:
        print(f"🔵 Node 2-A: Scenario Analysis 재실행 (시도 {retry_count}/1)")
    else:
        print("🔵 Node 2-A: Scenario Analysis 시작")
    print("="*80)

    from .node_2a_scenario_analysis import ScenarioAnalysisNode

    node = ScenarioAnalysisNode(_llm)

    # 재실행 시 피드백 전달
    validation_feedback = state.get("validation_feedback") if is_retry else None

    result = await node.execute(
        state["sites_data"],
        state.get("templates"),  # report_template (Node 1 출력)
        None,  # agent_guideline (현재 미사용)
        validation_feedback  # 재실행 시 피드백
    )

    print(f"✅ Node 2-A 완료: scenarios={len(result.get('scenarios', {}))}개")
    return {**state, **result}


async def node_2b_func(state: TCFDReportState) -> TCFDReportState:
    """
    Node 2-B: Impact Analysis
    - Top 5 리스크 선정
    - 리스크별 영향 분석
    - TextBlock x5 생성
    """
    retry_count = state.get("retry_count", 0)
    is_retry = retry_count > 0

    print("\n" + "="*80)
    if is_retry:
        print(f"🔵 Node 2-B: Impact Analysis 재실행 (시도 {retry_count}/1)")
    else:
        print("🔵 Node 2-B: Impact Analysis 시작")
    print("="*80)

    from .node_2b_impact_analysis import ImpactAnalysisNode

    node = ImpactAnalysisNode(_llm)

    # 재실행 시 피드백 전달
    validation_feedback = state.get("validation_feedback") if is_retry else None

    result = await node.execute(
        state["sites_data"],
        state.get("scenarios"),  # scenario_analysis (Node 2-A 출력)
        state.get("templates"),  # report_template (Node 1 출력)
        state.get("building_data"),  # Optional: BC Agent 결과
        state.get("additional_data"),  # Optional: AD Agent 결과
        None,  # sites_metadata (현재 미사용)
        validation_feedback  # 재실행 시 피드백
    )

    print(f"✅ Node 2-B 완료: top_risks={len(result.get('top_risks', []))}개 리스크")
    return {**state, **result}


async def node_2c_func(state: TCFDReportState) -> TCFDReportState:
    """
    Node 2-C: Mitigation Strategies
    - Top 5 리스크별 대응 전략
    - TextBlock x5 생성
    """
    retry_count = state.get("retry_count", 0)
    is_retry = retry_count > 0

    print("\n" + "="*80)
    if is_retry:
        print(f"🔵 Node 2-C: Mitigation Strategies 재실행 (시도 {retry_count}/1)")
    else:
        print("🔵 Node 2-C: Mitigation Strategies 시작")
    print("="*80)

    from .node_2c_mitigation_strategies import MitigationStrategiesNode

    node = MitigationStrategiesNode(_llm)

    # 재실행 시 피드백 전달
    validation_feedback = state.get("validation_feedback") if is_retry else None

    result = await node.execute(
        state.get("impact_analyses"),
        state.get("templates"),  # report_template (Node 1 출력)
        state.get("building_data"),  # Optional: BC Agent 결과
        state.get("additional_data"),  # Optional: AD Agent 결과
        None,  # company_context (현재 미사용)
        validation_feedback  # 재실행 시 피드백
    )

    print(f"✅ Node 2-C 완료: mitigation_strategies={len(result.get('mitigation_strategies', []))}개")
    return {**state, **result}


async def node_3_func(state: TCFDReportState) -> TCFDReportState:
    """
    Node 3: Strategy Section
    - 전략 섹션 통합
    - Executive Summary 생성
    - HeatmapTableBlock 생성
    """
    retry_count = state.get("retry_count", 0)
    is_retry = retry_count > 0

    print("\n" + "="*80)
    if is_retry:
        print(f"🔵 Node 3: Strategy Section 재실행 (시도 {retry_count}/1)")
    else:
        print("🔵 Node 3: Strategy Section 시작")
    print("="*80)

    from .node_3_strategy_section import StrategySectionNode

    node = StrategySectionNode(_llm)

    # 재실행 시 피드백 전달
    validation_feedback = state.get("validation_feedback") if is_retry else None

    result = await node.execute(
        state.get("scenarios"),
        state.get("impact_analyses"),
        state.get("mitigation_strategies"),
        state.get("sites_data"),
        state.get("impact_blocks"),
        state.get("mitigation_blocks"),
        state.get("templates"),  # report_template (Node 1 출력)
        None,  # implementation_roadmap (현재 미사용)
        validation_feedback  # 재실행 시 피드백
    )

    print(f"✅ Node 3 완료: strategy_section 생성 완료")
    return {**state, **result}


async def node_4_func(state: TCFDReportState) -> TCFDReportState:
    """
    Node 4: Validator
    - Rule-based 검증 (구조, 데이터 일관성)
    - LLM 기반 의미적 검증
    - 피드백 생성 (재실행 가이드 포함)
    """
    print("\n" + "="*80)
    print("🔵 Node 4: Validator 시작")
    print("="*80)

    from .node_4_validator import ValidatorNode

    # 재시도 횟수 증가 (재실행 시)
    retry_count = state.get("retry_count", 0)

    node = ValidatorNode(_llm)
    validation_result = await node.execute(
        state.get("strategy_section"),
        retry_count
    )

    # Validation 결과 저장
    result = {
        "validation_result": validation_result,
        "retry_count": retry_count
    }

    # Validation 통과 시 validated_sections 저장
    if validation_result.get("is_valid"):
        result["validated_sections"] = state.get("strategy_section")
        print(f"✅ Node 4 완료: Validation 통과 (Quality Score: {validation_result.get('quality_score'):.1f}%)")
    else:
        failed_nodes = validation_result.get("failed_nodes", [])
        print(f"⚠️ Node 4 완료: Validation 실패 ({len(validation_result.get('issues', []))}개 이슈)")
        print(f"   재실행 대상: {failed_nodes}")

    return {**state, **result}


async def node_5_func(state: TCFDReportState) -> TCFDReportState:
    """
    Node 5: Composer
    - 최종 TCFD 보고서 JSON 생성
    - 4개 섹션 통합 (Governance, Strategy, Risk Management, Metrics)
    """
    print("\n" + "="*80)
    print("🔵 Node 5: Composer 시작")
    print("="*80)

    from .node_5_composer import ComposerNode

    node = ComposerNode(_llm)
    result = await node.execute(
        state.get("validated_sections"),
        state.get("scenarios"),
        state.get("mitigation_strategies"),
        state.get("heatmap_table_block")
    )

    print(f"✅ Node 5 완료: 최종 보고서 JSON 생성 완료")
    return {**state, **result}


async def node_6_func(state: TCFDReportState) -> TCFDReportState:
    """
    Node 6: Finalizer
    - DB 저장 (tcfd_reports 테이블)
    - Validation 실패 여부와 관계없이 항상 보고서 생성
    - success 플래그로 검증 통과 여부 표시
    """
    print("\n" + "="*80)
    print("🔵 Node 6: Finalizer 시작")
    print("="*80)

    from .node_6_finalizer import FinalizerNode

    # Validation 결과 확인 (보고서는 생성하되 success 플래그만 설정)
    validation_result = state.get("validation_result", {})
    is_valid = validation_result.get("is_valid", False)

    if not is_valid:
        print("⚠️ Validation 실패 상태이지만 보고서는 생성합니다 (success=False)")

    # DB 저장 (validation 실패해도 항상 저장)
    node = FinalizerNode(_db_session)
    result = await node.execute(
        state.get("report"),
        state["user_id"]
    )

    # Validation 실패 시 success=False로 덮어쓰기
    if not is_valid:
        result["success"] = False

    if result.get("success"):
        print(f"✅ Node 6 완료: 보고서 저장 완료 (ID: {result.get('report_id')}, Validation: 통과)")
    else:
        print(f"⚠️ Node 6 완료: 보고서 저장 완료 (ID: {result.get('report_id')}, Validation: 실패)")

    # LLM Output Logger 요약 저장
    from .llm_output_logger import get_logger
    try:
        logger = get_logger()
        summary_path = logger.save_summary()
        print(f"📁 LLM 출력물 저장 완료: {logger.get_session_dir()}")
    except Exception as e:
        print(f"⚠️ LLM 출력물 요약 저장 실패: {e}")

    return {**state, **result}
