"""
AI Agent Main.py Mock Data Test Script
목 데이터를 사용하여 main.py의 SKAXPhysicalRiskAnalyzer 테스트

실행 방법:
    python test_main_mock.py

주의사항:
    - OPENAI_API_KEY 환경변수 필요 (LLM 호출)
    - scratch/run_test_mock/ 폴더에 Mock 데이터 필요
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    try:
        # stdout, stderr을 UTF-8로 재설정
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python 3.6 이하 버전 호환
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# .env 파일 로드 (OPENAI_API_KEY 등)
# override=True: 시스템 환경변수를 .env 파일 값으로 덮어씀
load_dotenv(override=True)

# DEBUG: API 키 확인
import os as _os
_api_key = _os.getenv('OPENAI_API_KEY', '')
print(f"[DEBUG] OPENAI_API_KEY length: {len(_api_key)}")
print(f"[DEBUG] OPENAI_API_KEY starts with: {_api_key[:10] if _api_key else 'EMPTY'}")

print("=" * 80)
print("AI Agent Main.py Mock Data Test")
print("=" * 80)

# 1. Check Mock Data Files
print("\n[1] Checking Mock Data Files...")
mock_session_id = "test_mock"
mock_path = f"./scratch/run_{mock_session_id}"

required_files = [
    "metadata.json",
    "climate_data.json",
    "geographic_data.json",
    "historical_events.json",
    "ssp_scenarios.json"
]

for filename in required_files:
    filepath = f"{mock_path}/{filename}"
    if os.path.exists(filepath):
        file_size = os.path.getsize(filepath) / 1024  # KB
        print(f"    [OK] {filename} ({file_size:.2f} KB)")
    else:
        print(f"    [ERROR] {filename} NOT FOUND")
        exit(1)

# 2. Load Config and Initialize Analyzer
print("\n[2] Initializing SKAXPhysicalRiskAnalyzer...")
from ai_agent.config.settings import Config
from ai_agent import SKAXPhysicalRiskAnalyzer

config = Config()
print(f"    DEBUG: {config.DEBUG}")
openai_key = config.LLM_CONFIG.get('api_key', '')
print(f"    OPENAI_API_KEY: {'Set' if openai_key else 'Not Set'}")

analyzer = SKAXPhysicalRiskAnalyzer(config)
print("    [OK] SKAXPhysicalRiskAnalyzer initialized")

# 3. Prepare Input Data
print("\n[3] Preparing Input Data...")

target_location = {
    'latitude': 37.5665,
    'longitude': 126.9780,
    'name': 'Seoul Test Location',
    'admin_code': '1100000000',
    'site_id': 'test_site_001'
}

building_info = {
    'building_age': 25,
    'has_seismic_design': True,
    'fire_access': True,
    'structure': '철근콘크리트',
    'main_purpose': '업무시설',
    'floors_below': 2,
    'floors_above': 10,
    'has_piloti': False,
    'water_supply_available': True
}

asset_info = {
    'total_asset_value': 50000000000,  # 500억원
    'insurance_coverage_rate': 0.7      # 보험보전율 70%
}

analysis_params = {
    'time_horizon': '2050',
    'analysis_period': '2025-2050',
    'start_year': 2025,
    'end_year': 2050,
    'scenario_ids': [1, 2, 3, 4],
    'search_radius_km': 100
}

# Additional data (optional)
additional_data = {
    'raw_text': '이 건물은 최근 리모델링을 진행했으며, 옥상에 태양광 패널이 설치되어 있습니다. 주변 지역은 홍수 위험이 있으며, 지하 주차장이 침수된 사례가 있습니다.',
    'metadata': {
        'source': 'test_input',
        'date': datetime.now().isoformat()
    }
}

print("    [OK] Input data prepared")
print(f"        Location: {target_location['name']}")
print(f"        Building Age: {building_info['building_age']} years")
print(f"        Asset Value: {asset_info['total_asset_value']:,} KRW")
print(f"        Additional Data: {'Provided' if additional_data else 'None'}")

# 4. Create Custom Initial State (Skip Node 1)
print("\n[4] Creating Custom Initial State (Bypassing Data Collection Node)...")

# analyzer의 workflow_graph에 직접 주입할 초기 상태 생성
initial_state = {
    'target_location': target_location,
    'building_info': building_info,
    'asset_info': asset_info,
    'analysis_params': analysis_params,

    # Language setting
    'language': 'en',  # 'ko' for Korean, 'en' for English

    # CRITICAL: Inject mock scratch_session_id to skip data_collection
    'scratch_session_id': mock_session_id,

    # Skip data_collection node
    'current_step': 'physical_risk_score_calculation',  # Node 2로 직접 이동
    'data_collection_status': 'completed',

    # Climate summary (lightweight)
    'climate_summary': {
        'location': target_location,
        'data_years': list(range(2025, 2051)),
        'ssp_scenarios': ['ssp1-2.6', 'ssp2-4.5', 'ssp3-7.0', 'ssp5-8.5'],
        'statistics': {
            'wsdi_mean': 18.5,
            'wsdi_max': 42.0,
            'wsdi_min': 8.0,
            'csdi_mean': 6.5,
            'csdi_max': 12.0,
            'csdi_min': 1.0
        }
    },

    # Additional data (optional)
    'additional_data': additional_data,

    'errors': [],
    'logs': ['Data collection bypassed with mock data'],
    'workflow_status': 'in_progress',
    'retry_count': 0,
    '_workflow_start_time': datetime.now().isoformat()
}

print("    [OK] Initial state created")
print(f"        Starting from: {initial_state['current_step']}")
print(f"        Scratch session: {mock_session_id}")
print(f"        Report Language: {initial_state['language']}")

# 5. Run Workflow
print("\n[5] Running Workflow...")
print("    " + "-" * 76)

try:
    # Execute workflow starting from Node 2 (Physical Risk Score Calculation)
    final_state = None
    node_count = 0

    for state in analyzer.workflow_graph.stream(initial_state):
        node_count += 1
        node_name = list(state.keys())[-1] if state else "unknown"
        print(f"    Step {node_count}: {node_name}")
        final_state = state

    print("    " + "-" * 76)
    print(f"    [OK] Workflow completed ({node_count} steps)")

except Exception as e:
    print(f"    [ERROR] Workflow failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 6. Extract and Display Results
print("\n[6] Analysis Results:")
print("=" * 80)

if final_state:
    last_node_key = list(final_state.keys())[-1]
    result = final_state[last_node_key]

    # Workflow Status
    status = result.get('workflow_status', 'unknown')
    print(f"\nWorkflow Status: {status}")

    # Logs
    logs = result.get('logs', [])
    print(f"\nCompleted Steps: {len(logs)}")
    for log in logs[-5:]:  # Show last 5 logs
        print(f"  - {log}")

    # Errors
    errors = result.get('errors', [])
    if errors:
        print(f"\nErrors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")

    # Physical Risk Scores
    physical_risk_scores = result.get('physical_risk_scores', {})
    if physical_risk_scores:
        print(f"\n[Physical Risk Scores] (H+E+V)/3 method")
        sorted_risks = sorted(
            physical_risk_scores.items(),
            key=lambda x: x[1].get('physical_risk_score_100', 0),
            reverse=True
        )
        for risk_type, risk_data in sorted_risks:
            score = risk_data.get('physical_risk_score_100', 0)
            level = risk_data.get('risk_level', 'Unknown')
            print(f"  {risk_type}: {score:.2f}/100 ({level})")

    # AAL Analysis
    aal_analysis = result.get('aal_analysis', {})
    if aal_analysis:
        print(f"\n[AAL Analysis] (Vulnerability-scaled)")
        sorted_aals = sorted(
            aal_analysis.items(),
            key=lambda x: x[1].get('final_aal_percentage', 0),
            reverse=True
        )
        for risk_type, aal_data in sorted_aals:
            aal_pct = aal_data.get('final_aal_percentage', 0)
            base_aal = aal_data.get('base_aal', 0)
            print(f"  {risk_type}: {aal_pct:.4f}% (base: {base_aal:.6f})")

    # Integrated Risks
    integrated_risks = result.get('integrated_risks', {})
    if integrated_risks:
        print(f"\n[Integrated Risk Scores]")
        sorted_integrated = sorted(
            integrated_risks.items(),
            key=lambda x: x[1].get('combined_score', 0),
            reverse=True
        )[:5]
        for risk_type, risk_data in sorted_integrated:
            combined = risk_data.get('combined_score', 0)
            print(f"  {risk_type}: {combined:.2f}/100 (combined)")

    # Building Characteristics
    building_characteristics = result.get('building_characteristics', {})
    if building_characteristics:
        print(f"\n[Building Characteristics Analysis]")
        analysis_status = building_characteristics.get('analysis_status', 'unknown')
        print(f"  Status: {analysis_status}")
        comprehensive = building_characteristics.get('comprehensive_analysis', {})
        if comprehensive:
            summary = comprehensive.get('summary', 'N/A')
            print(f"  Summary: {summary[:200]}..." if len(summary) > 200 else f"  Summary: {summary}")

    # Report Template
    report_template = result.get('report_template', {})
    if report_template:
        print(f"\n[Report Template]")
        tone = report_template.get('tone', {})
        if tone:
            print(f"  Style: {tone.get('style', 'N/A')}")
        sections = report_template.get('section_structure', {}).get('main_sections', [])
        if sections:
            print(f"  Sections: {len(sections)}")

    # Impact Analysis
    impact_analysis = result.get('impact_analysis', {})
    if impact_analysis:
        print(f"\n[Impact Analysis]")
        impact_status = impact_analysis.get('status', 'unknown')
        print(f"  Status: {impact_status}")

    # Response Strategy
    response_strategy = result.get('response_strategy', {})
    if response_strategy:
        print(f"\n[Response Strategy]")
        strategy_status = response_strategy.get('status', 'unknown')
        print(f"  Status: {strategy_status}")

    # Generated Report
    report = result.get('generated_report', {})
    if report:
        print(f"\n[Generated Report]")
        report_status = report.get('status', 'unknown')
        print(f"  Status: {report_status}")
        markdown = report.get('markdown', '')
        if markdown:
            print(f"  Length: {len(markdown)} characters")
            print(f"  Preview: {markdown[:200]}...")

    # Validation Result
    validation = result.get('validation_result', {})
    if validation:
        print(f"\n[Validation]")
        is_valid = validation.get('is_valid', False)
        print(f"  Valid: {is_valid}")
        issues = validation.get('issues', [])
        if issues:
            print(f"  Issues: {len(issues)}")
            for issue in issues[:3]:
                issue_type = issue.get('type', 'unknown') if isinstance(issue, dict) else 'unknown'
                issue_desc = issue.get('description', str(issue)) if isinstance(issue, dict) else str(issue)
                print(f"    - {issue_type}: {issue_desc}")

    # Refined Report
    refined_report = result.get('refined_report', {})
    if refined_report:
        print(f"\n[Refined Report]")
        refined_status = refined_report.get('status', 'unknown')
        print(f"  Status: {refined_status}")

    # Final Report
    final_report = result.get('final_report', {})
    if final_report:
        print(f"\n[Final Report]")
        final_status = final_report.get('status', 'unknown')
        print(f"  Status: {final_status}")

    # Output Paths
    output_paths = result.get('output_paths', {})
    if output_paths:
        print(f"\n[Output Files]")
        for format_type, path in output_paths.items():
            if path and os.path.exists(path):
                size = os.path.getsize(path) / 1024
                print(f"  {format_type}: {path} ({size:.2f} KB)")
            else:
                print(f"  {format_type}: {path} (not found)")

else:
    print("[ERROR] No final state returned")

# 7. Summary
print("\n" + "=" * 80)
print("Test Summary")
print("=" * 80)
print("[OK] Mock data loaded successfully")
print("[OK] Workflow executed (Node 2-11)")
if final_state:
    print(f"[OK] Final status: {result.get('workflow_status', 'unknown')}")
print("\nCheck LangSmith dashboard for detailed trace:")
print("https://smith.langchain.com/")
print("=" * 80)
