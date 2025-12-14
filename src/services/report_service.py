from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

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
        self._user_reports = {}  # user_id → [report_ids] 매핑 (In-Memory)
        self._additional_data = {}  # user_id → Spring Boot 추가 데이터 (In-Memory)
        self._executor = ThreadPoolExecutor(max_workers=4)  # 비동기 실행용 Thread Pool

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

                # Language 파라미터 전달
                language = request.language.value if request.language else 'ko'

                # 비동기 실행: 동기 함수를 별도 스레드에서 실행하여 이벤트 루프 블로킹 방지
                loop = asyncio.get_event_loop()
                analyze_func = partial(
                    analyzer.analyze,
                    target_location,
                    building_info,
                    asset_info,
                    analysis_params,
                    language=language
                )
                result = await loop.run_in_executor(self._executor, analyze_func)

                # 리포트 ID 생성 및 결과 캐싱
                report_id = uuid4()
                user_id = getattr(request, 'user_id', None)  # userId 추출 (나중에 스키마 추가)

                self._report_results[report_id] = {
                    'site_id': request.site_id,
                    'user_id': user_id,
                    'result': result,
                    'created_at': datetime.now()
                }

                # userId → reportId 매핑 저장
                if user_id:
                    if user_id not in self._user_reports:
                        self._user_reports[user_id] = []
                    self._user_reports[user_id].append(report_id)

                return {
                    "success": True,
                    "message": "리포트가 생성되었습니다.",
                    "siteId": str(request.site_id),
                    "reportId": str(report_id),
                    "userId": str(user_id) if user_id else None
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

    async def get_report_web_view(self, report_id: str) -> dict:
        """웹 리포트 뷰 조회 - 프론트엔드 렌더링용 데이터 반환"""
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

        # 실제 리포트 데이터 조회
        try:
            from uuid import UUID
            report_uuid = UUID(report_id)
            cached_report = self._report_results.get(report_uuid)

            if not cached_report:
                return None

            result = cached_report.get('result', {})
            final_report = result.get('final_report', {})

            # 웹 렌더링용 데이터 반환
            return {
                "siteId": str(cached_report['site_id']) if cached_report.get('site_id') else None,
                "reportData": {
                    "markdown": final_report.get('markdown', ''),
                    "json": final_report.get('json', {}),
                    "metadata": result.get('metadata', {}),
                },
                "createdAt": cached_report.get('created_at').isoformat() if cached_report.get('created_at') else None,
            }
        except Exception as e:
            print(f"Error retrieving web view: {e}")
            return None

    async def get_report_pdf(self, report_id: str) -> dict:
        """PDF 리포트 파일 경로 조회"""
        if settings.USE_MOCK_DATA:
            return ReportPdfResponse(
                downloadUrl="/reports/download/climate-risk-report.pdf",
                fileSize=2048576,  # 2MB
                expiresAt=datetime.now() + timedelta(hours=24),
            )

        # 실제 PDF 파일 경로 조회
        try:
            from uuid import UUID
            import os

            report_uuid = UUID(report_id)
            cached_report = self._report_results.get(report_uuid)

            if not cached_report:
                return None

            result = cached_report.get('result', {})
            output_paths = result.get('output_paths', {})
            pdf_path = output_paths.get('pdf')

            if not pdf_path or not os.path.exists(pdf_path):
                return None

            # 파일 크기 계산
            file_size = os.path.getsize(pdf_path)

            return {
                "pdfPath": pdf_path,
                "fileSize": file_size,
                "siteId": str(cached_report['site_id']) if cached_report.get('site_id') else None,
                "createdAt": cached_report.get('created_at').isoformat() if cached_report.get('created_at') else None,
            }
        except Exception as e:
            print(f"Error retrieving PDF: {e}")
            return None

    async def get_reports_by_user_id(self, user_id) -> Optional[dict]:
        """
        userId로 리포트 조회 (Spring Boot 호환)

        Args:
            user_id: 사용자 ID (UUID 또는 문자열)

        Returns:
            최신 리포트 데이터 또는 None
        """
        # userId로 reportId 목록 조회
        report_ids = self._user_reports.get(user_id, [])

        if not report_ids:
            return None

        # 최신 리포트 반환 (마지막 항목)
        latest_report_id = report_ids[-1]
        return await self.get_report_web_view(str(latest_report_id))

    async def get_latest_report_by_user(self, user_id) -> Optional[dict]:
        """
        userId로 최신 리포트 조회

        Args:
            user_id: 사용자 ID

        Returns:
            최신 리포트 또는 None
        """
        return await self.get_reports_by_user_id(user_id)

    async def register_report_data(self, user_id, data: dict) -> dict:
        """
        리포트 추가 데이터 등록 (Spring Boot 호환)

        Spring Boot에서 전송한 추가 데이터를 메모리에 저장하여
        AI Agent가 리포트 생성 시 사용할 수 있도록 합니다.

        Args:
            user_id: 사용자 ID
            data: Spring Boot에서 전송한 추가 데이터

        Returns:
            등록 결과 (success, message, userId, dataKeys, registeredAt)
        """
        # 사용자별 추가 데이터 저장
        self._additional_data[user_id] = {
            'data': data,
            'registered_at': datetime.now(),
            'user_id': user_id
        }

        return {
            "success": True,
            "message": "리포트 추가 데이터가 등록되었습니다.",
            "userId": str(user_id),
            "dataKeys": list(data.keys()),
            "registeredAt": datetime.now().isoformat()
        }

    def get_additional_data(self, user_id) -> Optional[dict]:
        """
        사용자의 추가 데이터 조회 (AI Agent용)

        Args:
            user_id: 사용자 ID

        Returns:
            저장된 추가 데이터 또는 None
        """
        cached = self._additional_data.get(user_id)
        if cached:
            return cached.get('data')
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
        self._user_reports.clear()

        return {
            "success": True,
            "message": "리포트가 삭제되었습니다.",
        }

    def shutdown(self):
        """Cleanup thread pool executor on app shutdown"""
        if self._executor:
            import logging
            logger = logging.getLogger("api")
            logger.info("Shutting down ReportService thread pool executor")
            self._executor.shutdown(wait=True)
            self._executor = None
