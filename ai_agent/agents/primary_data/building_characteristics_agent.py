'''
파일명: building_characteristics_agent.py
작성일: 2025-12-16
버전: v11 (2섹션 간소화 + 원본 데이터 제거, State 최적화)
파일 개요: 건축물 대장 기반 물리적 취약성 정밀 분석 에이전트 (보고서 생성용 가이드라인 제공)

역할:
    - BuildingDataLoader를 통해 DB에서만 건축물 데이터 조회 (API 호출 X)
    - 데이터 기반의 물리적 취약성(Vulnerability) 및 회복력(Resilience) 요인 도출
    - LLM을 활용한 **보고서 생성 에이전트를 위한 가이드라인** 생성 (보고서 콘텐츠 직접 생성 X)
    - 다중 사업장 병렬 처리 지원 (asyncio.gather)

아키텍처:
    - building_characteristics_loader.py: ETL (API 호출 → DB 적재) ← 별도 트리거로 실행
    - building_characteristics_agent.py: 분석 (DB 조회만 → LLM → 결과) ← Node 0에서 호출

변경 이력:
    - 2025-12-08: v01 - 초기 생성 (vulnerability_analysis_agent.py)
    - 2025-12-08: v02 - BuildingDataFetcher의 fetch_full_tcfd_data 활용, 분석 및 LLM 프롬프트 강화
    - 2025-12-08: v03 - 층별 용도 텍스트 LLM 해석 지시 추가
    - 2025-12-14: v04 - building_characteristics_agent.py로 이동, 프롬프트를 가이드라인 생성용으로 수정
    - 2025-12-15: v05 - 다중 사업장 배치 처리 지원 (analyze_batch), TCFD Report v2.1 대응
    - 2025-12-15: v06 - 병렬 처리 완료 (asyncio.gather, 전체 async 전환)
    - 2025-12-15: v07 - DB 연동 추가 (building_aggregate_cache 테이블)
    - 2025-12-16: v08 - ETL 분리 (BuildingDataLoader 사용)
    - 2025-12-16: v09 - DB 조회만 하도록 수정 (API 호출 X)
    - 2025-12-16: v10 - 영어 프롬프트 + 한글 출력, 5섹션→3섹션 간소화 (토큰 효율화)
    - 2025-12-16: v11 - 2섹션 간소화 (data_summary + report_guidelines), 원본 데이터 State 전달 제거
'''

from typing import Dict, Any, List, Optional
import logging
import os
from datetime import datetime
import json # for pretty printing data to LLM
import asyncio

# BuildingDataLoader 임포트 (ETL 담당)
try:
    from .building_characteristics_loader import BuildingDataLoader
except ImportError:
    BuildingDataLoader = None
    print("⚠️ BuildingDataLoader를 임포트할 수 없습니다.")

logger = logging.getLogger(__name__)


