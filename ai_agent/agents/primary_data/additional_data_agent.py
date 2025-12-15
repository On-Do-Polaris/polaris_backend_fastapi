'''
파일명: additional_data_agent.py
작성일: 2025-12-15
버전: v02 (TCFD Report v2.1 - Multi-Site Support)
파일 개요: 추가 데이터 (Excel) 분석 에이전트 (보고서 생성용 가이드라인 제공)

역할:
    - 사용자가 업로드한 Excel 파일에서 사업장별 추가 정보 추출
    - 추출된 데이터를 분석하여 보고서 생성 에이전트를 위한 가이드라인 생성
    - ⚠️ 조건부 실행: Excel 파일이 제공된 경우에만 실행
    - 다중 사업장 배치 처리 지원 (site_ids를 List[int]로 받음)

변경 이력:
    - 2025-12-14: v01 - 초기 생성 (TCFD Report v2 Refactoring)
    - 2025-12-15: v02 - 다중 사업장 배치 처리 확인, TCFD Report v2.1 대응
'''

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import pandas as pd
import json

logger = logging.getLogger(__name__)


class AdditionalDataAgent:
    """
    추가 데이터 분석 에이전트 (Excel → LLM Guideline)

    입력:
        - excel_file: str (파일 경로)
        - site_ids: List[int] (분석 대상 사업장 ID 리스트)

    출력:
        - site_specific_guidelines: Dict[int, Dict] (사업장별 가이드라인)
        - summary: str (전체 요약)
    """

    def __init__(self, llm_client=None):
        """
        초기화
        :param llm_client: LLM 클라이언트 인스턴스 (텍스트 생성용)
        """
        self.logger = logger
        self.llm_client = llm_client
        self.logger.info("AdditionalDataAgent 초기화 완료")

    def analyze(self, excel_file: str, site_ids: List[int]) -> Dict[str, Any]:
        """
        Excel 파일 분석 및 가이드라인 생성

        :param excel_file: Excel 파일 경로
        :param site_ids: 분석 대상 사업장 ID 리스트
        :return: 분석 결과 (사업장별 가이드라인 + 전체 요약)
        """
        self.logger.info(f"추가 데이터 분석 시작: {excel_file}, {len(site_ids)}개 사업장")

        try:
            # 1. Excel 파일 읽기
            raw_data = self._read_excel(excel_file)

            # 2. 사업장 ID와 매칭하여 데이터 추출
            site_data = self._extract_site_data(raw_data, site_ids)

            # 3. 각 사업장별 가이드라인 생성 (LLM 활용)
            site_specific_guidelines = {}
            for site_id, data in site_data.items():
                guideline = self._generate_site_guideline(site_id, data)
                site_specific_guidelines[site_id] = guideline

            # 4. 전체 요약 (Optional)
            summary = self._generate_summary(site_specific_guidelines)

            result = {
                "meta": {
                    "analyzed_at": datetime.now().isoformat(),
                    "source_file": excel_file,
                    "site_count": len(site_specific_guidelines)
                },
                "site_specific_guidelines": site_specific_guidelines,
                "summary": summary,
                "status": "completed"
            }

            self.logger.info("추가 데이터 분석 완료")
            return result

        except Exception as e:
            self.logger.error(f"추가 데이터 분석 실패: {e}")
            return {
                "meta": {
                    "analyzed_at": datetime.now().isoformat(),
                    "source_file": excel_file,
                    "error": str(e)
                },
                "site_specific_guidelines": {},
                "summary": "",
                "status": "failed"
            }

    def _read_excel(self, file_path: str) -> pd.DataFrame:
        """
        Excel 파일 읽기

        ⚠️ 예상 Excel 구조:
        - Column 1: site_id (또는 site_name)
        - Column 2~N: 추가 정보 (자유 형식)

        실제 구조는 프로젝트 요구사항에 따라 조정 필요
        """
        try:
            # TODO: 실제 Excel 구조에 맞게 수정 필요
            df = pd.read_excel(file_path, sheet_name=0)  # 첫 번째 시트 읽기
            self.logger.info(f"Excel 파일 읽기 성공: {len(df)}행, {len(df.columns)}열")
            return df
        except Exception as e:
            self.logger.error(f"Excel 파일 읽기 실패: {e}")
            raise

    def _extract_site_data(self, df: pd.DataFrame, site_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        DataFrame에서 사업장 ID에 해당하는 데이터 추출

        ⚠️ site_id 컬럼명은 실제 Excel 구조에 따라 조정 필요
        """
        site_data = {}

        # TODO: 실제 Excel 구조에 맞게 컬럼명 수정 필요
        # 예: 'site_id', 'site_name', '사업장ID', '사업장명' 등

        # 임시 구현: site_id 컬럼이 있다고 가정
        if 'site_id' in df.columns:
            for site_id in site_ids:
                site_df = df[df['site_id'] == site_id]
                if not site_df.empty:
                    # DataFrame을 dict로 변환 (첫 번째 행만 사용)
                    site_data[site_id] = site_df.iloc[0].to_dict()
                else:
                    self.logger.warning(f"사업장 ID {site_id}에 대한 데이터 없음")
                    site_data[site_id] = {}
        else:
            # site_id 컬럼이 없는 경우 - site_name으로 매칭 시도 등
            self.logger.warning("Excel에 site_id 컬럼이 없습니다. 전체 데이터를 반환합니다.")
            # Fallback: 모든 데이터를 첫 번째 site_id에 할당
            if site_ids:
                site_data[site_ids[0]] = df.to_dict(orient='records')

        return site_data

    def _generate_site_guideline(self, site_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        사업장별 가이드라인 생성 (LLM 활용)
        """
        if not data:
            return {
                "site_id": site_id,
                "guideline": "추가 데이터 없음",
                "relevance": 0.0,
                "key_insights": []
            }

        # LLM 사용
        if self.llm_client:
            try:
                prompt = self._build_prompt(site_id, data)
                response = self.llm_client.invoke(prompt)

                # 간단한 파싱 (실제로는 더 정교한 파싱 필요)
                return {
                    "site_id": site_id,
                    "guideline": response,
                    "key_insights": self._extract_key_insights(response)
                }
            except Exception as e:
                self.logger.error(f"LLM 가이드라인 생성 실패 (사업장 {site_id}): {e}")
                return self._generate_fallback_guideline(site_id, data)

        return self._generate_fallback_guideline(site_id, data)

    def _extract_key_insights(self, guideline_text: str) -> List[str]:
        """
        가이드라인 텍스트에서 핵심 인사이트 추출

        ⚠️ 간단한 구현: 줄바꿈 기준으로 분리
        실제로는 더 정교한 파싱 필요 (정규표현식, LLM 재호출 등)
        """
        # 간단한 파싱: "- "로 시작하는 줄만 추출
        insights = []
        for line in guideline_text.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                insights.append(line[2:])  # "- " 제거

        return insights[:5]  # 최대 5개만 반환

    def _generate_fallback_guideline(self, site_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 실패 시 기본 가이드라인 생성"""
        guideline = f"## 사업장 {site_id} 추가 정보\n\n"

        if data:
            for key, value in data.items():
                if value and str(value).strip():
                    guideline += f"- {key}: {value}\n"
        else:
            guideline += "- 추가 데이터 없음\n"

        return {
            "site_id": site_id,
            "guideline": guideline,
            "key_insights": []
        }

    def _build_prompt(self, site_id: int, data: Dict[str, Any]) -> str:
        """
        LLM 프롬프트 구성 (추가 데이터 → 가이드라인 변환)
        """
        # 데이터를 JSON 형식으로 정리
        data_json = json.dumps(data, indent=2, ensure_ascii=False)

        prompt = f"""당신은 TCFD 보고서 생성 전문가이며, **사용자가 제공한 추가 데이터를 분석하여 보고서 생성 에이전트를 위한 가이드라인**을 작성하는 역할을 맡고 있습니다.

제공된 데이터는 **사업장 {site_id}에 대한 추가 정보**이며, 이 정보를 바탕으로 보고서 작성 시 활용할 핵심 인사이트를 정리해주세요.

⚠️ **중요**: 이 가이드라인은 추후 Node 2-A (Scenario Analysis), Node 2-B (Impact Analysis), Node 2-C (Mitigation Strategies) 에이전트가 참고합니다.

---
## 사업장 {site_id} 추가 데이터

{data_json}

---
## 가이드라인 작성 지침

위의 추가 데이터를 분석하여 다음 목차에 따라 **보고서 생성 에이전트를 위한 가이드라인**을 작성하세요.

**[가이드라인 목차]**
1. **데이터 요약** (3-5문장)
   - 제공된 추가 데이터의 핵심 내용을 간결하게 요약
   - 어떤 유형의 정보인지 명시 (예: 시설물 세부 정보, 운영 현황, 재무 데이터 등)

2. **보고서 활용 방안**
   - Node 2-A (Scenario Analysis): 이 데이터가 시나리오 분석에 어떻게 활용될 수 있는지
   - Node 2-B (Impact Analysis): 영향 분석 시 강조해야 할 포인트
   - Node 2-C (Mitigation Strategies): 대응 전략 수립 시 참고할 정보

3. **주의사항**
   - 이 데이터를 과도하게 일반화하거나 왜곡하지 않도록 주의
   - 특정 사업장에만 해당하는 정보임을 명시

**톤앤매너**: 간결하고 실용적인 어조로, 보고서 생성 에이전트가 바로 활용할 수 있도록 구체적으로 작성하세요.
**주의**: 최종 보고서 내용을 직접 작성하지 마세요. 가이드라인과 핵심 포인트만 제공하세요.
"""
        return prompt

    def _generate_summary(self, site_specific_guidelines: Dict[int, Dict[str, Any]]) -> str:
        """
        전체 사업장 가이드라인 요약
        """
        if not site_specific_guidelines:
            return "추가 데이터 없음"

        summary = f"## 추가 데이터 전체 요약\n\n"
        summary += f"총 {len(site_specific_guidelines)}개 사업장에 대한 추가 데이터가 제공되었습니다.\n\n"

        # 사업장별 핵심 인사이트 수 집계
        total_insights = sum(len(g.get('key_insights', [])) for g in site_specific_guidelines.values())
        summary += f"총 {total_insights}개의 핵심 인사이트가 추출되었습니다.\n"

        return summary
