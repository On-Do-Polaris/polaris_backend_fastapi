'''
파일명: building_characteristics_agent.py
작성일: 2025-12-15
버전: v07 (TCFD Report v2.1 - DB 연동 추가)
파일 개요: 건축물 대장 기반 물리적 취약성 정밀 분석 에이전트 (보고서 생성용 가이드라인 제공)

역할:
    - BuildingDataFetcher를 통해 실시간 건축물 정보 및 지리 정보 수집
    - DB(building_aggregate_cache)에 데이터 적재 후 조회하여 분석
    - 데이터 기반의 물리적 취약성(Vulnerability) 및 회복력(Resilience) 요인 도출
    - LLM을 활용한 **보고서 생성 에이전트를 위한 가이드라인** 생성 (보고서 콘텐츠 직접 생성 X)
    - 다중 사업장 병렬 처리 지원 (asyncio.gather)

변경 이력:
    - 2025-12-08: v01 - 초기 생성 (vulnerability_analysis_agent.py)
    - 2025-12-08: v02 - BuildingDataFetcher의 fetch_full_tcfd_data 활용, 분석 및 LLM 프롬프트 강화
    - 2025-12-08: v03 - 층별 용도 텍스트 LLM 해석 지시 추가
    - 2025-12-14: v04 - building_characteristics_agent.py로 이동, 프롬프트를 가이드라인 생성용으로 수정
    - 2025-12-15: v05 - 다중 사업장 배치 처리 지원 (analyze_batch), TCFD Report v2.1 대응
    - 2025-12-15: v06 - 병렬 처리 완료 (asyncio.gather, 전체 async 전환)
    - 2025-12-15: v07 - DB 연동 추가 (building_aggregate_cache 테이블)
'''

from typing import Dict, Any, List, Optional
import logging
import os
from datetime import datetime
import json # for pretty printing data to LLM
import asyncio

# BuildingDataFetcher 임포트
try:
    from ...utils.building_data_fetcher import BuildingDataFetcher
except ImportError:
    BuildingDataFetcher = None
    print("⚠️ BuildingDataFetcher를 임포트할 수 없습니다.")

# DatabaseManager 임포트
try:
    from ...utils.database import DatabaseManager
except ImportError:
    DatabaseManager = None
    print("⚠️ DatabaseManager를 임포트할 수 없습니다.")

logger = logging.getLogger(__name__)


