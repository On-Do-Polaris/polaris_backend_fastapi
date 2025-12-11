'''
파일명: test_workflow_mock.py
생성일: 2025-12-11
버전: v01
파일 개요: Workflow Mock 데이터 테스트 스크립트
'''
import os
import sys

# 환경변수 설정 (import 전에 설정해야 함)
os.environ['WORKFLOW_MOCK_MODE'] = 'true'

# 프로젝트 루트를 sys.path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_agent.main import SKAXPhysicalRiskAnalyzer
from ai_agent.config.settings import Config


def test_workflow_with_mock():
    """
    Mock 데이터로 Workflow 전체 실행 테스트

    실행 흐름:
    1. Node 1 (Data Collection) - Mock 기후 데이터 반환
    2. Node 3 (Risk Assessment) - Mock H×E×V×AAL 반환
    3. Node 5~10 - 실제 LLM 로직 실행
    """
    print("=" * 70)
    print("Workflow Mock Data Test")
    print("=" * 70)
    print()

    # Config 초기화
    config = Config()

    # Mock 모드 확인
    print(f"WORKFLOW_MOCK_MODE: {config.WORKFLOW_MOCK_MODE}")

    if not config.WORKFLOW_MOCK_MODE:
        print("[ERROR] WORKFLOW_MOCK_MODE가 활성화되지 않았습니다!")
        print("환경변수 WORKFLOW_MOCK_MODE=true 를 설정하세요.")
        return

    print()

    # Analyzer 초기화
    print("[1/3] SKAXPhysicalRiskAnalyzer 초기화...")
    analyzer = SKAXPhysicalRiskAnalyzer(config)
    print("✓ Analyzer 초기화 완료")
    print()

    # Mock 입력 데이터 준비
    print("[2/3] Mock 입력 데이터 준비...")
    target_location = {
        'latitude': 37.5665,
        'longitude': 126.9780,
        'name': 'Seoul Test Site'
    }

    building_info = {
        'building_age': 25,
        'structure': 'reinforced_concrete',
        'seismic_design': True,
        'gross_floor_area': 5000
    }

    asset_info = {
        'total_asset_value': 50000000000,  # 500억원
        'insurance_coverage_rate': 0.7
    }

    analysis_params = {
        'time_horizon': '2050',
        'analysis_period': '2025-2050'
    }

    print(f"  - Location: {target_location['name']}")
    print(f"  - Building Age: {building_info['building_age']}년")
    print(f"  - Asset Value: {asset_info['total_asset_value']:,}원")
    print()

    # Workflow 실행
    print("[3/3] Workflow 실행 시작...")
    print("-" * 70)

    try:
        result = analyzer.analyze(
            target_location=target_location,
            building_info=building_info,
            asset_info=asset_info,
            analysis_params=analysis_params,
            language='ko'
        )

        print("-" * 70)
        print()

        # 결과 요약
        print("=" * 70)
        print("Test Result Summary")
        print("=" * 70)

        status = result.get('workflow_status', 'unknown')
        print(f"✓ Workflow Status: {status}")

        # 로그 출력
        logs = result.get('logs', [])
        if logs:
            print(f"\n✓ Completed Steps: {len(logs)}")
            for i, log in enumerate(logs[:5], 1):  # 처음 5개만 출력
                print(f"  {i}. {log}")
            if len(logs) > 5:
                print(f"  ... and {len(logs) - 5} more")

        # 에러 확인
        errors = result.get('errors', [])
        if errors:
            print(f"\n⚠ Errors: {len(errors)}")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")

        # Physical Risk Scores 확인
        physical_risk_scores = result.get('physical_risk_scores', {})
        if physical_risk_scores:
            print(f"\n✓ Physical Risk Scores: {len(physical_risk_scores)}개")
            for risk_type, risk_data in list(physical_risk_scores.items())[:3]:
                score = risk_data.get('physical_risk_score_100', 0)
                level = risk_data.get('risk_level', 'Unknown')
                print(f"  - {risk_type}: {score:.2f}/100 ({level})")

        # Building Characteristics 확인
        building_characteristics = result.get('building_characteristics', {})
        if building_characteristics:
            analysis_status = building_characteristics.get('analysis_status', 'unknown')
            print(f"\n✓ Building Characteristics: {analysis_status}")

        # Report 확인
        generated_report = result.get('generated_report')
        if generated_report:
            print(f"\n✓ Generated Report: Available")
            if isinstance(generated_report, dict):
                markdown_len = len(generated_report.get('markdown', ''))
                print(f"  - Markdown Length: {markdown_len} chars")

        # Validation 확인
        validation_result = result.get('validation_result', {})
        if validation_result:
            is_valid = validation_result.get('is_valid', False)
            print(f"\n✓ Validation: {'Passed' if is_valid else 'Failed'}")

        print()
        print("=" * 70)
        print("✅ Test Completed Successfully!")
        print("=" * 70)

        return result

    except Exception as e:
        print("-" * 70)
        print()
        print("=" * 70)
        print("❌ Test Failed!")
        print("=" * 70)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_workflow_with_mock()

    if result and result.get('workflow_status') == 'completed':
        sys.exit(0)  # 성공
    else:
        sys.exit(1)  # 실패
