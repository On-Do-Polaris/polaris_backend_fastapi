from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import os
import shutil
from pathlib import Path
import logging

from src.core.config import settings
from src.schemas.reports import (
    CreateReportRequest,
    ReportWebViewResponse,
    ReportPdfResponse,
    ReportPage,
)

# NEW: tcfd_report 파이프라인 사용 (report_generation 폴더 의존성 제거)
# DEPRECATED: SKAXPhysicalRiskAnalyzer (report_generation 의존)


class ReportService:
    """리포트 서비스 - tcfd_report 파이프라인을 사용하여 TCFD 리포트 생성"""

    def __init__(self):
        """서비스 초기화"""
        self._report_results = {}  # report_id별 결과 캐시
        self._user_reports = {}  # user_id → [report_ids] 매핑 (In-Memory)
        self._additional_data = {}  # user_id → Spring Boot 추가 데이터 (In-Memory)
        self._executor = ThreadPoolExecutor(max_workers=4)  # 비동기 실행용 Thread Pool
        self.logger = logging.getLogger("api.services.report")

    async def create_report(self, request: CreateReportRequest) -> dict:
        """
        Spring Boot API 호환 - TCFD 리포트 생성

        NEW: tcfd_report 파이프라인 사용 (Node 0-6)
        - report_generation 폴더 의존성 제거됨
        - LangGraph 기반 워크플로우 실행
        """
        if settings.USE_MOCK_DATA:
            return {
                "success": True,
                "message": "리포트가 생성되었습니다.",
                "siteId": str(request.site_id) if request.site_id else None,
            }

        # 실제 tcfd_report 파이프라인 호출
        try:
            # site_ids 준비 (단일 또는 다중)
            site_ids = []
            if request.site_id:
                site_ids = [str(request.site_id)]
            elif hasattr(request, 'site_ids') and request.site_ids:
                site_ids = [str(sid) for sid in request.site_ids]

            if not site_ids:
                return {
                    "success": False,
                    "message": "site_id 또는 site_ids가 필요합니다.",
                }

            user_id = getattr(request, 'user_id', None)

            # tcfd_report 파이프라인 실행
            result = await self._run_tcfd_pipeline(
                site_ids=site_ids,
                user_id=str(user_id) if user_id else None
            )

            if result.get('success'):
                report_id = result.get('report_id')

                # 캐시에 저장
                if report_id:
                    self._report_results[UUID(report_id)] = {
                        'site_id': request.site_id,
                        'user_id': user_id,
                        'result': result,
                        'created_at': datetime.now()
                    }

                    # userId → reportId 매핑 저장
                    if user_id:
                        if user_id not in self._user_reports:
                            self._user_reports[user_id] = []
                        self._user_reports[user_id].append(UUID(report_id))

                return {
                    "success": True,
                    "message": "TCFD 리포트가 생성되었습니다.",
                    "siteId": str(request.site_id) if request.site_id else None,
                    "reportId": report_id,
                    "userId": str(user_id) if user_id else None
                }
            else:
                return {
                    "success": False,
                    "message": result.get('error', '리포트 생성 실패'),
                }

        except Exception as e:
            self.logger.error(f"TCFD 리포트 생성 실패: {e}", exc_info=True)
            return {
                "success": False,
                "message": str(e),
            }

    async def _run_tcfd_pipeline(self, site_ids: List[str], user_id: Optional[str] = None) -> dict:
        """
        tcfd_report 파이프라인 실행 (Node 0-6)

        Args:
            site_ids: 사업장 ID 리스트
            user_id: 사용자 ID (선택)

        Returns:
            {
                'success': bool,
                'report_id': str,
                'error': str (실패 시)
            }
        """
        try:
            from ai_agent.agents.tcfd_report.workflow import create_tcfd_workflow
            from ai_agent.agents.tcfd_report.state import TCFDReportState
            from ai_agent.utils.database import DatabaseManager
            from langchain_openai import ChatOpenAI
            from qdrant_client import QdrantClient

            self.logger.info(f"[TCFD] 파이프라인 시작: site_ids={site_ids}, user_id={user_id}")

            # 의존성 초기화
            # Application DB 접속 (reports 테이블 저장용)
            db_session = DatabaseManager(
                db_host=os.environ.get('APPLICATION_DB_HOST'),
                db_port=os.environ.get('APPLICATION_DB_PORT', '5432'),
                db_name=os.environ.get('APPLICATION_DB_NAME'),
                db_user=os.environ.get('APPLICATION_DB_USER'),
                db_password=os.environ.get('APPLICATION_DB_PASSWORD')
            )

            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.7,
                api_key=os.environ.get('OPENAI_API_KEY')
            )

            # Qdrant 클라이언트 (없으면 None으로 전달)
            try:
                qdrant_client = QdrantClient(
                    host=os.environ.get('QDRANT_HOST', 'localhost'),
                    port=int(os.environ.get('QDRANT_PORT', 6333))
                )
            except Exception as e:
                self.logger.warning(f"[TCFD] Qdrant 연결 실패 (RAG 비활성화): {e}")
                qdrant_client = None

            # 초기 상태 설정
            initial_state: TCFDReportState = {
                "site_ids": site_ids,
                "user_id": user_id,
                "target_years": list(range(2024, 2024 + 9)),  # 9년
                "errors": [],
                "current_step": "initialized"
            }

            # 워크플로우 생성 및 실행
            workflow = create_tcfd_workflow(db_session, llm, qdrant_client)

            # 비동기 실행
            loop = asyncio.get_event_loop()
            final_state = await loop.run_in_executor(
                self._executor,
                lambda: workflow.invoke(initial_state)
            )

            # 결과 확인
            if final_state.get('errors'):
                self.logger.error(f"[TCFD] 파이프라인 오류: {final_state['errors']}")
                return {
                    'success': False,
                    'error': '; '.join(final_state['errors'])
                }

            report_id = final_state.get('report_id')
            self.logger.info(f"[TCFD] 파이프라인 완료: report_id={report_id}")

            return {
                'success': True,
                'report_id': report_id,
                'final_state': final_state
            }

        except ImportError as e:
            self.logger.error(f"[TCFD] 모듈 import 실패: {e}")
            return {
                'success': False,
                'error': f"tcfd_report 모듈 로드 실패: {e}"
            }
        except Exception as e:
            self.logger.error(f"[TCFD] 파이프라인 실행 실패: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
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

            # Spring Boot 호환 형식으로 변환
            return self._transform_to_spring_format(report_id, final_report, cached_report)
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

    async def register_report_data(self, user_id: UUID, site_id: UUID, file) -> dict:
        """
        리포트 추가 데이터 등록 (파일 포함) (Spring Boot 호환)

        Spring Boot에서 전송한 파일을 scratch/{siteId}/ 폴더에 저장합니다.

        Args:
            user_id: 사용자 ID
            site_id: 사업장 ID
            file: 업로드된 파일 (UploadFile)

        Returns:
            등록 결과 (success, message, userId, siteId, fileName, filePath, registeredAt)
        """
        try:
            # scratch/{siteId} 폴더 경로 생성
            base_dir = Path("scratch")
            site_dir = base_dir / str(site_id)

            # 폴더가 없으면 생성
            site_dir.mkdir(parents=True, exist_ok=True)

            # 파일 저장 경로 설정
            file_path = site_dir / file.filename

            # 파일 저장
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            # 메타데이터 저장 (기존 로직 유지)
            self._additional_data[user_id] = {
                'site_id': site_id,
                'file_name': file.filename,
                'file_path': str(file_path),
                'file_size': len(content),
                'content_type': file.content_type,
                'registered_at': datetime.now(),
                'user_id': user_id
            }

            return {
                "success": True,
                "message": "리포트 데이터 파일이 등록되었습니다.",
                "userId": str(user_id),
                "siteId": str(site_id),
                "fileName": file.filename,
                "filePath": str(file_path),
                "fileSize": len(content),
                "registeredAt": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"파일 저장 중 오류 발생: {str(e)}",
                "userId": str(user_id),
                "siteId": str(site_id)
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

    def _transform_to_spring_format(self, report_id: str, final_report: dict, cached_report: dict) -> dict:
        """
        AI Agent 결과를 Spring Boot 호환 형식으로 변환

        Args:
            report_id: 리포트 ID
            final_report: AI Agent의 final_report 딕셔너리
            cached_report: 캐시된 리포트 정보

        Returns:
            Spring Boot 호환 형식의 딕셔너리
            {
                "report_id": "tcfd_report_20251216_163321",
                "meta": {"title": "TCFD 보고서"},
                "sections": [
                    {
                        "section_id": "governance",
                        "title": "1. Governance",
                        "blocks": [
                            {
                                "type": "text",
                                "subheading": "1.1 이사회의 감독",
                                "content": "..."
                            }
                        ]
                    }
                ]
            }
        """
        from datetime import datetime

        # report_id 생성 (timestamp 포함)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        formatted_report_id = f"tcfd_report_{timestamp}"

        # JSON 데이터에서 섹션 추출
        json_data = final_report.get('json', {})
        executive_summary = json_data.get('executive_summary', '')
        sections_dict = json_data.get('sections', {})

        # 섹션 ID 매핑 (AI Agent 키 → Spring Boot 키)
        section_mapping = {
            'executive_summary': {'section_id': 'ceosummry', 'title': 'Executive Summary', 'number': '0'},
            'governance': {'section_id': 'governance', 'title': 'Governance', 'number': '1'},
            'strategy': {'section_id': 'strategy', 'title': 'Strategy', 'number': '2'},
            'risk_management': {'section_id': 'risk_management', 'title': 'Risk Management', 'number': '3'},
            'metrics_and_targets': {'section_id': 'metrics_targets', 'title': 'Metrics & Targets', 'number': '4'},
            'metrics_targets': {'section_id': 'metrics_targets', 'title': 'Metrics & Targets', 'number': '4'},
        }

        # sections 배열 생성
        sections = []

        # Executive Summary 추가
        if executive_summary:
            blocks = self._parse_markdown_to_blocks(executive_summary)
            sections.append({
                "section_id": "ceosummry",
                "title": "Executive Summary",
                "blocks": blocks
            })

        # 나머지 섹션 추가 (순서 유지)
        section_order = ['governance', 'strategy', 'risk_management', 'metrics_and_targets', 'metrics_targets']
        for section_key in section_order:
            content = sections_dict.get(section_key)
            if content and section_key in section_mapping:
                section_info = section_mapping[section_key]
                # 중복 방지
                if not any(s['section_id'] == section_info['section_id'] for s in sections):
                    blocks = self._parse_markdown_to_blocks(content)
                    sections.append({
                        "section_id": section_info['section_id'],
                        "title": f"{section_info['number']}. {section_info['title']}",
                        "blocks": blocks
                    })

        # Spring Boot 호환 형식으로 반환
        return {
            "report_id": formatted_report_id,
            "meta": {
                "title": "TCFD 보고서"
            },
            "sections": sections
        }

    def _parse_markdown_to_blocks(self, markdown_text: str) -> list:
        """
        Markdown 텍스트를 blocks 배열로 파싱

        Args:
            markdown_text: Markdown 형식의 텍스트

        Returns:
            blocks 배열
            [
                {
                    "type": "text",
                    "subheading": "1.1 제목",
                    "content": "내용..."
                },
                {
                    "type": "table",
                    "title": "테이블 제목",
                    "headers": [...],
                    "items": [...]
                }
            ]
        """
        import re

        blocks = []
        lines = markdown_text.split('\n')
        current_block = None
        current_content = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # ### 소제목 감지 (###로 시작하는 heading)
            if line.startswith('###'):
                # 이전 블록 저장
                if current_block:
                    current_block['content'] = '\n'.join(current_content).strip()
                    if current_block['content']:
                        blocks.append(current_block)

                # 새 블록 시작
                subheading = line.replace('###', '').strip()
                current_block = {
                    "type": "text",
                    "subheading": subheading,
                    "content": ""
                }
                current_content = []

            # 테이블 감지 (|로 시작)
            elif line.startswith('|') and '|' in line:
                # 이전 블록 저장
                if current_block:
                    current_block['content'] = '\n'.join(current_content).strip()
                    if current_block['content']:
                        blocks.append(current_block)
                    current_block = None
                    current_content = []

                # 테이블 파싱
                table_block = self._parse_table(lines, i)
                if table_block:
                    blocks.append(table_block)
                    # 테이블 라인 건너뛰기
                    while i < len(lines) and lines[i].strip().startswith('|'):
                        i += 1
                    continue

            # 일반 텍스트
            elif line and not line.startswith('#'):
                if current_block is None:
                    # 소제목 없는 블록
                    current_block = {
                        "type": "text",
                        "subheading": None,
                        "content": ""
                    }
                current_content.append(line)

            i += 1

        # 마지막 블록 저장
        if current_block and current_content:
            current_block['content'] = '\n'.join(current_content).strip()
            if current_block['content']:
                blocks.append(current_block)

        return blocks

    def _parse_table(self, lines: list, start_idx: int) -> dict:
        """
        Markdown 테이블을 table block으로 파싱

        Args:
            lines: 전체 라인 배열
            start_idx: 테이블 시작 인덱스

        Returns:
            table block 딕셔너리
            {
                "type": "table",
                "title": "테이블 제목",
                "subheading": "설명",
                "headers": [
                    {"text": "컬럼1", "value": "col1"},
                    {"text": "컬럼2", "value": "col2"}
                ],
                "items": [
                    {
                        "col1": {"value": "데이터1", "bg_color": "none"},
                        "col2": {"value": "데이터2", "bg_color": "green"}
                    }
                ],
                "legend": [...]
            }
        """
        table_lines = []
        i = start_idx

        # 테이블 이전에 제목이 있는지 확인 (### 또는 ** 굵은 글씨)
        title = None
        subheading = None
        if start_idx > 0:
            prev_line = lines[start_idx - 1].strip()
            if prev_line.startswith('**') and prev_line.endswith('**'):
                title = prev_line.strip('*').strip()
            elif prev_line.startswith('###'):
                title = prev_line.replace('###', '').strip()

        # 테이블 라인 수집
        while i < len(lines) and lines[i].strip().startswith('|'):
            table_lines.append(lines[i].strip())
            i += 1

        if len(table_lines) < 2:
            # 테이블이 아님 (헤더 + 구분선이 최소)
            return None

        # 헤더 파싱
        header_line = table_lines[0]
        header_cells = [cell.strip() for cell in header_line.split('|')[1:-1]]  # 첫/마지막 빈 셀 제거

        headers = []
        for cell in header_cells:
            value = cell.lower().replace(' ', '_').replace('(', '').replace(')', '')
            headers.append({
                "text": cell,
                "value": value
            })

        # 데이터 행 파싱 (구분선 제외)
        items = []
        for row_line in table_lines[2:]:  # 0: header, 1: separator, 2+: data
            if not row_line or row_line.startswith('|---'):
                continue

            cells = [cell.strip() for cell in row_line.split('|')[1:-1]]
            if len(cells) != len(headers):
                continue

            item = {}
            for idx, cell in enumerate(cells):
                header_value = headers[idx]['value']
                # 셀 값과 배경색 파싱
                bg_color = self._detect_color_from_text(cell)
                item[header_value] = {
                    "value": cell,
                    "bg_color": bg_color
                }
            items.append(item)

        return {
            "type": "table",
            "title": title or "표",
            "subheading": subheading,
            "headers": headers,
            "items": items,
            "legend": self._generate_legend()
        }

    def _detect_color_from_text(self, text: str) -> str:
        """
        텍스트에서 색상 힌트를 감지

        Args:
            text: 셀 텍스트

        Returns:
            색상 문자열 (green, yellow, orange, red, none)
        """
        # 숫자에서 %를 파싱하여 임계값 기반으로 색상 결정
        import re

        # 퍼센트 숫자 추출
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
        if match:
            value = float(match.group(1))
            if value >= 30:
                return "red"
            elif value >= 10:
                return "orange"
            elif value >= 5:
                return "yellow"
            elif value >= 0:
                return "green"

        # 숫자만 있는 경우 (점수)
        match = re.search(r'^\s*(\d+(?:\.\d+)?)\s*$', text)
        if match:
            value = float(match.group(1))
            if value >= 70:
                return "red"
            elif value >= 50:
                return "orange"
            elif value >= 30:
                return "yellow"
            else:
                return "green"

        return "none"

    def _generate_legend(self) -> list:
        """
        기본 범례 생성

        Returns:
            범례 배열
        """
        return [
            {"color": "green", "label": "낮음"},
            {"color": "yellow", "label": "보통"},
            {"color": "orange", "label": "높음"},
            {"color": "red", "label": "매우 높음"}
        ]

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
