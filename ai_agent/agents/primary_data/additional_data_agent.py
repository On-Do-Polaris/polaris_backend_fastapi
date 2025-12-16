'''
파일명: additional_data_agent.py
작성일: 2025-12-16
버전: v07 (2섹션 JSON 출력 간소화, BC Agent와 구조 통일)
파일 개요: 추가 데이터 분석 에이전트 (보고서 생성용 가이드라인 제공)

역할:
    - AdditionalDataLoader를 통해 DB에서만 추가 데이터 조회 (Excel 직접 접근 X)
    - 추출된 데이터를 분석하여 보고서 생성 에이전트를 위한 가이드라인 생성
    - ⚠️ 조건부 실행: 추가 데이터가 DB에 적재된 경우에만 실행
    - 다중 사업장 병렬 처리 지원 (asyncio.gather)

아키텍처:
    - additional_data_loader.py: ETL (Excel → DB 적재) ← 별도 트리거로 실행
    - additional_data_agent.py: 분석 (DB 조회만 → LLM → 가이드라인) ← Node 0에서 호출

변경 이력:
    - 2025-12-14: v01 - 초기 생성 (TCFD Report v2 Refactoring)
    - 2025-12-15: v02 - 다중 사업장 배치 처리 확인, TCFD Report v2.1 대응
    - 2025-12-15: v03 - 병렬 처리 완료 (asyncio.gather, 전체 async 전환)
    - 2025-12-16: v04 - ETL 분리 (AdditionalDataLoader 사용)
    - 2025-12-16: v05 - DB 조회만 하도록 수정 (Excel 직접 접근 X)
    - 2025-12-16: v06 - 영어 프롬프트 + 한글 출력 (토큰 효율화)
    - 2025-12-16: v07 - 2섹션 JSON 출력 (data_summary + report_guidelines), BC Agent와 구조 통일
'''

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json
import asyncio

# AdditionalDataLoader 임포트 (ETL 담당)
try:
    from .additional_data_loader import AdditionalDataLoader
except ImportError:
    AdditionalDataLoader = None
    print("⚠️ AdditionalDataLoader를 임포트할 수 없습니다.")

logger = logging.getLogger(__name__)


