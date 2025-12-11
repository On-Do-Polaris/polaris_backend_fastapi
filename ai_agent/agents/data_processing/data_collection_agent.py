'''
파일명: data_collection_agent.py
최종 수정일: 2025-11-24
버전: v03
파일 개요: 기후 데이터 수집 에이전트 (PostgreSQL → Scratch 저장)
변경 이력:
	- 2025-11-11: v01 - Super Agent 구조에 맞게 업데이트, 9개 리스크 대응
	- 2025-11-22: v02 - PostgreSQL 연동 및 Scratch 저장 구현
	- 2025-11-24: v03 - ERD 기반 데이터베이스 스키마 반영
'''
from typing import Dict, Any, Optional
import logging
from ai_agent.utils.database import DatabaseManager
from ai_agent.utils.scratch_manager import ScratchSpaceManager


class DataCollectionAgent:
	"""
	기후 데이터 수집 에이전트
	PostgreSQL에서 데이터를 조회하고 Scratch Space에 TTL 기반으로 저장

	- 기상 데이터 (온도, 강수량, 풍속)
	- 지리 데이터
	- 역사적 기후 데이터
	- SSP 시나리오 데이터
	"""

	def __init__(self, config=None):
		"""
		데이터 수집 에이전트 초기화

		Args:
			config: 설정 객체 (선택)
		"""
		self.config = config or {}
		self.logger = logging.getLogger(__name__)

		# 데이터베이스 및 Scratch Space 초기화
		self.db_manager = DatabaseManager()
		self.scratch_manager = ScratchSpaceManager(
			base_path=self.config.get('scratch_path', './scratch'),
			default_ttl_hours=self.config.get('ttl_hours', 4)
		)

	def collect(
		self,
		target_location: Dict,
		analysis_params: Dict,
		session_id: Optional[str] = None
	) -> Dict[str, Any]:
		"""
		타겟 위치에 대한 모든 필요 데이터 수집 및 Scratch에 저장

		Args:
			target_location: 분석 대상 위치 정보 (latitude, longitude, name)
			analysis_params: 분석 파라미터 (start_year, end_year, ssp_scenarios)
			session_id: Scratch 세션 ID (없으면 자동 생성)

		Returns:
			수집 결과 딕셔너리 (session_id 및 저장된 파일 경로 포함)
		"""
		# 1. Scratch 세션 생성
		if session_id is None:
			session_id = self.scratch_manager.create_session(
				ttl_hours=self.config.get('ttl_hours', 4),
				metadata={
					'location': target_location,
					'analysis_params': analysis_params,
					'agent': 'DataCollectionAgent'
				}
			)

		self.logger.info(f"Starting data collection for session: {session_id}")

		# 2. 기후 데이터 수집
		climate_data = self._collect_climate_data(target_location, analysis_params)
		self.scratch_manager.save_data(session_id, 'climate_data.json', climate_data, format='json')

		# 3. 지리 데이터 수집
		geographic_data = self._collect_geographic_data(target_location)
		self.scratch_manager.save_data(session_id, 'geographic_data.json', geographic_data, format='json')

		# 4. 역사적 재해 사건 수집
		historical_events = self._collect_historical_events(target_location, analysis_params)
		self.scratch_manager.save_data(session_id, 'historical_events.json', historical_events, format='json')

		# 5. SSP 시나리오 데이터 수집
		ssp_data = self._collect_ssp_scenario_data(target_location, analysis_params)
		self.scratch_manager.save_data(session_id, 'ssp_scenarios.json', ssp_data, format='json')

		# 수집 완료
		self.logger.info(f"Data collection completed for session: {session_id}")

		return {
			'status': 'success',
			'session_id': session_id,
			'location': target_location,
			'files': self.scratch_manager.list_files(session_id),
			'message': f'Data collected and saved to scratch space (TTL: {self.config.get("ttl_hours", 4)}h)'
		}

	def _collect_climate_data(self, location: Dict, params: Dict) -> Dict:
		"""
		기후 데이터 수집 (PostgreSQL에서 조회 - ERD v03 Wide Format)

		Args:
			location: 위치 정보 (latitude, longitude, admin_code)
			params: 분석 파라미터 (start_year, end_year, scenario)

		Returns:
			기후 데이터 딕셔너리 (Wide Format: ssp1, ssp2, ssp3, ssp5 columns)
		"""
		latitude = location['latitude']
		longitude = location['longitude']
		admin_code = location.get('admin_code')
		start_year = params.get('start_year', 2000)
		end_year = params.get('end_year', 2023)

		# ERD v03: scenario_id → scenario (string)
		# For backward compatibility, convert scenario_id to scenario string
		scenario_id = params.get('scenario_id')
		scenario = params.get('scenario')

		if scenario_id and not scenario:
			# Convert old scenario_id (1,2,3,5) to new scenario string
			scenario_map = {1: 'ssp1', 2: 'ssp2', 3: 'ssp3', 5: 'ssp5'}
			scenario = scenario_map.get(scenario_id)

		# If scenario is None, fetch all scenarios (Wide format)

		self.logger.info(f"Fetching climate data for ({latitude}, {longitude}) from {start_year} to {end_year}, scenario={scenario or 'all'}")

		# PostgreSQL에서 종합 데이터 조회 (ERD v03 Wide Format)
		all_data = self.db_manager.collect_all_climate_data(
			latitude=latitude,
			longitude=longitude,
			start_year=start_year,
			end_year=end_year,
			scenario=scenario,
			admin_code=admin_code
		)

		return {
			'location': all_data['location'],
			'period': all_data['period'],
			'scenario': all_data['scenario'],  # Changed from scenario_id
			'grid_info': all_data.get('grid'),
			'admin_info': all_data.get('admin'),
			'monthly_data': all_data.get('monthly_data', {}),
			'daily_data': all_data.get('daily_data', {}),
			'yearly_data': all_data.get('yearly_data', {}),
			'sea_level_data': all_data.get('sea_level_data', [])
		}

	def _collect_geographic_data(self, location: Dict) -> Dict:
		"""
		지리 정보 데이터 수집 (PostgreSQL에서 조회)

		Args:
			location: 위치 정보 (latitude, longitude, site_id)

		Returns:
			지리 데이터 딕셔너리
		"""
		latitude = location['latitude']
		longitude = location['longitude']
		site_id = location.get('site_id')

		self.logger.info(f"Fetching geographic data for ({latitude}, {longitude})")

		result = {
			'location': location
		}

		# Spatial Cache에서 토지피복 분석 데이터 조회
		if site_id:
			landcover = self.db_manager.fetch_spatial_landcover(site_id)
			if landcover:
				result['landcover_analysis'] = landcover

			# DEM 분석 데이터 조회
			dem = self.db_manager.fetch_spatial_dem(site_id)
			if dem:
				result['dem_analysis'] = dem

		# 주변 인프라 정보 조회
		result['nearby_hospitals'] = self.db_manager.fetch_nearby_hospitals(
			latitude, longitude, radius_km=5.0
		)

		# 행정구역 정보
		admin_code = location.get('admin_code')
		if admin_code:
			result['shelters'] = self.db_manager.fetch_nearby_shelters(admin_code)

		return result

	def _collect_historical_events(self, location: Dict, params: Dict) -> Dict:
		"""
		역사적 재해 사건 데이터 수집 (PostgreSQL에서 조회)

		Args:
			location: 위치 정보
			params: 분석 파라미터

		Returns:
			역사적 재해 데이터 딕셔너리
		"""
		latitude = location['latitude']
		longitude = location['longitude']
		start_year = params.get('start_year', 2000)
		end_year = params.get('end_year', 2023)
		radius_km = params.get('search_radius_km', 100)

		self.logger.info(f"Fetching historical typhoon events within {radius_km}km of ({latitude}, {longitude})")

		# PostgreSQL에서 태풍 이력 조회 (ERD 기반)
		typhoon_events = self.db_manager.fetch_typhoon_history(
			latitude=latitude,
			longitude=longitude,
			radius_km=radius_km,
			start_year=start_year,
			end_year=end_year
		)

		return {
			'location': location,
			'search_radius_km': radius_km,
			'period': {'start_year': start_year, 'end_year': end_year},
			'total_typhoon_events': len(typhoon_events),
			'typhoon_events': typhoon_events
		}

	def _collect_ssp_scenario_data(self, location: Dict, params: Dict) -> Dict:
		"""
		SSP 시나리오 데이터 수집 (PostgreSQL에서 조회)

		Args:
			location: 위치 정보
			params: 분석 파라미터

		Returns:
			SSP 시나리오 데이터 딕셔너리
		"""
		latitude = location['latitude']
		longitude = location['longitude']
		admin_code = location.get('admin_code')
		start_year = params.get('future_start_year', 2025)
		end_year = params.get('future_end_year', 2100)
		scenario_ids = params.get('scenario_ids', [1, 2, 3, 4])  # 1=SSP1-2.6, 2=SSP2-4.5, 3=SSP3-7.0, 4=SSP5-8.5

		self.logger.info(f"Fetching SSP scenario data for ({latitude}, {longitude})")

		# 각 시나리오별 데이터 조회 (ERD 기반)
		ssp_data = {}

		for scenario_id in scenario_ids:
			scenario_name = f"SSP{scenario_id}"

			# 종합 기후 데이터 수집 (각 시나리오별)
			scenario_data = self.db_manager.collect_all_climate_data(
				latitude=latitude,
				longitude=longitude,
				start_year=start_year,
				end_year=end_year,
				scenario_id=scenario_id,
				admin_code=admin_code
			)

			ssp_data[scenario_name] = scenario_data

		return {
			'location': location,
			'period': {'start_year': start_year, 'end_year': end_year},
			'scenarios': ssp_data
		}
