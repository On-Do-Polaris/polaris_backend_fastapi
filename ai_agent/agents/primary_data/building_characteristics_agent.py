'''
파일명: building_characteristics_agent.py
작성일: 2025-12-15
버전: v06 (TCFD Report v2.1 - Parallel Processing)
파일 개요: 건축물 대장 기반 물리적 취약성 정밀 분석 에이전트 (보고서 생성용 가이드라인 제공)

역할:
    - BuildingDataFetcher를 통해 실시간 건축물 정보 및 지리 정보 수집
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
'''

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json # for pretty printing data to LLM
import asyncio

# BuildingDataFetcher 임포트
try:
    from ...utils.building_data_fetcher import BuildingDataFetcher
except ImportError:
    BuildingDataFetcher = None
    print("⚠️ BuildingDataFetcher를 임포트할 수 없습니다.")

logger = logging.getLogger(__name__)


class BuildingCharacteristicsAgent:
    """
    건축물 물리적 특성 분석 에이전트 (TCFD 보고서 생성용)
    → 보고서 생성 에이전트에 참고할 만한 가이드라인을 제공
    → v05: 다중 사업장 배치 처리 지원 (TCFD Report v2.1)
    """

    def __init__(self, llm_client=None):
        """
        초기화
        :param llm_client: LLM 클라이언트 인스턴스 (텍스트 생성용)
        """
        self.logger = logger
        self.llm_client = llm_client

        if BuildingDataFetcher:
            try:
                self.fetcher = BuildingDataFetcher()
                self.logger.info("BuildingDataFetcher 초기화 성공")
            except Exception as e:
                self.logger.error(f"BuildingDataFetcher 초기화 실패: {e}")
                self.fetcher = None
        else:
            self.fetcher = None

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
        """BuildingDataFetcher를 통한 TCFD 데이터 조회"""
        if not self.fetcher:
            self.logger.warning("Fetcher 없음, 빈 데이터 반환")
            return {}

        try:
            # fetch_full_tcfd_data는 에러를 내부적으로 처리하고 Fallback 값을 반환함
            data = self.fetcher.fetch_full_tcfd_data(lat, lon, address)
            return data
        except Exception as e:
            self.logger.error(f"TCFD 데이터 조회 중 오류: {e}")
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
    ) -> str:
        """LLM을 활용한 보고서 생성 가이드라인 생성 (비동기)"""

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

                return response
            except Exception as e:
                self.logger.error(f"LLM 가이드라인 생성 실패: {e}")
                return self._generate_fallback_guidelines(data, vulnerabilities, resilience, grade)

        return self._generate_fallback_guidelines(data, vulnerabilities, resilience, grade)


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
        """LLM 프롬프트 구성 (보고서 생성 에이전트를 위한 가이드라인 생성용)"""

        meta = data.get('meta', {})
        physical_specs = data.get('physical_specs', {})
        floor_details = data.get('floor_details', [])
        transition_specs = data.get('transition_specs', {})

        prompt = f"""당신은 TCFD 보고서 생성 전문가이며, **보고서 생성 에이전트를 위한 가이드라인**을 작성하는 역할을 맡고 있습니다.

제공된 건축물 대장 데이터를 바탕으로 **보고서 생성 시 활용할 핵심 정보와 서술 방향**을 정리해주세요.

⚠️ **중요**: 당신은 최종 보고서를 직접 작성하는 것이 아니라, 다른 AI 에이전트가 보고서를 작성할 때 참고할 **가이드라인**을 제공하는 것입니다.

---
## 분석 대상 건물 상세 데이터 (Raw Data)

### 1. 메타 정보
{json.dumps(meta, indent=2, ensure_ascii=False)}

### 2. 물리적 특성 (Physical Specifications)
{json.dumps(physical_specs, indent=2, ensure_ascii=False)}

### 3. 층별 상세 정보 (Floor Details) - ⭐ 핵심 분석 대상
* `usage_main`(주용도) 및 `usage_etc`(기타용도) 텍스트를 꼼꼼히 분석하여 침수 시 위험 요소(전기실, 기계실, 방재실, 발전기 등)를 식별하세요.
* `is_potentially_critical` 플래그는 참고용 힌트일 뿐이며, 텍스트의 문맥을 고려하여 최종 판단하세요.
{json.dumps(floor_details, indent=2, ensure_ascii=False)}

### 4. 전환 특성 (Transition Specifications)
{json.dumps(transition_specs, indent=2, ensure_ascii=False)}

---
## 시스템 분석 결과 (건축물 대장 기반)

### 1. 식별된 주요 취약 요인
{self._format_list(vulnerabilities)}

### 2. 식별된 주요 회복력 요인
{self._format_list(resilience)}

### 3. 자체 평가 구조 안전 등급
- 등급: {grade}

"""

        if risk_scores:
            prompt += f"""
### 4. 외부 리스크 평가 점수
{self._format_dict(risk_scores)}

"""

        prompt += """
---
## 가이드라인 작성 지침

위의 상세 데이터를 면밀히 검토하고, 시스템 분석 결과(취약/회복 요인, 등급)를 참고하여 다음 목차에 따라 **보고서 생성 에이전트를 위한 가이드라인**을 작성하세요.

**핵심**: 이 가이드라인은 추후 Node 2-A (Scenario Analysis), Node 2-B (Impact Analysis), Node 2-C (Mitigation Strategies), Node 3 (Strategy Section) 에이전트가 참고합니다.

**[가이드라인 목차]**
1. **건물 구조적 특징 요약** (Strategy 섹션에서 활용)
   - 건물의 핵심 물리적 특성을 3-5개 항목으로 정리 (연식, 구조, 규모, 내진 설계 여부 등)
   - 각 특성이 물리적 리스크에 미치는 영향을 간결하게 설명

2. **주요 취약점** (P1~P5 영향 분석 섹션에서 강조할 부분)
   - 침수 리스크 관련: 지하층 존재, 지하 중요 설비(기계실/전기실) 등
   - 구조적 리스크 관련: 노후도, 내진 설계 미적용, 필로티 구조 추정 등
   - 각 취약점이 어떤 리스크 항목(침수, 지진 등)과 연관되는지 명시

3. **회복력 요인** (대응 방안 섹션에서 활용)
   - 건물이 보유한 강점 (신축, 내진 설계, 저수조, 에너지 효율 등)
   - 이러한 강점을 활용하여 어떤 대응 전략을 수립할 수 있는지 제안

4. **권장 서술 방향** (보고서 톤 & 스타일)
   - 이 건물에 대한 보고서를 작성할 때 어떤 톤(낙관적/경고적/중립적)을 취해야 하는지
   - 강조해야 할 핵심 메시지 (예: "노후화 심각, 조속한 보강 필요" vs "신축 건물로 리스크 낮음")
   - TCFD 보고서의 목적(재무적 중요성, 투자자 신뢰 확보)에 맞는 서술 방향 제시

**톤앤매너**: 간결하고 실용적인 어조로, 보고서 생성 에이전트가 바로 활용할 수 있도록 구체적으로 작성하세요.
**주의**: 최종 보고서 내용을 직접 작성하지 마세요. 가이드라인과 핵심 포인트만 제공하세요.
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