class AdditionalDataAgent:
    """
    추가 데이터 분석 에이전트 (DB → LLM Guideline)
    → v05: DB 조회만 (Excel 직접 접근 X)

    입력:
        - site_ids: List[str] (분석 대상 사업장 UUID 리스트)

    출력:
        - site_specific_guidelines: Dict[str, Dict] (사업장별 가이드라인)
        - summary: str (전체 요약)

    아키텍처:
        - AdditionalDataLoader: ETL (Excel → DB) - 별도 트리거
        - AdditionalDataAgent: 분석 (DB 조회만 → LLM → 가이드라인) - Node 0 호출
    """

    def __init__(self, llm_client=None, db_url: Optional[str] = None):
        """
        초기화
        :param llm_client: LLM 클라이언트 인스턴스 (텍스트 생성용)
        :param db_url: Datawarehouse DB URL (site_additional_data 테이블 접근용)
        """
        self.logger = logger
        self.llm_client = llm_client

        # AdditionalDataLoader 초기화 (DB 조회용)
        if AdditionalDataLoader:
            try:
                self.data_loader = AdditionalDataLoader(db_url=db_url)
                self.logger.info("AdditionalDataLoader 초기화 성공")
            except Exception as e:
                self.logger.error(f"AdditionalDataLoader 초기화 실패: {e}")
                self.data_loader = None
        else:
            self.data_loader = None

        self.logger.info("AdditionalDataAgent 초기화 완료")

    async def analyze_from_db(self, site_ids: List[str]) -> Dict[str, Any]:
        """
        DB에서 추가 데이터 조회 및 가이드라인 생성 (병렬 처리)
        → Node 0에서 호출하는 주 메서드

        :param site_ids: 분석 대상 사업장 UUID 리스트
        :return: 분석 결과 (사업장별 가이드라인 + 전체 요약)
        """
        self.logger.info(f"추가 데이터 분석 시작 (DB 조회): {len(site_ids)}개 사업장")

        try:
            # 1. 각 사업장별로 DB에서 추가 데이터 조회
            site_data = {}
            for site_id in site_ids:
                if self.data_loader:
                    data = self.data_loader.fetch_all_for_site(site_id)
                    site_data[site_id] = data
                else:
                    self.logger.warning(f"DataLoader 없음, 사업장 {site_id} 빈 데이터")
                    site_data[site_id] = {}

            # 2. 각 사업장별 가이드라인 생성 (병렬 처리)
            tasks = [
                self._generate_site_guideline(site_id, data)
                for site_id, data in site_data.items()
            ]

            self.logger.info(f"🔄 {len(tasks)}개 사업장 병렬 처리 시작")
            guidelines_list = await asyncio.gather(*tasks)

            # 결과를 dict로 변환
            site_specific_guidelines = {
                site_id: guideline
                for site_id, guideline in zip(site_data.keys(), guidelines_list)
            }
            self.logger.info(f"✅ {len(site_specific_guidelines)}개 사업장 병렬 처리 완료")

            # 3. 전체 요약 (Optional)
            summary = await self._generate_summary(site_specific_guidelines)

            result = {
                "meta": {
                    "analyzed_at": datetime.now().isoformat(),
                    "source": "database",
                    "site_count": len(site_specific_guidelines)
                },
                "site_specific_guidelines": site_specific_guidelines,
                "summary": summary,
                "status": "completed"
            }

            self.logger.info("추가 데이터 분석 완료 (DB 조회)")
            return result

        except Exception as e:
            self.logger.error(f"추가 데이터 분석 실패: {e}")
            return {
                "meta": {
                    "analyzed_at": datetime.now().isoformat(),
                    "source": "database",
                    "error": str(e)
                },
                "site_specific_guidelines": {},
                "summary": "",
                "status": "failed"
            }

    async def analyze(self, excel_file: str = None, site_ids: List = None) -> Dict[str, Any]:
        """
        추가 데이터 분석 (하위 호환성 유지)

        ⚠️ DEPRECATED: 새로운 코드에서는 analyze_from_db() 사용을 권장합니다.

        :param excel_file: Excel 파일 경로 (미사용, 호환성 유지)
        :param site_ids: 분석 대상 사업장 ID 리스트 (str UUID 또는 int)
        :return: 분석 결과 (사업장별 가이드라인 + 전체 요약)
        """
        self.logger.warning("analyze()는 deprecated입니다. analyze_from_db()를 사용하세요.")

        # site_ids를 str로 변환
        if site_ids:
            site_ids_str = [str(sid) for sid in site_ids]
        else:
            site_ids_str = []

        # DB 조회 메서드로 위임
        return await self.analyze_from_db(site_ids_str)

    async def _generate_site_guideline(self, site_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        사업장별 가이드라인 생성 (LLM 활용 - 비동기)
        v07: JSON 출력 (data_summary + report_guidelines)
        """
        if not data:
            return {
                "site_id": site_id,
                "agent_guidelines": {
                    "data_summary": {
                        "one_liner": "추가 데이터 없음",
                        "key_data_points": [],
                        "data_availability": "Low"
                    },
                    "report_guidelines": {
                        "scenario_analysis_focus": "데이터 부족",
                        "impact_analysis_focus": "데이터 부족",
                        "mitigation_focus": "데이터 부족"
                    }
                }
            }

        # LLM 사용
        if self.llm_client:
            try:
                prompt = self._build_prompt(site_id, data)

                # 비동기 LLM 호출
                if hasattr(self.llm_client, 'ainvoke'):
                    response = await self.llm_client.ainvoke(prompt)
                else:
                    # Fallback to sync invoke
                    response = self.llm_client.invoke(prompt)

                # AIMessage에서 content 추출
                response_text = response.content if hasattr(response, 'content') else str(response)

                # JSON 파싱
                parsed_guidelines = self._parse_json_response(response_text)
                if parsed_guidelines:
                    return {
                        "site_id": site_id,
                        "agent_guidelines": parsed_guidelines
                    }

                # JSON 파싱 실패 시 fallback
                self.logger.warning(f"JSON 파싱 실패 (사업장 {site_id})")
                return self._generate_fallback_guideline(site_id, data)

            except Exception as e:
                self.logger.error(f"LLM 가이드라인 생성 실패 (사업장 {site_id}): {e}")
                return self._generate_fallback_guideline(site_id, data)

        return self._generate_fallback_guideline(site_id, data)

    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        LLM 응답에서 JSON 추출 및 파싱 (BC Agent와 동일한 로직)
        """
        import re
        import json

        # 1. 순수 JSON인 경우
        try:
            clean_text = response_text.strip()
            if clean_text.startswith('{'):
                return json.loads(clean_text)
        except json.JSONDecodeError:
            pass

        # 2. 마크다운 코드블록 내 JSON 추출
        try:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass

        # 3. 중괄호 기반 추출 시도
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx + 1]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        return None

    def _generate_fallback_guideline(self, site_id: int, data: Any) -> Dict[str, Any]:
        """LLM 실패 시 기본 JSON 가이드라인 생성 (v07: 2섹션 구조)"""
        key_data_points = []
        one_liner = "추가 데이터 없음"
        availability = "Low"

        if data:
            # data가 dict인 경우 (카테고리별 데이터)
            if isinstance(data, dict):
                categories = list(data.keys())
                total_files = sum(len(v) if isinstance(v, list) else 1 for v in data.values())

                if categories:
                    one_liner = f"{len(categories)}개 카테고리의 추가 데이터 ({total_files}개 파일)"
                    key_data_points = [f"{cat}: {len(data[cat])}개 파일" if isinstance(data[cat], list) else f"{cat}: 1개" for cat in categories[:3]]
                    availability = "High" if total_files > 5 else "Medium"

            # data가 list인 경우 (시계열 데이터)
            elif isinstance(data, list):
                if len(data) > 0:
                    first_row = data[0]
                    columns = list(first_row.keys()) if isinstance(first_row, dict) else []
                    one_liner = f"시계열 데이터 {len(data)}개 레코드"
                    key_data_points = [f"{col} 데이터 포함" for col in columns[:3]]
                    availability = "High" if len(data) > 10 else "Medium"

        return {
            "site_id": site_id,
            "agent_guidelines": {
                "data_summary": {
                    "one_liner": one_liner,
                    "key_data_points": key_data_points,
                    "data_availability": availability
                },
                "report_guidelines": {
                    "scenario_analysis_focus": "제공된 추가 데이터를 바탕으로 시나리오 분석에 반영",
                    "impact_analysis_focus": "추가 데이터의 정량적 정보를 영향 분석에 활용",
                    "mitigation_focus": "데이터 기반 대응 전략 수립"
                }
            }
        }

    def _build_prompt(self, site_id: int, data: Dict[str, Any]) -> str:
        """
        LLM 프롬프트 구성 (추가 데이터 → 가이드라인 변환)
        v07 업데이트: 2섹션 간소화 (data_summary + report_guidelines)
        """
        # datetime 직렬화 핸들러
        def json_serializer(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        # 데이터 요약 (토큰 제한 때문에 전체 데이터 대신 요약만)
        summarized_data = self._summarize_data_for_prompt(data)
        data_json = json.dumps(summarized_data, indent=2, ensure_ascii=False, default=json_serializer)

        prompt = f"""<ROLE>
You are a TCFD report expert. Analyze additional site data and generate **concise guidelines** for TCFD report agents.
</ROLE>

<ADDITIONAL_DATA>
Site ID: {site_id}

{data_json}
</ADDITIONAL_DATA>

<OUTPUT_FORMAT>
Generate JSON with 2 sections:

{{
  "data_summary": {{
    "one_liner": "1-sentence data summary",
    "key_data_points": ["Data point 1", "Data point 2", "Data point 3"],
    "data_availability": "High/Medium/Low"
  }},

  "report_guidelines": {{
    "scenario_analysis_focus": "Key points for scenario analysis",
    "impact_analysis_focus": "Key points for impact analysis",
    "mitigation_focus": "Key points for adaptation strategies"
  }}
}}

**OUTPUT LANGUAGE: All text MUST be in KOREAN.** Only JSON keys in English.

Output pure JSON only. No markdown.
</OUTPUT_FORMAT>
"""
        return prompt

    def _summarize_data_for_prompt(self, data: Dict[str, Any], max_rows_per_sheet: int = 20) -> Dict[str, Any]:
        """
        LLM 토큰 제한을 위해 데이터 요약 (전체 덤프 대신 샘플만)

        Args:
            data: 카테고리별 데이터 (fetch_all_for_site 결과)
            max_rows_per_sheet: 시트당 최대 행 수

        Returns:
            요약된 데이터 (메타 정보 + 샘플 행)
        """
        summarized = {}

        for category, items in data.items():
            summarized[category] = []

            for item in items:
                file_info = {
                    "file_name": item.get("file_name", "unknown"),
                    "category": category,
                    "uploaded_at": str(item.get("uploaded_at", "")),
                }

                # structured_data에서 샘플만 추출
                structured = item.get("structured_data", {})
                if isinstance(structured, dict):
                    sheets_summary = []
                    for sheet in structured.get("sheets", []):
                        sheet_name = sheet.get("name", "Sheet")
                        row_count = sheet.get("row_count", 0)
                        content = sheet.get("content", "")

                        # 처음 N행만 추출
                        lines = content.split("\n")[:max_rows_per_sheet]
                        sample_content = "\n".join(lines)

                        sheets_summary.append({
                            "sheet_name": sheet_name,
                            "total_rows": row_count,
                            "sample_rows": len(lines),
                            "sample_content": sample_content
                        })

                    file_info["sheets"] = sheets_summary
                else:
                    file_info["data_preview"] = str(structured)[:2000]

                summarized[category].append(file_info)

        return summarized

    async def _generate_summary(self, site_specific_guidelines: Dict[int, Dict[str, Any]]) -> str:
        """
        전체 사업장 가이드라인 요약 (비동기)
        """
        if not site_specific_guidelines:
            return "추가 데이터 없음"

        summary = f"## 추가 데이터 전체 요약\n\n"
        summary += f"총 {len(site_specific_guidelines)}개 사업장에 대한 추가 데이터가 제공되었습니다.\n\n"

        # 사업장별 핵심 인사이트 수 집계
        total_insights = sum(len(g.get('key_insights', [])) for g in site_specific_guidelines.values())
        summary += f"총 {total_insights}개의 핵심 인사이트가 추출되었습니다.\n"

        return summary