class BuildingCharacteristicsAgent:
    """
    건축물 물리적 특성 분석 에이전트 (TCFD 보고서 생성용)
    → 보고서 생성 에이전트에 참고할 만한 가이드라인을 제공
    → v05: 다중 사업장 배치 처리 지원 (TCFD Report v2.1)
    → v07: DB 연동 추가 (building_aggregate_cache)

    플로우:
        1. 사업장 정보 (주소) 받음
        2. DB 캐시 확인 → 있으면 캐시에서 로드
        3. 캐시 없으면 → API 호출 → DB에 저장
        4. DB에서 데이터 로드
        5. LLM 분석
        6. 분석 결과만 state로 전달
    """

    def __init__(self, llm_client=None, db_url: Optional[str] = None):
        """
        초기화
        :param llm_client: LLM 클라이언트 인스턴스 (텍스트 생성용)
        :param db_url: Datawarehouse DB URL (building_aggregate_cache 테이블 접근용)
        """
        self.logger = logger
        self.llm_client = llm_client

        # BuildingDataFetcher 초기화
        if BuildingDataFetcher:
            try:
                self.fetcher = BuildingDataFetcher()
                self.logger.info("BuildingDataFetcher 초기화 성공")
            except Exception as e:
                self.logger.error(f"BuildingDataFetcher 초기화 실패: {e}")
                self.fetcher = None
        else:
            self.fetcher = None

        # DatabaseManager 초기화 (datawarehouse DB)
        self.db_manager = None
        if DatabaseManager:
            try:
                # datawarehouse DB URL 사용
                dw_db_url = db_url or os.getenv('DATAWAREHOUSE_DATABASE_URL') or os.getenv('DATABASE_URL')
                if dw_db_url:
                    self.db_manager = DatabaseManager(dw_db_url)
                    self.logger.info("DatabaseManager 초기화 성공 (building_aggregate_cache)")
                else:
                    self.logger.warning("DB URL이 설정되지 않음 - DB 캐시 비활성화")
            except Exception as e:
                self.logger.error(f"DatabaseManager 초기화 실패: {e}")
                self.db_manager = None

    async def analyze_batch(self, sites_data: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        다중 사업장 배치 분석 수행 (TCFD Report v2.1) - 병렬 처리

        :param sites_data: 사업장 정보 리스트
            각 Dict 구조: {
                "site_id": int,
                "site_info": {"latitude": float, "longitude": float, "address": str},
                "risk_results": [...],  # Optional: 리스크 점수
            }
        :return: 사업장별 분석 결과 딕셔너리 (site_id를 키로 사용)
            {
                site_id: {
                    "meta": {...},
                    "building_data": {...},
                    "structural_grade": str,
                    "vulnerabilities": [...],
                    "resilience": [...],
                    "agent_guidelines": str
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
                        "location": {},
                        "error": str(result)
                    },
                    "building_data": {},
                    "structural_grade": "Unknown",
                    "vulnerabilities": [],
                    "resilience": [],
                    "agent_guidelines": "분석 실패로 가이드라인을 생성할 수 없습니다."
                }
            else:
                results[site_id] = result
                self.logger.info(f"  ✓ 사업장 {site_id} 분석 완료: {result.get('structural_grade', 'Unknown')}")

        self.logger.info(f"✅ 다중 사업장 건물 특성 분석 완료: {len(results)}개 사업장")
        return results

    async def _analyze_single_site_async(
        self,
        site_id: int,
        lat: float,
        lon: float,
        address: str = None,
        risk_scores: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        단일 사업장 비동기 분석 (병렬 처리용)

        :param site_id: 사업장 ID
        :param lat: 위도
        :param lon: 경도
        :param address: 주소
        :param risk_scores: 리스크 점수
        :return: 분석 결과
        """
        try:
            return await self._analyze_single_site(lat, lon, address, risk_scores)
        except Exception as e:
            self.logger.error(f"사업장 {site_id} 분석 중 오류: {e}")
            return {
                "meta": {
                    "analyzed_at": datetime.now().isoformat(),
                    "location": {"lat": lat, "lon": lon},
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

    async def analyze(self, lat: float, lon: float, address: str = None, risk_scores: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        단일 사업장 분석 (하위 호환성 유지) - 비동기

        ⚠️ 새로운 코드에서는 analyze_batch() 사용을 권장합니다.
        """
        return await self._analyze_single_site(lat, lon, address, risk_scores)

    async def _analyze_single_site(self, lat: float, lon: float, address: str = None, risk_scores: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        위치 기반 건물 특성 분석 수행 (비동기)

        :param lat: 위도
        :param lon: 경도
        :param address: (선택) 도로명 주소 - 제공 시 더 정확한 데이터 조회 가능
        :param risk_scores: (선택) 외부에서 계산된 리스크 점수 딕셔너리
        :return: 분석 결과 (데이터, 취약/회복 요인, 가이드라인)
        """
        self.logger.info(f"건물 특성 분석 시작: lat={lat}, lon={lon}, address={address}")

        # 1. 데이터 수집 (fetch_full_tcfd_data 활용)
        building_data = self._fetch_data(lat, lon, address)

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

        result = {
            "meta": {
                "analyzed_at": datetime.now().isoformat(),
                "location": {"lat": lat, "lon": lon},
                "data_source": "Architectural HUB API (TCFD Enhanced)" if self.fetcher else "Fallback Data"
            },
            "building_data": building_data,
            "structural_grade": structural_grade,
            "vulnerabilities": vulnerabilities,
            "resilience": resilience,
            "agent_guidelines": guidelines  # ← 보고서 에이전트가 사용할 가이드라인
        }

        self.logger.info("건물 특성 분석 완료")
        return result

    def _fetch_data(self, lat: float, lon: float, address: str = None) -> Dict[str, Any]:
        """
        BuildingDataFetcher를 통한 TCFD 데이터 조회 (DB 캐시 활용)

        플로우:
            1. 주소 코드 추출
            2. DB 캐시 확인 → 있으면 캐시 데이터 반환
            3. 캐시 없으면 → API 호출 → DB 저장 → 데이터 반환
        """
        if not self.fetcher:
            self.logger.warning("Fetcher 없음, 빈 데이터 반환")
            return {}

        try:
            # 1. API로 데이터 조회 (주소 코드도 함께 반환됨)
            data = self.fetcher.fetch_full_tcfd_data(lat, lon, address)

            if not data:
                self.logger.warning(f"API에서 데이터 조회 실패: lat={lat}, lon={lon}")
                return {}

            # 2. 주소 코드 추출 (meta에서)
            meta = data.get('meta', {})
            sigungu_cd = meta.get('sigungu_cd', '')
            bjdong_cd = meta.get('bjdong_cd', '')
            bun = meta.get('bun', '')
            ji = meta.get('ji', '')

            # 3. DB 캐시에 저장 (주소 코드가 있는 경우만)
            if self.db_manager and sigungu_cd and bjdong_cd and bun and ji:
                try:
                    self.db_manager.save_building_aggregate_cache(
                        sigungu_cd=sigungu_cd,
                        bjdong_cd=bjdong_cd,
                        bun=bun,
                        ji=ji,
                        building_data=data
                    )
                    self.logger.info(f"DB 캐시 저장 완료: {sigungu_cd}-{bjdong_cd}-{bun}-{ji}")
                except Exception as cache_error:
                    self.logger.warning(f"DB 캐시 저장 실패 (계속 진행): {cache_error}")

            return data

        except Exception as e:
            self.logger.error(f"TCFD 데이터 조회 중 오류: {e}")
            return {}

    def _fetch_data_from_cache(
        self,
        sigungu_cd: str,
        bjdong_cd: str,
        bun: str,
        ji: str
    ) -> Optional[Dict[str, Any]]:
        """
        DB 캐시에서 빌딩 데이터 조회

        Args:
            sigungu_cd: 시군구 코드
            bjdong_cd: 법정동 코드
            bun: 번
            ji: 지

        Returns:
            BuildingDataFetcher 형식의 데이터 또는 None
        """
        if not self.db_manager:
            return None

        try:
            cache_data = self.db_manager.fetch_building_aggregate_cache(
                sigungu_cd=sigungu_cd,
                bjdong_cd=bjdong_cd,
                bun=bun,
                ji=ji
            )

            if cache_data:
                self.logger.info(f"DB 캐시에서 데이터 로드: {sigungu_cd}-{bjdong_cd}-{bun}-{ji}")
                return self.db_manager.convert_cache_to_building_data(cache_data)

            return None

        except Exception as e:
            self.logger.error(f"DB 캐시 조회 실패: {e}")
            return None

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
                return self._generate_fallback_guidelines_json(data, vulnerabilities, resilience, grade)

        return self._generate_fallback_guidelines_json(data, vulnerabilities, resilience, grade)

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
        resilience: List[Dict],
        grade: str
    ) -> Dict[str, Any]:
        """
        LLM 실패 시 기본 JSON 가이드라인 생성

        Returns:
            Dict: 구조화된 fallback 가이드라인
        """
        meta = data.get('meta', {})
        physical_specs = data.get('physical_specs', {})
        age = physical_specs.get('age', {}).get('years', 0)
        structure = physical_specs.get('structure', '미상')

        # 취약 요인 변환
        high_risk_factors = []
        for v in vulnerabilities[:5]:  # 최대 5개
            high_risk_factors.append({
                "factor": v.get('factor', ''),
                "related_risks": self._infer_related_risks(v.get('category', '')),
                "severity": v.get('severity', 'Medium'),
                "impact_description": v.get('description', '')
            })

        # 회복력 요인 변환
        resilience_factors = []
        for r in resilience[:5]:  # 최대 5개
            resilience_factors.append({
                "factor": r.get('factor', ''),
                "related_risks": self._infer_related_risks(r.get('category', '')),
                "strength": r.get('strength', 'Medium'),
                "benefit_description": r.get('description', '')
            })

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
            "building_summary": {
                "one_liner": f"{age}년 경과 {structure} 건물, 구조등급 {grade}",
                "key_characteristics": [
                    f"준공 {age}년차 건물",
                    f"구조: {structure}",
                    f"구조안전등급: {grade}"
                ],
                "risk_exposure_level": risk_level
            },
            "vulnerability_summary": {
                "high_risk_factors": high_risk_factors,
                "resilience_factors": resilience_factors
            },
            "impact_analysis_guide": {
                "financial_impact": {
                    "estimated_exposure": risk_level,
                    "key_cost_drivers": ["건물 노후화", "설비 손상 위험"],
                    "narrative": "LLM 분석 실패로 기본 가이드라인 제공. 상세 분석 필요."
                },
                "operational_impact": {
                    "critical_systems_at_risk": ["전기 설비", "기계 설비"],
                    "estimated_downtime": "산정 필요",
                    "narrative": "LLM 분석 실패로 기본 가이드라인 제공. 상세 분석 필요."
                },
                "asset_impact": {
                    "vulnerable_assets": ["건물 구조", "설비"],
                    "damage_potential": "Moderate",
                    "narrative": "LLM 분석 실패로 기본 가이드라인 제공. 상세 분석 필요."
                }
            },
            "mitigation_recommendations": {
                "short_term": [
                    {
                        "action": "취약 지점 긴급 점검",
                        "target_risk": "general",
                        "priority": "High",
                        "estimated_cost": "산정 필요"
                    }
                ],
                "mid_term": [
                    {
                        "action": "설비 보강 계획 수립",
                        "target_risk": "general",
                        "priority": "Medium",
                        "estimated_cost": "산정 필요"
                    }
                ],
                "long_term": [
                    {
                        "action": "장기 리스크 저감 전략 수립",
                        "target_risk": "general",
                        "priority": "Medium",
                        "estimated_cost": "산정 필요"
                    }
                ]
            },
            "report_narrative_guide": {
                "recommended_tone": tone,
                "key_message": f"구조등급 {grade} 건물로, 체계적인 리스크 관리 필요",
                "tcfd_alignment": "물리적 리스크 노출에 대한 모니터링 및 대응 전략 수립",
                "stakeholder_focus": "건물 리스크 현황 파악 및 대응 방안 제시"
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

        v08 업데이트: JSON 구조화 출력으로 변경
        - Node 2-B (Impact Analysis): financial_impact, operational_impact, asset_impact 활용
        - Node 2-C (Mitigation Strategies): short_term, mid_term, long_term 대응 방안 활용
        - Node 3 (Strategy Section): vulnerability_summary 활용
        """

        meta = data.get('meta', {})
        physical_specs = data.get('physical_specs', {})
        floor_details = data.get('floor_details', [])
        transition_specs = data.get('transition_specs', {})

        # 건물 정보 요약
        building_age = physical_specs.get('age', {}).get('years', 0)
        structure_type = physical_specs.get('structure', '미상')
        seismic_applied = physical_specs.get('seismic', {}).get('applied', 'Unknown')
        max_underground = physical_specs.get('floors', {}).get('max_underground', 0)
        ground_floors = physical_specs.get('floors', {}).get('ground', 0)

        # 지하층 중요 설비 여부
        basement_critical = any(
            f.get('type') == 'Underground' and f.get('is_potentially_critical')
            for f in floor_details
        )

        prompt = f"""<ROLE>
당신은 TCFD 보고서 생성 전문가입니다. 건축물 데이터를 분석하여
**보고서 생성 노드(Node 2-B, 2-C, 3)가 활용할 구조화된 가이드라인**을 JSON 형식으로 생성합니다.
</ROLE>

<BUILDING_DATA>
## 건물 기본 정보
- 주소: {meta.get('address', '미상')}
- 준공연도: {physical_specs.get('age', {}).get('completion_year', '미상')} (경과년수: {building_age}년)
- 구조: {structure_type}
- 내진설계: {seismic_applied}
- 지상층수: {ground_floors}층, 지하층수: {max_underground}층
- 구조안전등급: {grade}

## 층별 상세 (지하층 중심)
{json.dumps([f for f in floor_details if f.get('type') == 'Underground'], indent=2, ensure_ascii=False) if floor_details else '(지하층 없음)'}

## 에너지/전환 특성
{json.dumps(transition_specs, indent=2, ensure_ascii=False) if transition_specs else '(데이터 없음)'}
</BUILDING_DATA>

<SYSTEM_ANALYSIS>
## 식별된 취약 요인 (시스템 분석)
{self._format_list(vulnerabilities) if vulnerabilities else '(식별된 취약 요인 없음)'}

## 식별된 회복력 요인 (시스템 분석)
{self._format_list(resilience) if resilience else '(식별된 회복력 요인 없음)'}
</SYSTEM_ANALYSIS>

<RISK_CONTEXT>
## 외부 리스크 평가 점수
{self._format_dict(risk_scores) if risk_scores else '(리스크 점수 미제공)'}
</RISK_CONTEXT>

<OUTPUT_REQUIREMENTS>
다음 JSON 형식으로 정확히 출력하세요. 각 필드는 해당 TCFD 보고서 노드에서 직접 활용됩니다.

```json
{{
  "building_summary": {{
    "one_liner": "건물 특성을 1문장으로 요약 (예: '30년 경과 철근콘크리트 건물, 내진설계 미적용')",
    "key_characteristics": [
      "핵심 물리적 특성 1 (예: 준공 30년차 노후 건물)",
      "핵심 물리적 특성 2",
      "핵심 물리적 특성 3"
    ],
    "risk_exposure_level": "High/Medium/Low - 전반적 리스크 노출 수준"
  }},

  "vulnerability_summary": {{
    "high_risk_factors": [
      {{
        "factor": "취약 요인명 (예: 지하 전기실)",
        "related_risks": ["river_flood", "urban_flood"],
        "severity": "Very High/High/Medium",
        "impact_description": "이 요인이 미치는 구체적 영향 (재무/운영/자산 관점)"
      }}
    ],
    "resilience_factors": [
      {{
        "factor": "회복력 요인명 (예: 내진설계 적용)",
        "related_risks": ["typhoon", "earthquake"],
        "strength": "Very High/High/Medium",
        "benefit_description": "이 요인이 제공하는 구체적 이점"
      }}
    ]
  }},

  "impact_analysis_guide": {{
    "financial_impact": {{
      "estimated_exposure": "예상 재무적 노출 수준 (High/Medium/Low)",
      "key_cost_drivers": ["주요 비용 발생 요인 1", "비용 요인 2"],
      "narrative": "재무적 영향에 대해 보고서에 서술할 핵심 내용 (2-3문장)"
    }},
    "operational_impact": {{
      "critical_systems_at_risk": ["위험에 노출된 핵심 시스템/설비"],
      "estimated_downtime": "예상 운영 중단 기간 (예: '최대 7일')",
      "narrative": "운영적 영향에 대해 보고서에 서술할 핵심 내용 (2-3문장)"
    }},
    "asset_impact": {{
      "vulnerable_assets": ["취약한 자산/설비 리스트"],
      "damage_potential": "예상 손상 수준 (Severe/Moderate/Minor)",
      "narrative": "자산 영향에 대해 보고서에 서술할 핵심 내용 (2-3문장)"
    }}
  }},

  "mitigation_recommendations": {{
    "short_term": [
      {{
        "action": "단기 조치 (1년 이내)",
        "target_risk": "대응 대상 리스크 (예: urban_flood)",
        "priority": "High/Medium",
        "estimated_cost": "예상 비용 범위 (예: 5억원~10억원)"
      }}
    ],
    "mid_term": [
      {{
        "action": "중기 조치 (1-5년)",
        "target_risk": "대응 대상 리스크",
        "priority": "High/Medium",
        "estimated_cost": "예상 비용 범위"
      }}
    ],
    "long_term": [
      {{
        "action": "장기 조치 (5년 이상)",
        "target_risk": "대응 대상 리스크",
        "priority": "High/Medium",
        "estimated_cost": "예상 비용 범위"
      }}
    ]
  }},

  "report_narrative_guide": {{
    "recommended_tone": "warning/neutral/positive - 권장 보고서 톤",
    "key_message": "보고서에서 강조해야 할 핵심 메시지 (1문장)",
    "tcfd_alignment": "TCFD 프레임워크 관점에서 강조할 포인트",
    "stakeholder_focus": "투자자/이해관계자에게 전달할 핵심 내용"
  }}
}}
```
</OUTPUT_REQUIREMENTS>

<QUALITY_CHECKLIST>
출력 전 확인사항:
- [ ] 모든 JSON 필드가 채워져 있는가?
- [ ] high_risk_factors의 related_risks가 실제 리스크 타입인가? (river_flood, urban_flood, typhoon, extreme_heat, drought, wildfire, sea_level_rise, extreme_cold, water_stress)
- [ ] impact_analysis_guide의 narrative가 구체적이고 데이터 기반인가?
- [ ] mitigation_recommendations가 실행 가능하고 비용 추정이 현실적인가?
- [ ] 건물 데이터(연식, 구조, 지하층 등)를 근거로 분석했는가?
</QUALITY_CHECKLIST>

JSON 출력만 제공하세요. 추가 설명이나 마크다운 코드블록(```) 없이 순수 JSON만 출력하세요.
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
