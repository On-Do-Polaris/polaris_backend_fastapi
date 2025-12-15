"""
Node 0: Data Preprocessing
사업장 데이터 로딩 + Excel 데이터 처리 (Optional)

작성일: 2025-12-15
버전: v05 (target_years 필터링 추가)

설계 이유:
- State 기반: TCFDReportState TypedDict 사용
- 5개 결과 테이블 분리: 노드별 필요한 데이터만 접근
- BC/AD 결과 별도 필드: building_data, additional_data로 분리
- 배치 처리: 여러 사업장 동시 로딩
- target_years: 특정 년도만 필터링 (2025~2030, 2020s~2050s)

DB 접근:
- Application DB (SpringBoot): sites 테이블 (사업장 정보)
- Datawarehouse DB (ModelOps): H, E, V, P, AAL 결과 테이블들
"""

import asyncio
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .state import TCFDReportState
from ...utils.database import DatabaseManager
from ..primary_data.additional_data_agent import AdditionalDataAgent
from ..primary_data.building_characteristics_agent import BuildingCharacteristicsAgent


# 유효한 target_year 값들 (보고서에서 사용하는 년도)
VALID_TARGET_YEARS: List[str] = [
    "2025", "2026", "2027", "2028", "2029", "2030",
    "2020s", "2030s", "2040s", "2050s"
]