class BuildingCharacteristicsAgent:
    """
    건축물 물리적 특성 분석 에이전트 (TCFD 보고서 생성용)
    → 보고서 생성 에이전트에 참고할 만한 가이드라인을 제공
    → v09: DB 조회만 (API 호출 X)

    플로우:
        1. 사업장 정보 (site_id 또는 주소) 받음
        2. BuildingDataLoader를 통해 DB에서만 데이터 조회 (API 호출 X)
        3. 취약성/회복력 분석
        4. LLM 가이드라인 생성
        5. 분석 결과 반환

    아키텍처:
        - BuildingDataLoader: ETL (API → DB) - 별도 트리거
        - BuildingCharacteristicsAgent: 분석 (DB 조회만 → LLM → 결과) - Node 0 호출
    """

    def __init__(self, llm_client=None, db_url: Optional[str] = None, db_manager=None):
        """
        초기화
        :param llm_client: LLM 클라이언트 인스턴스 (텍스트 생성용)
        :param db_url: Datawarehouse DB URL (building_aggregate_cache 테이블 접근용) - DEPRECATED
        :param db_manager: DatabaseManager 인스턴스 (권장)
        """
        self.logger = logger
        self.llm_client = llm_client

        # BuildingDataLoader 초기화 (ETL 담당)
        if BuildingDataLoader:
            try:
                self.data_loader = BuildingDataLoader(db_url=db_url, db_manager=db_manager)
                self.logger.info("BuildingDataLoader 초기화 성공")
            except Exception as e:
                self.logger.error(f"BuildingDataLoader 초기화 실패: {e}")
                self.data_loader = None
        else:
            self.data_loader = None

    async def analyze_batch(self, sites_data: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        다중 사업장 배치 분석 수행 (v11: 2섹션 간소화) - 병렬 처리

        :param sites_data: 사업장 정보 리스트
            각 Dict 구조: {
                "site_id": int,
                "site_info": {"latitude": float, "longitude": float, "address": str},
                "risk_results": [...],  # Optional: 리스크 점수
            }
        :return: 사업장별 분석 결과 딕셔너리 (site_id를 키로 사용)
            {
                site_id: {
                    "meta": {"analyzed_at": str, "data_source": str},
                    "agent_guidelines": {
                        "data_summary": {"one_liner": str, "key_characteristics": [...], "risk_exposure_level": str},
                        "report_guidelines": {"impact_focus": str, "mitigation_priorities": str, "reporting_tone": str}
                    }
                },
                ...
            }
        """
        self.logger.info(f"🔄 다중 사업장 건물 특성 분석 시작: {len(sites_data)}개 사업장 (병렬 처리)")

        # 병렬 처리를 위한 태스크 생성
        tasks = []
        site_ids = []

        for site_data in sites_data:
            site_id = site_data.get("site_id")
            site_info = site_data.get("site_info", {})

            lat = site_info.get("latitude")
            lon = site_info.get("longitude")
            address = site_info.get("address")

            # risk_results를 risk_scores 형식으로 변환 (Optional)
            risk_scores = self._convert_risk_results_to_scores(site_data.get("risk_results", []))

            # 각 사업장별로 async 태스크 생성
            task = self._analyze_single_site_async(site_id, lat, lon, address, risk_scores)
            tasks.append(task)
            site_ids.append(site_id)

        # 병렬 실행
        self.logger.info(f"⚡ {len(tasks)}개 사업장 병렬 분석 시작...")
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과를 dict로 변환
        results = {}
        for site_id, result in zip(site_ids, results_list):
            if isinstance(result, Exception):
                self.logger.error(f"  - 사업장 {site_id} 분석 실패: {result}")
                results[site_id] = {
                    "meta": {
                        "analyzed_at": datetime.now().isoformat(),
                        "data_source": "Error",
                        "error": str(result)
                    },
                    "agent_guidelines": {
                        "data_summary": {
                            "one_liner": "분석 실패",
                            "key_characteristics": [],
                            "risk_exposure_level": "Unknown"
                        },
                        "report_guidelines": {
                            "impact_focus": "분석 실패로 가이드라인을 생성할 수 없습니다.",
                            "mitigation_priorities": "데이터 확인 필요",
                            "reporting_tone": "neutral"
                        }
                    }
                }
            else:
                results[site_id] = result
                risk_level = result.get('agent_guidelines', {}).get('data_summary', {}).get('risk_exposure_level', 'Unknown')
                self.logger.info(f"  ✓ 사업장 {site_id} 분석 완료: {risk_level}")

        self.logger.info(f"✅ 다중 사업장 건물 특성 분석 완료: {len(results)}개 사업장")
        return results

    async def _analyze_single_site_async(
        self,
        site_id,  # int 또는 str (UUID)
        lat: float = None,
        lon: float = None,
        address: str = None,
        risk_scores: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        단일 사업장 비동기 분석 (병렬 처리용) - DB 조회만

        :param site_id: 사업장 ID (int 또는 UUID str)
        :param lat: 위도 (미사용, 호환성 유지)
        :param lon: 경도 (미사용, 호환성 유지)
        :param address: 주소 (DB 캐시 조회용)
        :param risk_scores: 리스크 점수
        :return: 분석 결과
        """
        try:
            # site_id를 str로 변환 (UUID 형식)
            site_id_str = str(site_id) if site_id else None
            return await self._analyze_single_site(lat, lon, address, risk_scores, site_id_str)
        except Exception as e:
            self.logger.error(f"사업장 {site_id} 분석 중 오류: {e}")
            return {
                "meta": {
                    "analyzed_at": datetime.now().isoformat(),
                    "location": {"address": address},
                    "error": str(e)
                },
                "building_data": {},
                "structural_grade": "Unknown",
                "vulnerabilities": [],
                "resilience": [],
                "agent_guidelines": "분석 실패로 가이드라인을 생성할 수 없습니다."
            }

    def _convert_risk_results_to_scores(self, risk_results: List[Dict]) -> Dict[str, Any]:
        """
        risk_results를 risk_scores 형식으로 변환

        risk_results 예시:
        [
            {"risk_type": "river_flood", "final_aal": 5.2, "physical_risk_score": 68.5},
            ...
        ]

        risk_scores 예시:
        {
            "river_flood": {"aal": 5.2, "physical_risk_score": 68.5},
            ...
        }
        """
        risk_scores = {}
        for result in risk_results:
            risk_type = result.get("risk_type")
            if risk_type:
                risk_scores[risk_type] = {
                    "aal": result.get("final_aal", 0),
                    "physical_risk_score": result.get("physical_risk_score", 0)
                }
        return risk_scores

    async def analyze(
        self,
        lat: float = None,
        lon: float = None,
        address: str = None,
        risk_scores: Dict[str, Any] = None,
        site_id: str = None
    ) -> Dict[str, Any]:
        """
        단일 사업장 분석 (하위 호환성 유지) - 비동기

        ⚠️ 새로운 코드에서는 analyze_batch() 사용을 권장합니다.
        """
        return await self._analyze_single_site(lat, lon, address, risk_scores, site_id)

    async def _analyze_single_site(
        self,
        lat: float = None,
        lon: float = None,
        address: str = None,
        risk_scores: Dict[str, Any] = None,
        site_id: str = None
    ) -> Dict[str, Any]:
        """
        건물 특성 분석 수행 (비동기) - DB 조회만

        :param lat: 위도 (미사용, 호환성 유지)
        :param lon: 경도 (미사용, 호환성 유지)
        :param address: (선택) 도로명 주소 - DB 캐시 조회에 사용
        :param risk_scores: (선택) 외부에서 계산된 리스크 점수 딕셔너리
        :param site_id: (선택) 사업장 UUID - DB 조회에 사용
        :return: 분석 결과 (데이터, 취약/회복 요인, 가이드라인)
        """
        self.logger.info(f"건물 특성 분석 시작: site_id={site_id}, address={address}")

        # 1. 데이터 수집 (DB 캐시에서만 조회 - API 호출 X)
        building_data = self._fetch_data(lat, lon, address, site_id)

        # 2. 요인 분석
        vulnerabilities = self._identify_vulnerabilities(building_data)
        resilience = self._identify_resilience(building_data)

        # 3. 구조적 등급 평가
        structural_grade = self._evaluate_structural_grade(building_data)

        # 4. LLM 가이드라인 생성 (보고서 에이전트용) - 비동기
        guidelines = await self._generate_llm_guidelines(
            building_data,
            vulnerabilities,
            resilience,
            structural_grade,
            risk_scores
        )

        # 5. 원본 건물 데이터에서 주요 정보 추출 (API 응답용)
        physical_specs = building_data.get('physical_specs', {}) if building_data else {}
        floors = physical_specs.get('floors', {})
        seismic = physical_specs.get('seismic', {})

        building_summary = {
            "area": physical_specs.get('total_area'),  # 면적
            "grndflr_cnt": floors.get('ground'),  # 지상층수
            "ugrn_flr_cnt": floors.get('underground'),  # 지하층수
            "rserthqk_dsgn_apply_yn": seismic.get('applied', 'N')  # 내진설계적용여부
        }

        result = {
            "meta": {
                "analyzed_at": datetime.now().isoformat(),
                "data_source": "building_aggregate_cache (DB)" if self.data_loader else "Fallback Data"
            },
            "agent_guidelines": guidelines,  # data_summary + report_guidelines
            "building_summary": building_summary  # 원본 건물 데이터 요약
        }

        self.logger.info("건물 특성 분석 완료")
        return result

    def _fetch_data(
        self,
        lat: float = None,
        lon: float = None,
        address: str = None,
        site_id: str = None
    ) -> Dict[str, Any]:
        """
        BuildingDataLoader를 통한 건축물 데이터 조회 (DB만 - API 호출 X)

        조회 우선순위:
            1. cache_id (= site_id) 직접 매칭 (가장 정확함)
            2. 도로명 주소 매칭 (Fallback)

        Args:
            lat: 위도 (미사용, 호환성 유지)
            lon: 경도 (미사용, 호환성 유지)
            address: 도로명 주소 (Fallback용)
            site_id: 사업장 UUID (cache_id로 사용)

        Returns:
            BuildingDataFetcher 형식의 건축물 데이터
        """
        if not self.data_loader:
            self.logger.warning("DataLoader 없음, 빈 데이터 반환")
            return {}

        try:
            # 1. cache_id (= site_id)로 직접 조회 (최우선)
            if site_id:
                data = self.data_loader.fetch_from_db_only(cache_id=site_id)
                if data:
                    self.logger.info(f"building_aggregate_cache에서 cache_id로 데이터 조회 완료: {site_id}")
                    return data
                else:
                    self.logger.warning(f"building_aggregate_cache에 cache_id={site_id} 데이터 없음, 주소로 재시도")

            # 2. Fallback: 주소로 building_aggregate_cache 조회
            if address:
                data = self.data_loader.fetch_from_db_only(road_address=address)
                if data:
                    self.logger.info(f"building_aggregate_cache에서 주소로 데이터 조회 완료: {address}")
                    return data

            # DB에 데이터 없으면 빈 데이터 반환 (API 호출 X)
            self.logger.warning(f"building_aggregate_cache에 데이터 없음 (site_id={site_id}, address={address})")
            return {}

        except Exception as e:
            self.logger.error(f"DB 데이터 조회 중 오류: {e}")
            return {}

    def _identify_vulnerabilities(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """취약성 요인 식별 로직 (건축물 대장 API 기반만 사용)"""
        factors = []

        if not data:
            return factors

        physical_specs = data.get('physical_specs', {})
        floor_details = data.get('floor_details', [])

        # 1. 노후도 (Aging)
        age = physical_specs.get('age', {}).get('years', 0)
        if age >= 40:
            factors.append({
                "category": "Structural",
                "factor": "심각한 노후화",
                "severity": "Very High",
                "description": f"준공 {age}년차 건물로, 구조적 성능 저하 및 내구성 부족 가능성이 매우 높음"
            })
        elif age >= 30:
            factors.append({
                "category": "Structural",
                "factor": "건물 노후화",
                "severity": "High",
                "description": f"준공 {age}년차 건물로, 설비 및 마감재 노후화 진행 우려"
            })

        # 2. 내진 설계 미적용/취약 (Seismic Vulnerability) - 다중 건물 집계
        seismic_info = physical_specs.get('seismic', {})
        buildings_with_design = seismic_info.get('buildings_with_design', 0)
        buildings_without_design = seismic_info.get('buildings_without_design', 0)
        total_buildings = buildings_with_design + buildings_without_design

        if total_buildings > 0:
            if buildings_without_design > buildings_with_design:
                factors.append({
                    "category": "Seismic",
                    "factor": "다수 건물 내진 설계 미적용",
                    "severity": "Very High",
                    "description": f"총 {total_buildings}개 건물 중 {buildings_without_design}개가 내진 설계 미적용 ({buildings_without_design/total_buildings*100:.1f}%)"
                })
            elif buildings_without_design > 0:
                factors.append({
                    "category": "Seismic",
                    "factor": "일부 건물 내진 설계 미적용",
                    "severity": "High",
                    "description": f"총 {total_buildings}개 건물 중 {buildings_without_design}개가 내진 설계 미적용"
                })


        # 3. 지하층 및 중요 설비 (Basement & Critical Facilities)
        max_underground = physical_specs.get('floors', {}).get('max_underground', 0)
        has_potential_critical_facility = False

        if max_underground > 0:
            factors.append({
                "category": "Flood",
                "factor": "지하층 보유 건물 존재",
                "severity": "Medium" if max_underground == 1 else "High",
                "description": f"최대 지하 {max_underground}층까지 보유한 건물이 있어 침수 시 피해 위험"
            })

            # 지하층 용도에서 중요 설비 키워드 탐지
            for floor in floor_details:
                if floor.get('type') == 'Underground' and floor.get('is_potentially_critical'):
                    has_potential_critical_facility = True

            if has_potential_critical_facility:
                factors.append({
                    "category": "Flood/Operational",
                    "factor": "지하 중요 설비 의심",
                    "severity": "High",
                    "description": "지하층 용도에 기계실/전기실 등 중요 설비 관련 키워드가 포함되어 있어 침수 시 운영 중단 위험 (LLM 상세 분석 필요)"
                })

        # 4. 필로티 구조 추정 (Piloti Structure)
        structure = physical_specs.get('structure', '')
        ground_floors = physical_specs.get('floors', {}).get('ground', 0)
        # 1층이 주차장이고 철근콘크리트 구조이며 3층 이상인 경우 필로티로 추정
        if '철근콘크리트' in structure and ground_floors >= 3:
            first_floor_parking = any(
                "주차장" in f.get('usage_main', '') 
                for f in floor_details 
                if f.get('floor_no') == 1
            )
            if first_floor_parking:
                factors.append({
                    "category": "Structural",
                    "factor": "필로티 구조 (추정)",
                    "severity": "High",
                    "description": "1층 주차장 + 철근콘크리트 구조로 필로티 구조 추정, 지진 시 층 붕괴 위험 및 침수 취약성 존재"
                })

        return factors

    def _identify_resilience(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """회복력/강점 요인 식별 로직 (건축물 대장 API 기반만 사용)"""
        factors = []

        if not data:
            return factors

        physical_specs = data.get('physical_specs', {})
        transition_specs = data.get('transition_specs', {})
        floor_details = data.get('floor_details', [])

        # 1. 신축 건물
        age = physical_specs.get('age', {}).get('years', 0)
        if age < 10:
            factors.append({
                "category": "Structural",
                "factor": "최신 건축 기준 적용",
                "strength": "High",
                "description": f"준공 {age}년차 신축 건물로 최신 내진 및 소방 기준이 적용되었을 가능성 높음"
            })

        # 2. 내진 설계 적용 (Seismic Resilience)
        seismic_applied = physical_specs.get('seismic', {}).get('applied', 'Unknown')
        if seismic_applied == 'Y':
            seismic_ability = physical_specs.get('seismic', {}).get('ability', '')
            desc = "내진 설계가 적용되어 지진에 대한 구조적 안정성 확보"
            if seismic_ability:
                desc += f" (내진능력: {seismic_ability})"
            factors.append({
                "category": "Seismic",
                "factor": "내진 설계 적용",
                "strength": "Very High",
                "description": desc
            })

        # 3. 저수조 (가뭄 대응)
        has_water_tank = any('저수조' in f.get('usage_etc', '') for f in floor_details)
        if has_water_tank:
            factors.append({
                "category": "Drought",
                "factor": "저수조 보유",
                "strength": "Medium",
                "description": "비상 용수 확보 시설(저수조) 보유로 가뭄 및 단수 시 회복력 존재"
            })

        # 4. 견고한 구조재 (Structure Resilience)
        structure = physical_specs.get('structure', '')
        if '철근콘크리트' in structure or '철골' in structure:
             factors.append({
                "category": "Fire/Wind",
                "factor": "견고한 구조재",
                "strength": "Medium",
                "description": f"{structure} 구조로 화재 및 강풍에 대한 저항성 보유"
            })

        return factors

    def _evaluate_structural_grade(self, data: Dict[str, Any]) -> str:
        """건축물 대장 데이터 기반 구조적 안전 등급 평가 (A~E)"""
        if not data:
            return "Unknown"

        score = 100  # 기준점
        physical_specs = data.get('physical_specs', {})
        floor_details = data.get('floor_details', [])

        # 1. 노후도 (감점)
        age = physical_specs.get('age', {}).get('years', 0)
        score -= min(age * 1, 50)  # 1년당 1점 감점, 최대 50점

        # 2. 내진 설계 미적용 (감점)
        seismic_applied = physical_specs.get('seismic', {}).get('applied', 'Unknown')
        if seismic_applied == 'N':
            score -= 20
        elif not physical_specs.get('seismic', {}).get('ability', ''):
            score -= 10  # 내진능력 미명시

        # 3. 필로티 구조 추정 (감점)
        structure = physical_specs.get('structure', '')
        ground_floors_count = physical_specs.get('floors', {}).get('ground', 0)
        is_piloti_suspected = (
            ('철근콘크리트' in structure or '철골' in structure) 
            and ground_floors_count >= 3 
            and any("주차장" in f.get('usage_main', '') for f in floor_details if f.get('floor_no') == 1)
        )
        if is_piloti_suspected:
            score -= 15

        # 4. 지하 중요 설비 존재 (감점)
        has_critical_basement = any(
            f.get('type') == 'Underground' and f.get('is_potentially_critical') 
            for f in floor_details
        )
        if has_critical_basement:
            score -= 15

        # 5. 구조재 평가
        if '철근콘크리트' in structure or '철골' in structure:
            score += 10  # 견고한 구조
        elif '목구조' in structure or '조적조' in structure:
            score -= 10  # 취약 구조

        # 6. 저수조 보유 (가점)
        has_water_tank = any('저수조' in f.get('usage_etc', '') for f in floor_details)
        if has_water_tank:
            score += 5

        # 등급 산정
        if score >= 90:
            return "A (Excellent)"
        elif score >= 80:
            return "B (Good)"
        elif score >= 70:
            return "C (Fair)"
        elif score >= 60:
            return "D (Poor)"
        else:
            return "E (Very Poor)"

    async def _generate_llm_guidelines(
        self,
        data: Dict[str, Any],
        vulnerabilities: List[Dict],
        resilience: List[Dict],
        grade: str,
        risk_scores: Dict = None
    ) -> Dict[str, Any]:
        """
        LLM을 활용한 보고서 생성 가이드라인 생성 (비동기)

        v08 업데이트: JSON 구조화 출력 반환
        - 기존: str (마크다운 텍스트)
        - 변경: Dict (구조화된 JSON)

        Returns:
            Dict: {
                "building_summary": {...},
                "vulnerability_summary": {...},
                "impact_analysis_guide": {...},
                "mitigation_recommendations": {...},
                "report_narrative_guide": {...}
            }
        """

        # LLM 사용
        if self.llm_client:
            try:
                prompt = self._build_prompt(data, vulnerabilities, resilience, grade, risk_scores)

                # 비동기 LLM 호출
                if hasattr(self.llm_client, 'ainvoke'):
                    response = await self.llm_client.ainvoke(prompt)
                else:
                    # Fallback to sync invoke
                    response = self.llm_client.invoke(prompt)

                # AIMessage 객체에서 텍스트 추출
                if hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)

                # JSON 파싱 시도
                parsed_guidelines = self._parse_llm_json_response(response_text)
                if parsed_guidelines:
                    self.logger.info("LLM JSON 가이드라인 파싱 성공")
                    return parsed_guidelines

                # JSON 파싱 실패 시 텍스트로 반환 (하위 호환성)
                self.logger.warning("LLM JSON 파싱 실패, 텍스트로 반환")
                return {"raw_text": response_text}

            except Exception as e:
                self.logger.error(f"LLM 가이드라인 생성 실패: {e}")
                return self._generate_fallback_guidelines_json(data, vulnerabilities, grade)

        return self._generate_fallback_guidelines_json(data, vulnerabilities, grade)

    def _parse_llm_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        LLM 응답에서 JSON 추출 및 파싱

        Args:
            response_text: LLM 응답 텍스트

        Returns:
            Dict: 파싱된 JSON 또는 None
        """
        import re

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

    def _generate_fallback_guidelines_json(
        self,
        data: Dict[str, Any],
        vulnerabilities: List[Dict],
        grade: str
    ) -> Dict[str, Any]:
        """
        LLM 실패 시 기본 JSON 가이드라인 생성 (v11: 2섹션 구조)

        Returns:
            Dict: {"data_summary": {...}, "report_guidelines": {...}}
        """
        meta = data.get('meta', {})
        physical_specs = data.get('physical_specs', {})
        age = physical_specs.get('age', {}).get('years', 0)
        structure = physical_specs.get('structure', '미상')
        seismic = physical_specs.get('seismic', {}).get('applied', 'N')

        # 주요 특성 추출
        characteristics = [f"준공 {age}년차 건물", f"구조: {structure}"]

        # 취약점/회복력 요약
        if vulnerabilities:
            characteristics.append(f"주요 취약점: {vulnerabilities[0].get('factor', '')}")
        if seismic == 'Y':
            characteristics.append("내진설계 적용")

        # 리스크 레벨 결정
        if 'E' in grade or 'D' in grade:
            risk_level = "High"
            tone = "warning"
        elif 'C' in grade:
            risk_level = "Medium"
            tone = "neutral"
        else:
            risk_level = "Low"
            tone = "positive"

        return {
            "data_summary": {
                "one_liner": f"{age}년 경과 {structure} 건물, 구조등급 {grade}",
                "key_characteristics": characteristics[:3],  # 최대 3개
                "risk_exposure_level": risk_level
            },
            "report_guidelines": {
                "impact_focus": f"구조등급 {grade} 건물의 물리적 리스크 노출 분석 (재무/운영/자산)",
                "mitigation_priorities": "단기: 취약 지점 점검, 중기: 설비 보강, 장기: 리스크 저감 전략",
                "reporting_tone": tone
            },
            "_fallback": True  # Fallback 가이드라인임을 표시
        }

    def _infer_related_risks(self, category: str) -> List[str]:
        """카테고리에서 관련 리스크 타입 추론"""
        category_lower = category.lower()
        risk_mapping = {
            "flood": ["river_flood", "urban_flood"],
            "seismic": ["typhoon"],
            "structural": ["typhoon", "extreme_heat"],
            "fire": ["wildfire", "extreme_heat"],
            "wind": ["typhoon"],
            "drought": ["drought", "water_stress"],
            "heat": ["extreme_heat"],
            "cold": ["extreme_cold"]
        }

        for key, risks in risk_mapping.items():
            if key in category_lower:
                return risks

        return ["general"]


    def _generate_fallback_guidelines(
        self,
        data: Dict[str, Any],
        vulnerabilities: List[Dict],
        resilience: List[Dict],
        grade: str
    ) -> str:
        """LLM 실패 시 기본 가이드라인 생성"""
        guidelines = "## 보고서 생성 가이드라인 (자동 생성)\n\n"

        meta = data.get('meta', {})
        physical_specs = data.get('physical_specs', {})

        guidelines += "### 1. 건물 구조적 특징 요약\n"
        guidelines += f"- 주소: {meta.get('address', '미상')}\n"
        guidelines += f"- 구조: {physical_specs.get('structure', '미상')}, {physical_specs.get('age', {}).get('years', '?')}년 경과\n"
        guidelines += f"- 구조 등급: {grade}\n"

        guidelines += "\n### 2. Strategy 섹션 작성 방향\n"
        guidelines += "- LLM 분석 실패로 기본 가이드라인만 제공됩니다.\n"

        guidelines += "\n### 3. P1~P5 영향 분석 강조 포인트\n"
        if vulnerabilities:
            for v in vulnerabilities[:3]:  # 상위 3개만
                guidelines += f"- {v['factor']}: {v['description']}\n"

        guidelines += "\n### 4. 대응 방안 작성 시 활용할 회복력 요인\n"
        if resilience:
            for r in resilience[:3]:  # 상위 3개만
                guidelines += f"- {r['factor']}: {r['description']}\n"

        guidelines += "\n### 5. 보고서 톤 & 스타일 권장사항\n"
        guidelines += "- LLM 정상 작동 시 더 상세한 가이드라인을 제공합니다.\n"

        return guidelines

    def _build_prompt(
        self,
        data: Dict[str, Any],
        vulnerabilities: List[Dict],
        resilience: List[Dict],
        grade: str,
        risk_scores: Dict = None
    ) -> str:
        """
        LLM 프롬프트 구성 (TCFD 보고서 노드용 구조화된 가이드라인 생성)

        v10 업데이트: 간소화된 영어 프롬프트 + 한글 출력 (토큰 효율화)
        - 5개 섹션 → 3개 섹션으로 축소
        - Node 2-B (Impact Analysis): analysis_guidelines.impact_focus 활용
        - Node 2-C (Mitigation Strategies): analysis_guidelines.mitigation_priorities 활용
        - Node 3 (Strategy Section): vulnerability_summary 활용
        """

        meta = data.get('meta', {})
        physical_specs = data.get('physical_specs', {})
        floor_details = data.get('floor_details', [])
        geo_risks = data.get('geo_risks', {})

        # Building info summary
        building_age = physical_specs.get('age', {}).get('years', 0)
        structure_type = physical_specs.get('structure', 'Unknown')
        seismic_applied = physical_specs.get('seismic', {}).get('applied', 'Unknown')
        max_underground = physical_specs.get('floors', {}).get('max_underground', 0)
        ground_floors = physical_specs.get('floors', {}).get('ground', 0)

        # River & coast distance
        river_info = geo_risks.get('river', {})
        river_distance = river_info.get('distance_m', 'N/A') if river_info else 'N/A'
        coast_distance = geo_risks.get('coast_distance_m', 'N/A')

        # Underground critical facilities check
        basement_critical = any(
            f.get('type') == 'Underground' and f.get('is_potentially_critical')
            for f in floor_details
        )

        prompt = f"""<ROLE>
You are a TCFD building analysis expert. Analyze building data and generate **concise guidelines** for TCFD report agents.
</ROLE>

<BUILDING_DATA>
Address: {meta.get('address', 'N/A')}
Age: {building_age} years (Built: {physical_specs.get('age', {}).get('completion_year', 'N/A')})
Structure: {structure_type} | Seismic: {seismic_applied} | Grade: {grade}
Floors: {ground_floors} above, {max_underground} below
River: {river_distance}m | Coast: {coast_distance}m

Basement: {json.dumps([f for f in floor_details if f.get('type') == 'Underground'], ensure_ascii=False) if floor_details else 'None'}

Vulnerabilities: {self._format_list(vulnerabilities) if vulnerabilities else 'None'}
Resilience: {self._format_list(resilience) if resilience else 'None'}
Risk Scores: {self._format_dict(risk_scores) if risk_scores else 'None'}
</BUILDING_DATA>

<OUTPUT_FORMAT>
Generate JSON with 3 sections (Hybrid Structure):

{{
  "data_summary": {{
    "one_liner": "Comprehensive 1-2 sentence building summary (100-150 chars). Include age, structure type, key vulnerability factor.",
    "key_characteristics": ["Provide 4-5 characteristics, each 60-100 chars with SPECIFIC details. Example: '35-year-old reinforced concrete building with no seismic retrofitting, high earthquake vulnerability'", "Include: age/condition, structure type/materials, seismic status, basement facilities, flood exposure"],
    "risk_exposure_level": "High/Medium/Low with brief justification"
  }},

  "report_guidelines": {{
    "impact_focus": "4-6 sentences (250-350 chars) on financial impacts (asset damage costs, insurance implications), operational impacts (business interruption, supply chain risks), and strategic risks (long-term value deterioration). Be specific with risk categories.",
    "mitigation_priorities": "4-6 sentences (250-350 chars) with SPECIFIC actions: Short-term (0-6 months): immediate inspections/repairs. Mid-term (6-24 months): structural reinforcements/equipment upgrades. Long-term (2-5 years): strategic relocation/major renovations. Include cost-benefit considerations.",
    "reporting_tone": "warning/neutral/positive"
  }},

  "detailed_context": "Comprehensive natural narrative (6-10 paragraphs, 1200-1800 chars). MUST cover ALL of the following in detail: (1) Building age and structural integrity assessment, (2) Structure type and material analysis with specific vulnerabilities, (3) Seismic design status and earthquake risk exposure, (4) Basement facilities inventory and critical infrastructure locations (electrical rooms, mechanical systems, server rooms), (5) Flood risk assessment considering river/coast proximity and underground floors, (6) Overall vulnerability synthesis with severity rankings, (7) Resilience factors and existing protective measures. Each paragraph should provide actionable insights for downstream TCFD report generation agents."
}}

**OUTPUT LANGUAGE: Korean (한글).** All text must be in Korean (한글) for local stakeholders.

**CRITICAL LENGTH REQUIREMENTS:**
- Total output: 1500-2500 characters MINIMUM
- detailed_context: 1200-1800 characters (most critical section)
- key_characteristics: Each item should be 60-100 characters with specific details
- impact_focus: 250-350 characters with concrete financial/operational impacts
- mitigation_priorities: 250-350 characters with specific short/mid/long-term actions

⚠️ OUTPUT THAT IS SHORTER THAN 1500 CHARACTERS WILL BE REJECTED. Provide comprehensive, detailed analysis.

Output pure JSON only. No markdown.
</OUTPUT_FORMAT>
"""
        return prompt

    def _format_list(self, items: List[Dict]) -> str:
        if not items: return "(없음)"
        return "\n".join([f"- **{item.get('factor')} ({item.get('category', '')})**: {item.get('description', '')} (심각도: {item.get('severity', item.get('strength', ''))})" for item in items])

    def _format_dict(self, items: Dict) -> str:
        if not items: return "(없음)"
        formatted_str = ""
        for k, v in items.items():
            if isinstance(v, dict):
                formatted_str += f"- **{k}**:\n"
                for sub_k, sub_v in v.items():
                    formatted_str += f"  - {sub_k}: {sub_v}\n"
            else:
                formatted_str += f"- {k}: {v}\n"
        return formatted_str
