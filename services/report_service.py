from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime

from core.config import settings
from schemas.reports import (
    ReportGenerationRequest,
    ReportGenerationStatus,
    ReportContent,
    ReportSection,
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

    async def generate_report(self, request: ReportGenerationRequest) -> ReportGenerationStatus:
        """리포트 생성 시작"""
        report_id = uuid4()

        if settings.USE_MOCK_DATA:
            return ReportGenerationStatus(
                reportId=report_id,
                scope=request.scope,
                siteId=request.site_id,
                siteIds=request.site_ids,
                status="completed",
                progress=100,
                startedAt=datetime.now(),
                completedAt=datetime.now(),
            )

        # 실제 ai_agent 호출하여 리포트 생성
        try:
            analyzer = self._get_analyzer()

            # 단일 사업장 또는 복수 사업장 처리
            if request.scope == "single" and request.site_id:
                # 단일 사업장 분석 및 리포트 생성
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

                # 결과 캐시
                self._report_results[report_id] = {
                    'scope': request.scope,
                    'site_id': request.site_id,
                    'result': result
                }

                status = "completed" if result.get('workflow_status') == 'completed' else "failed"

                return ReportGenerationStatus(
                    reportId=report_id,
                    scope=request.scope,
                    siteId=request.site_id,
                    status=status,
                    progress=100 if status == "completed" else 0,
                    startedAt=datetime.now(),
                    completedAt=datetime.now() if status == "completed" else None,
                )

            # 복수 사업장 리포트 (all scope)
            return ReportGenerationStatus(
                reportId=report_id,
                scope=request.scope,
                siteIds=request.site_ids,
                status="queued",
                progress=0,
                startedAt=datetime.now(),
            )

        except Exception as e:
            return ReportGenerationStatus(
                reportId=report_id,
                scope=request.scope,
                siteId=request.site_id,
                siteIds=request.site_ids,
                status="failed",
                progress=0,
                startedAt=datetime.now(),
            )

    async def get_report_status(self, report_id: UUID) -> Optional[ReportGenerationStatus]:
        """리포트 생성 상태 조회"""
        if settings.USE_MOCK_DATA:
            return ReportGenerationStatus(
                reportId=report_id,
                scope="single",
                siteId=uuid4(),
                status="completed",
                progress=100,
                startedAt=datetime.now(),
                completedAt=datetime.now(),
            )

        # 캐시에서 조회
        cached = self._report_results.get(report_id)
        if cached:
            result = cached.get('result', {})
            status = "completed" if result.get('workflow_status') == 'completed' else "failed"

            return ReportGenerationStatus(
                reportId=report_id,
                scope=cached.get('scope', 'single'),
                siteId=cached.get('site_id'),
                status=status,
                progress=100 if status == "completed" else 0,
                startedAt=datetime.now(),
                completedAt=datetime.now() if status == "completed" else None,
            )

        return None

    async def get_report_content(self, report_id: UUID) -> Optional[ReportContent]:
        """리포트 컨텐츠 조회"""
        if settings.USE_MOCK_DATA:
            return ReportContent(
                reportId=report_id,
                title="기후 물리적 리스크 분석 리포트",
                generatedAt=datetime.now(),
                scope="single",
                sections=[
                    ReportSection(
                        title="1. 개요",
                        content="본 리포트는 사업장의 기후 물리적 리스크를 분석한 결과입니다. "
                                "주요 리스크 요인으로 태풍, 홍수, 가뭄이 식별되었으며, "
                                "종합 리스크 등급은 '중간'으로 평가되었습니다.",
                        order=1,
                    ),
                    ReportSection(
                        title="2. 물리적 리스크 점수",
                        content="태풍: 78.5점 (높음)\n"
                                "내륙홍수: 55.0점 (중간)\n"
                                "가뭄: 25.0점 (낮음)\n\n"
                                "총 물리적 리스크 점수: 65.5점",
                        order=2,
                    ),
                    ReportSection(
                        title="3. 재무 영향 분석",
                        content="연간 예상 손실(AAL): 125,000,000원\n"
                                "최대 예상 손실(MPL): 500,000,000원\n\n"
                                "태풍으로 인한 손실이 전체의 68%를 차지합니다.",
                        order=3,
                    ),
                    ReportSection(
                        title="4. SSP 시나리오 전망",
                        content="SSP5-8.5 시나리오 기준 2050년 전망:\n"
                                "- 물리적 리스크 점수: 78.5점 (20% 증가)\n"
                                "- AAL: 150,000,000원 (20% 증가)\n\n"
                                "기후변화에 따른 리스크 증가가 예상됩니다.",
                        order=4,
                    ),
                    ReportSection(
                        title="5. 권장 사항",
                        content="1. 태풍 대비 시설물 보강\n"
                                "2. 배수 시스템 점검 및 개선\n"
                                "3. 비상 발전기 설치\n"
                                "4. 기후 리스크 보험 가입 검토",
                        order=5,
                    ),
                ],
                summary="종합 리스크 등급 '중간', AAL 1.25억원. "
                        "태풍이 주요 리스크 요인으로 시설물 보강이 권장됩니다.",
            )

        # 캐시에서 ai_agent 결과 조회
        cached = self._report_results.get(report_id)
        if not cached:
            return None

        result = cached.get('result', {})
        generated_report = result.get('generated_report', {})

        # ai_agent 결과를 ReportContent 형식으로 변환
        sections = []
        order = 1

        # 개요 섹션
        if result.get('vulnerability_analysis'):
            sections.append(ReportSection(
                title="1. 개요",
                content=generated_report.get('executive_summary', '분석 결과 개요'),
                order=order,
            ))
            order += 1

        # 물리적 리스크 점수 섹션
        physical_risk_scores = result.get('physical_risk_scores', {})
        if physical_risk_scores:
            content_lines = []
            for risk_type, risk_data in physical_risk_scores.items():
                score = risk_data.get('physical_risk_score_100', 0)
                level = risk_data.get('risk_level', 'Unknown')
                content_lines.append(f"{risk_type}: {score:.1f}점 ({level})")

            sections.append(ReportSection(
                title="2. 물리적 리스크 점수",
                content="\n".join(content_lines),
                order=order,
            ))
            order += 1

        # 재무 영향 섹션
        total_financial_loss = sum(
            data.get('financial_loss', 0) for data in physical_risk_scores.values()
        )
        if total_financial_loss > 0:
            sections.append(ReportSection(
                title="3. 재무 영향 분석",
                content=f"총 연간 예상 손실: {total_financial_loss:,.0f}원",
                order=order,
            ))
            order += 1

        # 대응 전략 섹션
        response_strategy = result.get('response_strategy', {})
        if response_strategy:
            recommendations = response_strategy.get('recommendations', [])
            if recommendations:
                content = "\n".join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations)])
                sections.append(ReportSection(
                    title="4. 권장 사항",
                    content=content,
                    order=order,
                ))

        return ReportContent(
            reportId=report_id,
            title="기후 물리적 리스크 분석 리포트",
            generatedAt=datetime.now(),
            scope=cached.get('scope', 'single'),
            sections=sections,
            summary=generated_report.get('executive_summary', ''),
        )

    async def get_report_file(self, report_id: UUID, format: str) -> Optional[str]:
        """리포트 파일 경로 반환"""
        if settings.USE_MOCK_DATA:
            # Mock 파일 경로 반환
            return f"/reports/{report_id}.{format}"

        # 실제로는 PDF/DOCX 생성 로직 필요
        # ai_agent의 generated_report를 파일로 변환
        cached = self._report_results.get(report_id)
        if not cached:
            return None

        # TODO: PDF/DOCX 파일 생성 구현
        return f"/reports/{report_id}.{format}"