class DataPreprocessingNode:
    """
    Node 0: 데이터 전처리 노드 (TCFD Report v2.1)

    입력:
        - site_ids: List[int] (사업장 ID 리스트)
        - excel_file: Optional[str] (Excel 파일 경로)
        - target_year: Optional[str] (분석 목표 연도, None이면 전체)

    출력:
        - TCFDReportState
    """

    def __init__(
        self,
        app_db_url: Optional[str] = None,
        dw_db_url: Optional[str] = None,
        llm_client=None,
        max_concurrent_sites: int = 10,
        bc_chunk_size: int = 5
    ):
        """
        두 개의 DB 연결 + LLM 클라이언트 초기화

        Args:
            app_db_url: Application DB URL (SpringBoot DB)
            dw_db_url: Datawarehouse DB URL (FastAPI + ModelOps DB)
            llm_client: LLM 클라이언트 (BC, AD에 전달)
            max_concurrent_sites: DB 조회 시 동시 처리 최대 사업장 수 (기본 10)
            bc_chunk_size: BC 분석 시 청크 크기 (기본 5, API Rate Limit 고려)
        """
        self.app_db_url = app_db_url or os.getenv('APPLICATION_DATABASE_URL')
        self.dw_db_url = dw_db_url or os.getenv('DATABASE_URL')

        if not self.app_db_url:
            raise ValueError("APPLICATION_DATABASE_URL is not set")
        if not self.dw_db_url:
            raise ValueError("DATABASE_URL is not set")

        # DB 매니저 초기화
        self.app_db = DatabaseManager(self.app_db_url)
        self.dw_db = DatabaseManager(self.dw_db_url)

        # LLM 클라이언트 저장
        self.llm_client = llm_client

        # 병렬 처리 설정
        self.max_concurrent_sites = max_concurrent_sites
        self.bc_chunk_size = bc_chunk_size

        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"Node 0: Data Preprocessing initialized "
            f"(max_concurrent={max_concurrent_sites}, bc_chunk={bc_chunk_size})"
        )

    async def execute(
        self,
        site_ids: List[int],
        excel_file: Optional[str] = None,
        target_years: Optional[List[str]] = None
    ) -> TCFDReportState:
        """
        메인 실행 함수

        Args:
            site_ids: 사업장 ID 리스트
            excel_file: Excel 파일 경로 (Optional)
            target_years: 분석 목표 연도 리스트 (Optional).
                         None이면 VALID_TARGET_YEARS 사용.

        Returns:
            TCFDReportState
        """
        # target_years가 None이면 기본값 사용
        if target_years is None:
            target_years = VALID_TARGET_YEARS

        self.logger.info(
            f"Node 0 실행 시작: {len(site_ids)}개 사업장, "
            f"target_years={target_years}"
        )

        # 1. Application DB에서 사이트 기본 정보 조회
        site_data = await self._load_site_info_parallel(site_ids)

        # 2. Datawarehouse DB에서 5개 결과 테이블 분리 조회
        (
            aal_scaled_results,
            hazard_results,
            exposure_results,
            vulnerability_results,
            probability_results
        ) = await self._load_modelops_results_parallel(site_data, target_years)

        # 3. BuildingCharacteristicsAgent 실행 (배치 처리) → 별도 필드로 반환
        self.logger.info("BuildingCharacteristicsAgent 실행 시작")
        building_data = await self._analyze_building_characteristics(
            site_data, aal_scaled_results, hazard_results
        )

        # 4. Excel 데이터 처리 (Optional) → 별도 필드로 반환
        additional_data: Dict[str, Any] = {}
        use_additional_data = False

        if excel_file and os.path.exists(excel_file):
            self.logger.info(f"Excel 파일 처리 시작: {excel_file}")
            additional_data, use_additional_data = await self._process_excel(
                excel_file, site_ids
            )
        else:
            self.logger.info("Excel 파일 없음 - AdditionalDataAgent 건너뜀")

        self.logger.info(f"Node 0 실행 완료: {len(site_data)}개 사업장 로딩")

        # 5. State 반환
        return TCFDReportState(
            site_data=site_data,
            aal_scaled_results=aal_scaled_results,
            hazard_results=hazard_results,
            exposure_results=exposure_results,
            vulnerability_results=vulnerability_results,
            probability_results=probability_results,
            building_data=building_data,
            additional_data=additional_data,
            use_additional_data=use_additional_data
        )

    # ==================== Site Info 조회 (Application DB) ====================

    async def _load_site_info_parallel(
        self,
        site_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Application DB에서 사이트 기본 정보 병렬 조회

        Args:
            site_ids: 사업장 ID 리스트

        Returns:
            site_data 리스트 (기본 정보만)
        """
        all_site_data = []

        for i in range(0, len(site_ids), self.max_concurrent_sites):
            chunk = site_ids[i:i + self.max_concurrent_sites]
            self.logger.info(
                f"Site Info 조회 청크 {i//self.max_concurrent_sites + 1}: "
                f"{len(chunk)}개 사업장"
            )

            tasks = [self._load_single_site_info(site_id) for site_id in chunk]
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

            for site_id, result in zip(chunk, chunk_results):
                if isinstance(result, Exception):
                    self.logger.error(f"사업장 {site_id} 정보 조회 실패: {result}")
                elif result is not None:
                    all_site_data.append(result)

            if i + self.max_concurrent_sites < len(site_ids):
                await asyncio.sleep(0.3)

        self.logger.info(f"Site Info 조회 완료: {len(all_site_data)}/{len(site_ids)}개")
        return all_site_data

    async def _load_single_site_info(self, site_id: int) -> Optional[Dict[str, Any]]:
        """
        단일 사업장 기본 정보 조회 (Application DB)

        Args:
            site_id: 사업장 ID

        Returns:
            site_data Dict (기본 정보만, BC/AD 결과 없음)
        """
        try:
            site_query = """
                SELECT
                    id, user_id, name,
                    road_address, jibun_address,
                    latitude, longitude, type
                FROM sites
                WHERE id = %s
            """
            site_results = self.app_db.execute_query(site_query, (str(site_id),))

            if not site_results:
                self.logger.warning(f"사업장 {site_id} 정보를 찾을 수 없습니다")
                return None

            site_info = site_results[0]

            return {
                "site_id": site_id,
                "site_info": {
                    "name": site_info['name'],
                    "latitude": float(site_info['latitude']),
                    "longitude": float(site_info['longitude']),
                    "address": site_info['road_address'] or site_info['jibun_address'],
                    "type": site_info.get('type')
                }
            }

        except Exception as e:
            self.logger.error(f"사업장 {site_id} 정보 조회 실패: {e}", exc_info=True)
            return None

    # ==================== ModelOps 결과 조회 (Datawarehouse DB) ====================

    async def _load_modelops_results_parallel(
        self,
        site_data: List[Dict[str, Any]],
        target_years: Optional[List[str]] = None
    ) -> tuple:
        """
        Datawarehouse DB에서 5개 결과 테이블 분리 조회 (병렬)

        Args:
            site_data: 사이트 기본 정보 리스트
            target_years: 분석 목표 연도 리스트 (None이면 전체)

        Returns:
            (aal_scaled_results, hazard_results, exposure_results,
             vulnerability_results, probability_results)
        """
        all_aal = []
        all_hazard = []
        all_exposure = []
        all_vulnerability = []
        all_probability = []

        for i in range(0, len(site_data), self.max_concurrent_sites):
            chunk = site_data[i:i + self.max_concurrent_sites]
            self.logger.info(
                f"ModelOps 결과 조회 청크 {i//self.max_concurrent_sites + 1}: "
                f"{len(chunk)}개 사업장"
            )

            tasks = [
                self._load_single_site_modelops(site, target_years)
                for site in chunk
            ]
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

            for site, result in zip(chunk, chunk_results):
                if isinstance(result, Exception):
                    self.logger.error(
                        f"사업장 {site['site_id']} ModelOps 결과 조회 실패: {result}"
                    )
                elif result is not None:
                    all_aal.extend(result['aal_scaled_results'])
                    all_hazard.extend(result['hazard_results'])
                    all_exposure.extend(result['exposure_results'])
                    all_vulnerability.extend(result['vulnerability_results'])
                    all_probability.extend(result['probability_results'])

            if i + self.max_concurrent_sites < len(site_data):
                await asyncio.sleep(0.3)

        self.logger.info(
            f"ModelOps 결과 조회 완료: "
            f"AAL={len(all_aal)}, H={len(all_hazard)}, E={len(all_exposure)}, "
            f"V={len(all_vulnerability)}, P={len(all_probability)}"
        )

        return (
            all_aal,
            all_hazard,
            all_exposure,
            all_vulnerability,
            all_probability
        )

    async def _load_single_site_modelops(
        self,
        site: Dict[str, Any],
        target_years: Optional[List[str]] = None
    ) -> Optional[Dict[str, List[Dict]]]:
        """
        단일 사업장 ModelOps 결과 조회 (5개 테이블)

        Args:
            site: 사이트 정보 Dict
            target_years: 분석 목표 연도 리스트 (None이면 전체)

        Returns:
            {
                'aal_scaled_results': [...],
                'hazard_results': [...],
                'exposure_results': [...],
                'vulnerability_results': [...],
                'probability_results': [...]
            }
        """
        try:
            site_id = str(site['site_id'])
            latitude = site['site_info']['latitude']
            longitude = site['site_info']['longitude']

            # DatabaseManager의 fetch_all_modelops_results 사용
            results = self.dw_db.fetch_all_modelops_results(
                site_id=site_id,
                latitude=latitude,
                longitude=longitude,
                target_years=target_years,
                risk_type=None  # 모든 리스크 타입 조회
            )

            return results

        except Exception as e:
            self.logger.error(
                f"사업장 {site['site_id']} ModelOps 결과 조회 실패: {e}",
                exc_info=True
            )
            return None

    # ==================== BC Agent 실행 ====================

    async def _analyze_building_characteristics(
        self,
        site_data: List[Dict[str, Any]],
        aal_scaled_results: List[Dict[str, Any]],
        hazard_results: List[Dict[str, Any]]
    ) -> Dict[int, Dict[str, Any]]:
        """
        BuildingCharacteristicsAgent를 사용하여 건물 특성 분석 (청크 단위 배치 처리)

        Args:
            site_data: 사이트 기본 정보 리스트
            aal_scaled_results: AAL 결과 (risk_scores 생성용)
            hazard_results: Hazard 결과 (risk_scores 생성용)

        Returns:
            building_data: Dict[site_id, BC 분석 결과]
        """
        building_data: Dict[int, Dict[str, Any]] = {}

        try:
            bc_agent = BuildingCharacteristicsAgent(llm_client=self.llm_client)

            for i in range(0, len(site_data), self.bc_chunk_size):
                chunk = site_data[i:i + self.bc_chunk_size]
                self.logger.info(
                    f"BC 분석 청크 {i//self.bc_chunk_size + 1}: "
                    f"{len(chunk)}개 사업장"
                )

                # BC가 기대하는 형식으로 변환
                bc_input = []
                for site in chunk:
                    # 해당 사이트의 risk_results 추출
                    site_risk_results = self._extract_risk_results_for_site(
                        site['site_id'],
                        aal_scaled_results,
                        hazard_results
                    )

                    bc_input.append({
                        "site_id": site["site_id"],
                        "site_info": site["site_info"],
                        "risk_results": site_risk_results
                    })

                try:
                    bc_results = await bc_agent.analyze_batch(bc_input)

                    # 결과를 building_data에 저장
                    for site_id, result in bc_results.items():
                        building_data[site_id] = result

                except Exception as chunk_error:
                    self.logger.error(f"BC 청크 분석 실패: {chunk_error}", exc_info=True)
                    # 실패한 사이트는 빈 딕셔너리로 저장
                    for site in chunk:
                        building_data[site["site_id"]] = {}

                if i + self.bc_chunk_size < len(site_data):
                    await asyncio.sleep(1.0)

            return building_data

        except Exception as e:
            self.logger.error(f"BuildingCharacteristicsAgent 실행 실패: {e}", exc_info=True)
            # 전체 실패 시 모든 사이트에 빈 딕셔너리
            for site in site_data:
                building_data[site["site_id"]] = {}
            return building_data

    def _extract_risk_results_for_site(
        self,
        site_id: int,
        aal_scaled_results: List[Dict[str, Any]],
        hazard_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        특정 사이트의 risk_results 추출 (BC Agent용)

        Args:
            site_id: 사이트 ID
            aal_scaled_results: 전체 AAL 결과
            hazard_results: 전체 Hazard 결과

        Returns:
            해당 사이트의 risk_results 리스트
        """
        site_id_str = str(site_id)
        risk_map = {}

        # AAL 데이터 매핑 (SSP245 기준)
        for aal in aal_scaled_results:
            if str(aal.get('site_id')) == site_id_str:
                risk_type = aal.get('risk_type')
                if risk_type:
                    risk_map[risk_type] = {
                        "risk_type": risk_type,
                        "final_aal": aal.get('ssp245_final_aal', 0.0),
                        "physical_risk_score": 0.0
                    }

        # Hazard Score 매핑
        for hazard in hazard_results:
            # hazard_results는 lat/lon 기반이므로 site_id가 없음
            # 여기서는 risk_type만 매칭
            risk_type = hazard.get('risk_type')
            if risk_type and risk_type in risk_map:
                risk_map[risk_type]["physical_risk_score"] = hazard.get('ssp245_score_100', 0.0)

        return list(risk_map.values())

    # ==================== AD Agent 실행 ====================

    async def _process_excel(
        self,
        excel_file: str,
        site_ids: List[int]
    ) -> tuple:
        """
        Excel 파일 처리 (AdditionalDataAgent 호출)

        Args:
            excel_file: Excel 파일 경로
            site_ids: 사업장 ID 리스트

        Returns:
            (additional_data: Dict, use_additional_data: bool)
        """
        try:
            agent = AdditionalDataAgent(llm_client=self.llm_client)
            result = agent.analyze(excel_file, site_ids)

            if result.get("status") == "completed":
                self.logger.info(
                    f"AD 분석 완료: {len(result.get('site_specific_guidelines', {}))}개 사업장 가이드라인 생성"
                )
                return result, True  # additional_data, use_additional_data = True
            else:
                self.logger.warning(
                    f"Excel 분석 실패: {result.get('meta', {}).get('error', 'Unknown')}"
                )
                return {}, False

        except Exception as e:
            self.logger.error(f"Excel 파일 처리 실패: {e}", exc_info=True)
            return {}, False
