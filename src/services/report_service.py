from uuid import UUID, uuid4
from datetime import datetime, timedelta

from src.core.config import settings
from src.schemas.reports import (
    CreateReportRequest,
    ReportWebViewResponse,
    ReportPdfResponse,
    ReportPage,
)

# ai_agent 호출
from ai_agent import SKAXPhysicalRiskAnalyzer
from ai_agent.config.settings import load_config


class ReportService:
    """리포트 서비스 - ai_agent의 LLM을 사용하여 리포트 생성"""

    def __init__(self):
        """서비스 초기화"""
        self._analyzer = None
        self._report_results = {}  # report_id별 결과 캐시

    def _get_analyzer(self) -> SKAXPhysicalRiskAnalyzer:
        """ai_agent 분석기 인스턴스 반환 (lazy initialization)"""
        if self._analyzer is None:
            config = load_config()
            self._analyzer = SKAXPhysicalRiskAnalyzer(config)
        return self._analyzer

    async def create_report(self, request: CreateReportRequest) -> dict:
        """Spring Boot API 호환 - 리포트 생성"""
        if settings.USE_MOCK_DATA:
            return {
                "success": True,
                "message": "리포트가 생성되었습니다.",
                "siteId": str(request.site_id) if request.site_id else None,
            }

        # 실제 ai_agent 호출하여 리포트 생성
        try:
            analyzer = self._get_analyzer()

            if request.site_id:
                target_location = {
                    'latitude': 37.5665,  # 실제로는 DB에서 조회
                    'longitude': 126.9780,
                    'name': f'Site-{request.site_id}'
                }

                building_info = {
                    'building_age': 20,
                    'has_seismic_design': True,
                    'fire_access': True
                }

                asset_info = {
                    'total_asset_value': 50000000000,
                    'insurance_coverage_rate': 0.7
                }

                analysis_params = {
                    'time_horizon': '2050',
                    'analysis_period': '2025-2050'
                }

                result = analyzer.analyze(target_location, building_info, asset_info, analysis_params)

                report_id = uuid4()
                self._report_results[report_id] = {
                    'site_id': request.site_id,
                    'result': result
                }

                return {
                    "success": True,
                    "message": "리포트가 생성되었습니다.",
                    "siteId": str(request.site_id),
                }

            return {
                "success": True,
                "message": "전체 사업장 리포트가 생성되었습니다.",
            }

        except Exception as e:
            return {
                "success": False,
                "message": str(e),
            }

    async def get_report_web_view(self) -> ReportWebViewResponse:
        """Spring Boot API 호환 - 웹 리포트 뷰 조회"""
        if settings.USE_MOCK_DATA:
            pages = [
                ReportPage(
                    pageNumber=1,
                    imageUrl="/reports/images/cover.png",
                    title="기후 물리적 리스크 분석 리포트",
                ),
                ReportPage(
                    pageNumber=2,
                    imageUrl="/reports/images/overview.png",
                    title="분석 개요",
                ),
                ReportPage(
                    pageNumber=3,
                    imageUrl="/reports/images/physical-risk.png",
                    title="물리적 리스크 점수",
                ),
                ReportPage(
                    pageNumber=4,
                    imageUrl="/reports/images/financial-impact.png",
                    title="재무 영향 분석",
                ),
                ReportPage(
                    pageNumber=5,
                    imageUrl="/reports/images/ssp-projection.png",
                    title="SSP 시나리오 전망",
                ),
                ReportPage(
                    pageNumber=6,
                    imageUrl="/reports/images/recommendations.png",
                    title="권장 사항",
                ),
            ]

            return ReportWebViewResponse(
                siteId=None,
                pages=pages,
            )

        return None

    async def get_report_pdf(self) -> ReportPdfResponse:
        """Spring Boot API 호환 - PDF 리포트 조회"""
        if settings.USE_MOCK_DATA:
            return ReportPdfResponse(
                downloadUrl="/reports/download/climate-risk-report.pdf",
                fileSize=2048576,  # 2MB
                expiresAt=datetime.now() + timedelta(hours=24),
            )

        return None

    async def delete_report(self) -> dict:
        """Spring Boot API 호환 - 리포트 삭제"""
        if settings.USE_MOCK_DATA:
            return {
                "success": True,
                "message": "리포트가 삭제되었습니다.",
            }

        # 캐시 초기화
        self._report_results.clear()

        return {
            "success": True,
            "message": "리포트가 삭제되었습니다.",
        }
