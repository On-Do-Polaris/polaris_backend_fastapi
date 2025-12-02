'''
파일명: data_collection_agent.py
최종 수정일: 2025-11-22
버전: v02
파일 개요: 기후 데이터 수집 에이전트 (PostgreSQL → Scratch 저장)
변경 이력:
	- 2025-11-11: v01 - Super Agent 구조에 맞게 업데이트, 9개 리스크 대응
	- 2025-11-22: v02 - PostgreSQL 연동 및 Scratch 저장 구현
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
		기후 데이터 수집 (PostgreSQL에서 조회)

		Args:
			location: 위치 정보 (latitude, longitude)
			params: 분석 파라미터 (start_year, end_year)

		Returns:
			기후 데이터 딕셔너리
		"""
		latitude = location['latitude']
		longitude = location['longitude']
		start_year = params.get('start_year', 2000)
		end_year = params.get('end_year', 2023)

		self.logger.info(f"Fetching climate data for ({latitude}, {longitude}) from {start_year} to {end_year}")

		# PostgreSQL에서 데이터 조회
		climate_data = self.db_manager.fetch_climate_data(
			latitude=latitude,
			longitude=longitude,
			start_year=start_year,
			end_year=end_year
		)

		# 데이터 분류 및 가공
		temperature_data = self._extract_temperature_data(climate_data['records'])
		precipitation_data = self._extract_precipitation_data(climate_data['records'])
		sea_level_data = self._extract_sea_level_data(climate_data['records'])
		wind_data = self._extract_wind_data(climate_data['records'])

		return {
			'location': climate_data['location'],
			'period': climate_data['period'],
			'total_records': climate_data['total_records'],
			'temperature_data': temperature_data,
			'precipitation_data': precipitation_data,
			'sea_level_data': sea_level_data,
			'wind_data': wind_data
		}

	def _extract_temperature_data(self, records: list) -> Dict:
		"""기온 데이터 추출"""
		return {
			'daily_max_temp': [r.get('temperature_max') for r in records],
			'daily_min_temp': [r.get('temperature_min') for r in records],
			'daily_avg_temp': [r.get('temperature_avg') for r in records],
			'dates': [r.get('date') for r in records]
		}

	def _extract_precipitation_data(self, records: list) -> Dict:
		"""강수량 데이터 추출"""
		return {
			'daily_precipitation': [r.get('precipitation_daily') for r in records],
			'monthly_precipitation': [r.get('precipitation_monthly') for r in records],
			'dates': [r.get('date') for r in records]
		}

	def _extract_sea_level_data(self, records: list) -> Dict:
		"""해수면 데이터 추출"""
		return {
			'sea_level': [r.get('sea_level') for r in records if r.get('sea_level')],
			'dates': [r.get('date') for r in records if r.get('sea_level')]
		}

	def _extract_wind_data(self, records: list) -> Dict:
		"""풍속 데이터 추출"""
		return {
			'wind_speed': [r.get('wind_speed') for r in records if r.get('wind_speed')],
			'dates': [r.get('date') for r in records if r.get('wind_speed')]
		}

	def _collect_geographic_data(self, location: Dict) -> Dict:
		"""
		지리 정보 데이터 수집 (PostgreSQL에서 조회)

		Args:
			location: 위치 정보

		Returns:
			지리 데이터 딕셔너리
		"""
		latitude = location['latitude']
		longitude = location['longitude']

		self.logger.info(f"Fetching geographic data for ({latitude}, {longitude})")

		# PostgreSQL에서 지리 데이터 조회
		geo_data = self.db_manager.fetch_geographic_data(
			latitude=latitude,
			longitude=longitude
		)

		return {
			'location': location,
			'elevation': geo_data.get('elevation'),
			'slope': geo_data.get('slope'),
			'land_cover': geo_data.get('land_cover'),
			'vegetation_index': geo_data.get('vegetation_index'),
			'proximity_to_water': geo_data.get('proximity_to_water'),
			'soil_type': geo_data.get('soil_type'),
			'drainage_class': geo_data.get('drainage_class')
		}

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
		radius_km = params.get('search_radius_km', 50)

		self.logger.info(f"Fetching historical events within {radius_km}km of ({latitude}, {longitude})")

		# PostgreSQL에서 역사적 재해 사건 조회
		events = self.db_manager.fetch_historical_events(
			latitude=latitude,
			longitude=longitude,
			radius_km=radius_km,
			start_year=start_year,
			end_year=end_year
		)

		# 이벤트 타입별 분류
		events_by_type = {
			'heatwaves': [],
			'coldwaves': [],
			'droughts': [],
			'floods': [],
			'wildfires': [],
			'typhoons': [],
			'other': []
		}

		for event in events:
			event_type = event.get('event_type', 'other')
			if event_type in events_by_type:
				events_by_type[event_type].append(event)
			else:
				events_by_type['other'].append(event)

		return {
			'location': location,
			'search_radius_km': radius_km,
			'period': {'start_year': start_year, 'end_year': end_year},
			'total_events': len(events),
			'events_by_type': events_by_type,
			'all_events': events
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
		start_year = params.get('future_start_year', 2025)
		end_year = params.get('future_end_year', 2100)
		scenarios = params.get('ssp_scenarios', ['ssp1-2.6', 'ssp2-4.5', 'ssp3-7.0', 'ssp5-8.5'])

		self.logger.info(f"Fetching SSP scenario data for ({latitude}, {longitude})")

		# 각 시나리오별 데이터 조회
		ssp_data = {}

		for scenario in scenarios:
			scenario_data = self.db_manager.fetch_ssp_scenario_data(
				latitude=latitude,
				longitude=longitude,
				scenario=scenario,
				start_year=start_year,
				end_year=end_year
			)
			ssp_data[scenario] = scenario_data

		return {
			'location': location,
			'period': {'start_year': start_year, 'end_year': end_year},
			'scenarios': ssp_data
		}
