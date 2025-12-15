"""
Node 0: Data Preprocessing
사업장 데이터 로딩 + Excel 데이터 처리 (Optional)

작성일: 2025-12-15
버전: v02 (TCFD Report v2.1 - DB Direct Queries)

설계 이유:
- Excel Optional 처리: 모든 사용자가 추가 데이터를 제공하지 않으므로 분기 처리 필수
- 병렬 로딩: 8개 사업장 데이터 동시 로딩으로 10초 내 완료
- DB 직접 조회: psycopg2로 application + datawarehouse 양쪽 DB 접근
- AdditionalDataAgent 조건부 실행: Excel 파일이 있을 때만 실행

DB 접근:
- application DB (SpringBoot): sites 테이블 (사업장 정보)
- datawarehouse DB (ModelOps): H, E, V, AAL 결과 테이블들
"""

import asyncio
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...utils.database import DatabaseManager
from ..primary_data.additional_data_agent import AdditionalDataAgent
from ..primary_data.building_characteristics_agent import BuildingCharacteristicsAgent


class DataPreprocessingNode:
    """
    Node 0: 데이터 전처리 노드 (TCFD Report v2.1)

    입력:
        - site_ids: List[int] (최대 8개 사업장)
        - excel_file: Optional[str] (Excel 파일 경로)
        - user_id: int (Optional)

    출력:
        - sites_data: List[Dict] - 사업장별 분석 데이터
            [{
                "site_id": int,
                "site_info": {"latitude": float, "longitude": float, "address": str, "name": str},
                "risk_results": [...],  # H, E, V, AAL 결과
                "building_characteristics": {...}  # BuildingCharacteristicsAgent 결과 (Node 0에서 채움)
            }]
        - additional_data_guidelines: Optional[Dict] - Excel 가이드라인 (조건부)
    """

    def __init__(
        self,
        app_db_url: Optional[str] = None,
        dw_db_url: Optional[str] = None,
        llm_client=None,
        max_concurrent_sites: int = 10,  # 동시 처리 최대 사업장 수
        bc_chunk_size: int = 5  # BC 청크 크기
    ):
        """
        두 개의 DB 연결 + LLM 클라이언트 초기화

        Args:
            app_db_url: application DB URL (SpringBoot DB)
            dw_db_url: datawarehouse DB URL (FastAPI + ModelOps DB)
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
        user_id: Optional[int] = None,
        target_year: str = "2050"
    ) -> Dict[str, Any]:
        """
        메인 실행 함수

        Args:
            site_ids: 사업장 ID 리스트 (최대 8개)
            excel_file: Excel 파일 경로 (Optional)
            user_id: 사용자 ID (Optional)
            target_year: 분석 목표 연도 (기본값: 2050)

        Returns:
            Dict with sites_data, additional_data_guidelines
        """
        self.logger.info(f"Node 0 실행 시작: {len(site_ids)}개 사업장, target_year={target_year}")

        # 1. 사업장 데이터 병렬 로딩 (application + datawarehouse DB)
        sites_data = await self._load_sites_data_parallel(site_ids, target_year)

        # 2. BuildingCharacteristicsAgent 실행 (배치 처리)
        self.logger.info("BuildingCharacteristicsAgent 실행 시작")
        sites_data = await self._analyze_building_characteristics(sites_data)

        # 3. Excel 데이터 처리 (Optional 분기)
        additional_data_guidelines = None

        if excel_file and os.path.exists(excel_file):
            self.logger.info(f"Excel 파일 처리 시작: {excel_file}")
            additional_data_guidelines = await self._process_excel(excel_file, site_ids)
        else:
            self.logger.info("Excel 파일 없음 - AdditionalDataAgent 건너뜀")

        self.logger.info(f"Node 0 실행 완료: {len(sites_data)}개 사업장 로딩")

        return {
            "sites_data": sites_data,
            "additional_data_guidelines": additional_data_guidelines,
            "loaded_at": datetime.now().isoformat(),
            "target_year": target_year
        }

    async def _load_sites_data_parallel(
        self,
        site_ids: List[int],
        target_year: str
    ) -> List[Dict]:
        """
        병렬로 사업장 데이터 로딩 (청크 단위 처리로 메모리 관리)

        Args:
            site_ids: 사업장 ID 리스트
            target_year: 분석 목표 연도

        Returns:
            List of site data dictionaries
        """
        all_sites_data = []
        
        # 청크 단위로 분할 처리 (max_concurrent_sites씩)
        for i in range(0, len(site_ids), self.max_concurrent_sites):
            chunk = site_ids[i:i + self.max_concurrent_sites]
            self.logger.info(
                f"DB 조회 청크 {i//self.max_concurrent_sites + 1}: "
                f"{len(chunk)}개 사업장 ({i+1}~{i+len(chunk)})"
            )
            
            tasks = [self._load_single_site(site_id, target_year) for site_id in chunk]
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 성공한 결과만 수집 (예외는 로깅)
            for site_id, result in zip(chunk, chunk_results):
                if isinstance(result, Exception):
                    self.logger.error(f"사업장 {site_id} 로딩 실패: {result}")
                elif result is not None:
                    all_sites_data.append(result)
            
            # API Rate Limit 방지를 위한 짧은 대기
            if i + self.max_concurrent_sites < len(site_ids):
                await asyncio.sleep(0.5)
        
        self.logger.info(f"총 {len(all_sites_data)}/{len(site_ids)}개 사업장 로딩 완료")
        return all_sites_data

    async def _load_single_site(
        self,
        site_id: int,
        target_year: str
    ) -> Optional[Dict]:
        """
        단일 사업장 데이터 로딩 (application + datawarehouse DB)

        Args:
            site_id: 사업장 ID (UUID in DB, but passed as int/str)
            target_year: 분석 목표 연도

        Returns:
            Dict with site_info, risk_results, building_characteristics
        """
        try:
            # 1. application DB에서 사업장 정보 조회
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
            latitude = float(site_info['latitude'])
            longitude = float(site_info['longitude'])

            # 2. datawarehouse DB에서 ModelOps 결과 조회
            modelops_results = self.dw_db.fetch_all_modelops_results(
                site_id=str(site_id),
                latitude=latitude,
                longitude=longitude,
                target_year=target_year,
                risk_type=None  # 모든 리스크 타입 조회
            )

            # 3. risk_results 포맷팅 (AAL + Physical Risk Score)
            risk_results = self._format_risk_results(
                modelops_results.get('aal_scaled_results', []),
                modelops_results.get('hazard_results', [])
            )

            # 4. building_characteristics는 나중에 BuildingCharacteristicsAgent에서 채울 예정
            # Node 0에서는 빈 딕셔너리로 placeholder 제공

            return {
                "site_id": site_id,
                "site_info": {
                    "name": site_info['name'],
                    "latitude": latitude,
                    "longitude": longitude,
                    "address": site_info['road_address'] or site_info['jibun_address'],
                    "type": site_info.get('type')
                },
                "risk_results": risk_results,
                "modelops_raw": modelops_results,  # 원본 데이터 보관 (디버깅용)
                "building_characteristics": None  # BC에서 채워질 예정
            }

        except Exception as e:
            self.logger.error(f"사업장 {site_id} 데이터 로딩 실패: {e}", exc_info=True)
            return None

    async def _analyze_building_characteristics(
        self,
        sites_data: List[Dict]
    ) -> List[Dict]:
        """
        BuildingCharacteristicsAgent를 사용하여 건물 특성 분석 (청크 단위 배치 처리)

        Args:
            sites_data: 사업장 데이터 리스트

        Returns:
            building_characteristics가 채워진 sites_data
        """
        try:
            bc_agent = BuildingCharacteristicsAgent(llm_client=self.llm_client)
            
            # 청크 단위로 분할 처리 (API Rate Limit 고려)
            for i in range(0, len(sites_data), self.bc_chunk_size):
                chunk = sites_data[i:i + self.bc_chunk_size]
                self.logger.info(
                    f"BC 분석 청크 {i//self.bc_chunk_size + 1}: "
                    f"{len(chunk)}개 사업장 ({i+1}~{i+len(chunk)})"
                )
                
                # BC가 기대하는 형식으로 변환
                bc_input = []
                for site in chunk:
                    bc_input.append({
                        "site_id": site["site_id"],
                        "site_info": site["site_info"],
                        "risk_results": site["risk_results"]
                    })
                
                # 배치 분석 실행 (chunk 단위)
                try:
                    bc_results = bc_agent.analyze_batch(bc_input)
                    
                    # 결과를 sites_data에 병합
                    for site in chunk:
                        site_id = site["site_id"]
                        if site_id in bc_results:
                            site["building_characteristics"] = bc_results[site_id]
                        else:
                            self.logger.warning(f"사업장 {site_id} BC 분석 결과 없음")
                            site["building_characteristics"] = {}
                
                except Exception as chunk_error:
                    self.logger.error(f"BC 청크 분석 실패: {chunk_error}", exc_info=True)
                    # 실패한 청크는 빈 딕셔너리로 채움
                    for site in chunk:
                        site["building_characteristics"] = {}
                
                # API Rate Limit 방지를 위한 대기
                if i + self.bc_chunk_size < len(sites_data):
                    await asyncio.sleep(1.0)  # 1초 대기
            
            return sites_data

        except Exception as e:
            self.logger.error(f"BuildingCharacteristicsAgent 실행 실패: {e}", exc_info=True)
            # 실패해도 기존 데이터는 반환
            for site in sites_data:
                if site.get("building_characteristics") is None:
                    site["building_characteristics"] = {}
            return sites_data

    def _format_risk_results(
        self,
        aal_results: List[Dict],
        hazard_results: List[Dict]
    ) -> List[Dict]:
        """
        AAL + Hazard 결과를 risk_results 형식으로 변환

        Args:
            aal_results: AAL scaled results (from aal_scaled_results table)
            hazard_results: Hazard results (from hazard_results table)

        Returns:
            List of risk result dictionaries
            [{
                "risk_type": str,
                "final_aal": float,  # SSP245 기준
                "physical_risk_score": float  # Hazard Score (0-100)
            }]
        """
        risk_map = {}

        # AAL 데이터 매핑 (SSP245 시나리오 사용)
        for aal in aal_results:
            risk_type = aal.get('risk_type')
            if risk_type:
                risk_map[risk_type] = {
                    "risk_type": risk_type,
                    "final_aal": aal.get('ssp245_final_aal', 0.0),
                    "physical_risk_score": 0.0  # Hazard에서 채울 예정
                }

        # Hazard Score 매핑 (SSP245 시나리오 사용)
        for hazard in hazard_results:
            risk_type = hazard.get('risk_type')
            if risk_type and risk_type in risk_map:
                risk_map[risk_type]["physical_risk_score"] = hazard.get('ssp245_score_100', 0.0)

        return list(risk_map.values())

    async def _process_excel(
        self,
        excel_file: str,
        site_ids: List[int]
    ) -> Optional[Dict]:
        """
        Excel 파일 처리 (AdditionalDataAgent 호출)

        Args:
            excel_file: Excel 파일 경로
            site_ids: 사업장 ID 리스트

        Returns:
            Dict with site_specific_guidelines and summary
        """
        try:
            # AdditionalDataAgent 초기화 및 실행
            agent = AdditionalDataAgent(llm_client=self.llm_client)
            result = agent.analyze(excel_file, site_ids)

            # AD의 실제 반환 구조에 맞춤
            if result.get("status") == "completed":
                return {
                    "site_specific_guidelines": result.get("site_specific_guidelines", {}),
                    "summary": result.get("summary", "")
                }
            else:
                self.logger.warning(f"Excel 분석 실패: {result.get('meta', {}).get('error', 'Unknown')}")
                return None

        except Exception as e:
            self.logger.error(f"Excel 파일 처리 실패: {e}", exc_info=True)
            return None
