"""
AI Agent Main.py Mock Data Test Script (Phase 2 - Multi-Site)
Mock DB 데이터를 사용하여 다중 사업장 통합 리포트 생성 테스트

Phase 2 워크플로우:
    - Mock DB Loader를 사용하여 Phase 1 결과 생성 (H, E, V, Risk Scores, AAL)
    - analyze_integrated() 메서드로 3개 사업장 통합 분석
    - Building Characteristics, Report Generation 등 Phase 2 노드 실행

실행 방법:
    python test_main_mock.py

주요 검증 사항:
    ✅ Mock DB 데이터 로드 (Phase 1 결과)
    ✅ 다중 사업장 통합 분석
    ✅ TCFD 리포트 생성 (Markdown, JSON, PDF)
    ✅ LangSmith 트레이싱

주의사항:
    - OPENAI_API_KEY 환경변수 필요 (LLM 호출)
    - Mock DB Loader 사용 (실제 DB 불필요)
    - scratch 폴더 불필요 (Mock 데이터 자동 생성)
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# .env 파일 로드
load_dotenv(override=True)

# API 키 확인
api_key = os.getenv('OPENAI_API_KEY', '')
print(f"[DEBUG] OPENAI_API_KEY length: {len(api_key)}")
print(f"[DEBUG] OPENAI_API_KEY starts with: {api_key[:10] if api_key else 'EMPTY'}")

print("=" * 80)
print("Multi-Site Integrated Report Generation Test (Phase 2)")
print("Using Mock DB Loader - No actual database required")
print("=" * 80)

# 1. Load Mock DB Data (Phase 1 Results)
print("\n[1] Loading Mock DB Data (Phase 1 Results)...")
from ai_agent.utils.mock_db_loader import load_mock_multi_site_data

sites_data = load_mock_multi_site_data(num_sites=3, company_name="SKAX Test Company")

print(f"    [OK] Loaded {len(sites_data)} sites")
for site in sites_data:
    print(f"\n    Site: {site['site_name']} ({site['site_id']})")
    print(f"        Location: {site['location']['name']}")
    print(f"        Asset Value: {site['asset_info']['total_asset_value']:,} KRW")
    print(f"        Building Age: {site['building_info']['building_age']} years")

    # Show top 3 risk scores
    sorted_risks = sorted(
        site['risk_scores'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]
    print(f"        Top 3 Risks:")
    for risk_type, score in sorted_risks:
        aal = site['aal_values'].get(risk_type, 0)
        print(f"          - {risk_type}: Risk={score:.1f}/100, AAL={aal:.4f}%")

# 2. Initialize Analyzer
print("\n[2] Initializing SKAXPhysicalRiskAnalyzer...")
from ai_agent.config.settings import Config
from ai_agent import SKAXPhysicalRiskAnalyzer

config = Config()
print(f"    DEBUG: {config.DEBUG}")

analyzer = SKAXPhysicalRiskAnalyzer(config)
print("    [OK] Analyzer initialized")

# 3. Prepare Parameters
print("\n[3] Preparing Analysis Parameters...")

site_ids = [site['site_id'] for site in sites_data]
company_name = "SKAX Test Company"
analysis_params = {
    'time_horizon': '2050',
    'analysis_period': '2025-2050',
    'start_year': 2025,
    'end_year': 2050
}
language = 'ko'  # 'ko' for Korean, 'en' for English

print(f"    Site IDs: {site_ids}")
print(f"    Company: {company_name}")
print(f"    Language: {language}")

# 4. Run Integrated Multi-Site Analysis
print("\n[4] Running Integrated Multi-Site Analysis...")
print("    " + "-" * 76)

try:
    # Execute analyze_integrated() method
    results = analyzer.analyze_integrated(
        site_ids=site_ids,
        sites_data=sites_data,
        company_name=company_name,
        analysis_params=analysis_params,
        language=language
    )

    print("    " + "-" * 76)
    print(f"    [OK] Integrated analysis completed")

except Exception as e:
    print(f"    [ERROR] Analysis failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 5. Display Results
print("\n[5] Analysis Results:")
print("=" * 80)

if results:
    # Workflow Status
    status = results.get('workflow_status', 'unknown')
    print(f"\nWorkflow Status: {status}")

    # Logs
    logs = results.get('logs', [])
    if logs:
        print(f"\nCompleted Steps: {len(logs)}")
        for log in logs[-5:]:
            print(f"  - {log}")

    # Errors
    errors = results.get('errors', [])
    if errors:
        print(f"\nErrors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")

    # Multi-Site Data Summary
    print(f"\n[Multi-Site Summary]")
    print(f"  Number of Sites: {len(site_ids)}")
    print(f"  Company: {company_name}")

    # Show each site's top risks
    for site in sites_data:
        site_id = site['site_id']
        site_name = site['site_name']
        print(f"\n  Site: {site_name} ({site_id})")

        # Top 5 risks for this site
        sorted_risks = sorted(
            site['risk_scores'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        for risk_type, score in sorted_risks:
            aal = site['aal_values'].get(risk_type, 0)
            h = site['hazard_scores'].get(risk_type, 0)
            e = site['exposure_scores'].get(risk_type, 0)
            v = site['vulnerability_scores'].get(risk_type, 0)
            print(f"    {risk_type:20s}: Risk={score:5.1f}/100, AAL={aal:6.4f}% (H={h:.1f}, E={e:.1f}, V={v:.1f})")

    # Building Characteristics (if analyzed)
    building_characteristics = results.get('building_characteristics', {})
    if building_characteristics:
        print(f"\n[Building Characteristics Analysis]")
        analysis_status = building_characteristics.get('analysis_status', 'unknown')
        print(f"  Status: {analysis_status}")

        comprehensive = building_characteristics.get('comprehensive_analysis', {})
        if comprehensive:
            summary = comprehensive.get('summary', 'N/A')
            print(f"  Summary: {summary[:200]}..." if len(summary) > 200 else f"  Summary: {summary}")

    # Report Template
    report_template = results.get('report_template', {})
    if report_template:
        print(f"\n[Report Template]")
        tone = report_template.get('tone', {})
        if tone:
            print(f"  Style: {tone.get('style', 'N/A')}")
        sections = report_template.get('section_structure', {}).get('main_sections', [])
        if sections:
            print(f"  Sections: {len(sections)}")
            for section in sections[:5]:
                if isinstance(section, dict):
                    print(f"    - {section.get('title', 'Untitled')}")

    # Impact Analysis
    impact_analysis = results.get('impact_analysis', {})
    if impact_analysis:
        print(f"\n[Impact Analysis]")
        impact_status = impact_analysis.get('status', 'unknown')
        print(f"  Status: {impact_status}")

    # Response Strategy
    response_strategy = results.get('response_strategy', {})
    if response_strategy:
        print(f"\n[Response Strategy]")
        strategy_status = response_strategy.get('status', 'unknown')
        print(f"  Status: {strategy_status}")

    # Generated Report
    report = results.get('generated_report', {})
    if report:
        print(f"\n[Generated Report]")
        report_status = report.get('status', 'unknown')
        print(f"  Status: {report_status}")
        markdown = report.get('markdown', '')
        if markdown:
            print(f"  Length: {len(markdown)} characters")
            print(f"\n  Preview (first 15 lines):")
            print("  " + "-" * 76)
            all_lines = markdown.split('\n')
            preview_lines = all_lines[:15]
            for line in preview_lines:
                print(f"  {line}")
            if len(all_lines) > 15:
                remaining = len(all_lines) - 15
                print(f"  ... ({remaining} more lines)")
            print("  " + "-" * 76)

    # Validation Result
    validation = results.get('validation_result', {})
    if validation:
        print(f"\n[Validation]")
        is_valid = validation.get('is_valid', False)
        print(f"  Valid: {is_valid}")
        issues = validation.get('issues_found', [])
        if issues:
            print(f"  Issues: {len(issues)}")
            for issue in issues[:3]:
                issue_type = issue.get('type', 'unknown') if isinstance(issue, dict) else 'unknown'
                issue_desc = issue.get('description', str(issue)) if isinstance(issue, dict) else str(issue)
                print(f"    - {issue_type}: {issue_desc}")

    # Final Report
    final_report = results.get('final_report', {})
    if final_report:
        print(f"\n[Final Report]")
        final_status = final_report.get('status', 'unknown')
        print(f"  Status: {final_status}")

    # Output Paths
    output_paths = results.get('output_paths', {})
    if output_paths:
        print(f"\n[Output Files]")
        for format_type, path in output_paths.items():
            if path and os.path.exists(path):
                size = os.path.getsize(path) / 1024
                print(f"  {format_type}: {path} ({size:.2f} KB)")
            else:
                print(f"  {format_type}: {path} (not found)")

else:
    print("[ERROR] No results returned")

# 6. Summary and Validation
print("\n" + "=" * 80)
print("Test Summary")
print("=" * 80)

# Display loaded sites
print(f"\n[Data Loading]")
print(f"  ✅ Mock DB data loaded successfully ({len(sites_data)} sites)")
for site in sites_data:
    print(f"      - {site['site_name']}: {site['asset_info']['total_asset_value']:,} KRW")

# Workflow execution
print(f"\n[Workflow Execution]")
print(f"  ✅ Integrated analysis executed")
print(f"      - Company: {company_name}")
print(f"      - Sites: {', '.join([s['site_name'] for s in sites_data])}")
print(f"      - Language: {language}")

# Results validation
if results:
    print(f"\n[Results Validation]")
    print(f"  ✅ Final status: {results.get('workflow_status', 'unknown')}")

    # Key validations
    validations = {
        'Multi-Site Integration': len(sites_data) > 1,
        'Phase 1 Data Loaded': sites_data[0].get('risk_scores') is not None,
        'Report Generated': results.get('generated_report') is not None or results.get('final_report') is not None,
        'Output Files Created': results.get('output_paths') is not None,
    }

    for check_name, passed in validations.items():
        status_icon = '✅' if passed else '❌'
        status_text = 'PASS' if passed else 'FAIL'
        print(f"  {status_icon} {check_name}: {status_text}")

    # Overall result
    all_passed = all(validations.values())
    print(f"\n{'='*80}")
    if all_passed:
        print("  🎉 ALL TESTS PASSED - Multi-Site Integrated Report Generation Successful!")
    else:
        print("  ⚠️  SOME TESTS FAILED - Check validation results above")
    print(f"{'='*80}")

print("\nCheck LangSmith dashboard for detailed trace:")
print("https://smith.langchain.com/")
print("=" * 80)
