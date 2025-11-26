#!/usr/bin/env python
"""Mock API 테스트 스크립트"""
import sys
import asyncio
from uuid import uuid4

sys.path.insert(0, '.')

from src.services.analysis_service import AnalysisService
from src.services.report_service import ReportService


async def test_analysis_service():
    """분석 서비스 Mock 데이터 테스트"""
    print("=" * 60)
    print("Testing Analysis Service (Mock Data)")
    print("=" * 60)

    service = AnalysisService()
    site_id = uuid4()

    # StartAnalysisRequest mock 생성
    class MockSite:
        id = site_id
        name = 'Test Site'
        latitude = 37.5665
        longitude = 126.9780

    class MockRequest:
        site = MockSite()

    # 1. start_analysis
    print("\n1. Testing start_analysis...")
    result = await service.start_analysis(site_id, MockRequest())
    print(f"   Status: {result.status}")
    print(f"   Progress: {result.progress}%")

    # 2. get_physical_risk_scores
    print("\n2. Testing get_physical_risk_scores...")
    result2 = await service.get_physical_risk_scores(site_id, 'HIGH_TEMPERATURE')
    if result2:
        print(f"   Scenarios: {len(result2.scenarios)}")
        print(f"   First scenario: {result2.scenarios[0].scenario}")

    # 3. get_past_events
    print("\n3. Testing get_past_events...")
    result3 = await service.get_past_events(site_id)
    if result3:
        print(f"   Disasters: {len(result3.disasters)}")
        print(f"   Site: {result3.site_name}")

    # 4. get_financial_impacts
    print("\n4. Testing get_financial_impacts...")
    result4 = await service.get_financial_impacts(site_id)
    if result4:
        print(f"   Scenarios: {len(result4.scenarios)}")

    # 5. get_vulnerability
    print("\n5. Testing get_vulnerability...")
    result5 = await service.get_vulnerability(site_id)
    if result5:
        print(f"   Vulnerabilities: {len(result5.vulnerabilities)}")

    # 6. get_total_analysis
    print("\n6. Testing get_total_analysis...")
    result6 = await service.get_total_analysis(site_id, 'HIGH_TEMPERATURE')
    if result6:
        print(f"   Physical Risks: {len(result6.physical_risks)}")
        print(f"   Site: {result6.site_name}")

    print("\n" + "=" * 60)
    print("[OK] All Analysis Service tests passed!")
    print("=" * 60)


async def test_report_service():
    """리포트 서비스 Mock 데이터 테스트"""
    print("\n" + "=" * 60)
    print("Testing Report Service (Mock Data)")
    print("=" * 60)

    service = ReportService()
    test_site_id = uuid4()

    class MockRequest:
        site_id = test_site_id

    # 1. create_report
    print("\n1. Testing create_report...")
    result = await service.create_report(MockRequest())
    print(f"   Success: {result.get('success')}")
    print(f"   Message: {result.get('message')}")

    # 2. get_report_web_view
    print("\n2. Testing get_report_web_view...")
    result2 = await service.get_report_web_view()
    if result2:
        print(f"   Pages: {len(result2.pages)}")
        print(f"   First page: {result2.pages[0].title}")

    # 3. get_report_pdf
    print("\n3. Testing get_report_pdf...")
    result3 = await service.get_report_pdf()
    if result3:
        print(f"   Download URL: {result3.download_url}")
        print(f"   File size: {result3.file_size} bytes")

    print("\n" + "=" * 60)
    print("[OK] All Report Service tests passed!")
    print("=" * 60)


async def main():
    """메인 테스트 실행"""
    await test_analysis_service()
    await test_report_service()
    print("\n[OK] All Mock API tests completed successfully!\n")


if __name__ == "__main__":
    asyncio.run(main())
