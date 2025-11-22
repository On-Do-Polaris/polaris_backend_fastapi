'''
파일명: hazard_batch.py
최종 수정일: 2025-11-22
버전: v01
파일 개요: Hazard Score(H) 배치 계산 워크플로우
	- 전체 격자 좌표에 대해 연 1회 H 점수 계산
	- 결과를 데이터베이스 또는 파일 시스템에 저장
변경 이력:
	- 2025-11-22: v01 - 초기 생성
'''

from typing import List, Dict, Any
import logging
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

from ..agents.aiops.hazard_calculate import (
	CoastalFloodHScoreAgent,
	ColdWaveHScoreAgent,
	DroughtHScoreAgent,
	HighTemperatureHScoreAgent,
	InlandFloodHScoreAgent,
	TyphoonHScoreAgent,
	UrbanFloodHScoreAgent,
	WaterScarcityHScoreAgent,
	WildfireHScoreAgent
)

logger = logging.getLogger(__name__)


class HazardBatchProcessor:
	"""
	Hazard Score(H) 배치 계산 프로세서
	전체 격자 좌표에 대해 9개 리스크의 위험 점수 계산
	"""

	def __init__(self, config: Dict[str, Any]):
		"""
		Args:
			config: 설정 딕셔너리
				- db_config: 데이터베이스 설정
				- storage_config: 저장소 설정
				- parallel_workers: 병렬 처리 워커 수
		"""
		self.config = config
		self.db_config = config.get('db_config', {})
		self.storage_config = config.get('storage_config', {})
		self.parallel_workers = config.get('parallel_workers', 4)

		# 9개 리스크 에이전트 초기화
		self.agents = {
			'coastal_flood': CoastalFloodHScoreAgent(),
			'cold_wave': ColdWaveHScoreAgent(),
			'drought': DroughtHScoreAgent(),
			'high_temperature': HighTemperatureHScoreAgent(),
			'inland_flood': InlandFloodHScoreAgent(),
			'typhoon': TyphoonHScoreAgent(),
			'urban_flood': UrbanFloodHScoreAgent(),
			'water_scarcity': WaterScarcityHScoreAgent(),
			'wildfire': WildfireHScoreAgent()
		}

		logger.info(f"HazardBatchProcessor initialized with {self.parallel_workers} workers")


	def process_all_grids(self, grid_coordinates: List[Dict[str, float]]) -> Dict[str, Any]:
		"""
		전체 격자 좌표에 대해 Hazard Score 계산

		Args:
			grid_coordinates: 격자 좌표 리스트
				예: [{'lat': 37.5665, 'lon': 126.9780}, ...]

		Returns:
			배치 처리 결과
				- total_grids: 총 격자 수
				- processed: 처리 완료 격자 수
				- failed: 실패 격자 수
				- start_time: 시작 시간
				- end_time: 종료 시간
				- results: 격자별 결과 (선택적)
		"""
		start_time = datetime.now()
		logger.info(f"Starting hazard score batch processing for {len(grid_coordinates)} grids")

		results = []
		failed_count = 0

		# 병렬 처리
		with ProcessPoolExecutor(max_workers=self.parallel_workers) as executor:
			futures = {
				executor.submit(self._process_single_grid, coord): coord
				for coord in grid_coordinates
			}

			for future in as_completed(futures):
				coord = futures[future]
				try:
					result = future.result()
					results.append(result)

					if result['status'] == 'success':
						logger.info(f"Grid ({coord['lat']}, {coord['lon']}) processed successfully")
					else:
						failed_count += 1
						logger.error(f"Grid ({coord['lat']}, {coord['lon']}) failed: {result.get('error')}")

				except Exception as e:
					failed_count += 1
					logger.error(f"Grid ({coord['lat']}, {coord['lon']}) exception: {str(e)}")

		end_time = datetime.now()
		duration = (end_time - start_time).total_seconds()

		summary = {
			'total_grids': len(grid_coordinates),
			'processed': len(results) - failed_count,
			'failed': failed_count,
			'start_time': start_time.isoformat(),
			'end_time': end_time.isoformat(),
			'duration_seconds': duration,
			'results': results if self.config.get('include_results', False) else None
		}

		logger.info(f"Hazard batch processing completed: {summary['processed']}/{summary['total_grids']} grids in {duration:.2f}s")

		return summary


	def _process_single_grid(self, coordinate: Dict[str, float]) -> Dict[str, Any]:
		"""
		단일 격자 좌표에 대해 9개 리스크의 Hazard Score 계산

		Args:
			coordinate: 격자 좌표 {'lat': float, 'lon': float}

		Returns:
			격자 처리 결과
		"""
		lat = coordinate['lat']
		lon = coordinate['lon']

		try:
			# 1. 해당 격자의 기후 데이터 수집 (데이터베이스 또는 API에서)
			collected_data = self._fetch_climate_data(lat, lon)

			# 2. 9개 리스크별 Hazard Score 계산
			hazard_scores = {}

			for risk_type, agent in self.agents.items():
				try:
					result = agent.calculate_hazard_score(collected_data)

					if result.get('status') == 'completed':
						hazard_scores[risk_type] = {
							'hazard_score': result['hazard_score'],
							'hazard_score_100': result['hazard_score_100'],
							'hazard_level': result['hazard_level']
						}
					else:
						logger.error(f"Risk {risk_type} failed for grid ({lat}, {lon}): {result.get('error')}")
						hazard_scores[risk_type] = None

				except Exception as e:
					logger.error(f"Risk {risk_type} exception for grid ({lat}, {lon}): {str(e)}")
					hazard_scores[risk_type] = None

			# 3. 결과 저장 (데이터베이스 또는 파일)
			self._save_results(lat, lon, hazard_scores)

			return {
				'status': 'success',
				'coordinate': coordinate,
				'timestamp': datetime.now().isoformat(),
				'risks_calculated': len([v for v in hazard_scores.values() if v is not None])
			}

		except Exception as e:
			return {
				'status': 'failed',
				'coordinate': coordinate,
				'error': str(e),
				'timestamp': datetime.now().isoformat()
			}


	def _fetch_climate_data(self, lat: float, lon: float) -> Dict[str, Any]:
		"""
		특정 격자 좌표의 기후 데이터 수집

		Args:
			lat: 위도
			lon: 경도

		Returns:
			수집된 기후 데이터

		TODO: 실제 데이터베이스 또는 API 연동 구현
		"""
		# 임시 구현 - 실제로는 데이터베이스에서 조회
		logger.debug(f"Fetching climate data for ({lat}, {lon})")

		return {
			'location': {'lat': lat, 'lon': lon},
			'climate_data': {
				# 실제 데이터 구조에 맞게 수정 필요
				'wsdi': [],  # Warm Spell Duration Index
				'csdi': [],  # Cold Spell Duration Index
				'temperature': [],
				'precipitation': [],
				'wind_speed': [],
				'sea_level': [],
				'drought_index': [],
				# ... 기타 기후 변수
			}
		}


	def _save_results(self, lat: float, lon: float, hazard_scores: Dict[str, Any]) -> None:
		"""
		계산 결과 저장

		Args:
			lat: 위도
			lon: 경도
			hazard_scores: 9개 리스크별 Hazard Score

		TODO: 실제 데이터베이스 또는 파일 저장 구현
		"""
		logger.debug(f"Saving hazard scores for grid ({lat}, {lon})")

		# 저장 방식 1: 데이터베이스
		if self.storage_config.get('type') == 'database':
			# DB 저장 로직 구현
			# 예: INSERT INTO hazard_scores (lat, lon, risk_type, hazard_score, hazard_level, updated_at)
			#     VALUES (lat, lon, 'coastal_flood', 0.65, 'High', NOW())
			pass

		# 저장 방식 2: 파일 시스템 (JSON, Parquet 등)
		elif self.storage_config.get('type') == 'file':
			# 파일 저장 로직 구현
			# 예: hazard_scores/{year}/lat_{lat}_lon_{lon}.json
			pass

		# 저장 방식 3: 클라우드 스토리지 (S3, GCS 등)
		elif self.storage_config.get('type') == 'cloud':
			# 클라우드 저장 로직 구현
			pass


	def calculate_aggregate_statistics(self, grid_coordinates: List[Dict[str, float]]) -> Dict[str, Any]:
		"""
		전체 격자에 대한 집계 통계 계산

		Args:
			grid_coordinates: 격자 좌표 리스트

		Returns:
			집계 통계
				- risk_type별 평균 Hazard Score
				- risk_type별 최대/최소 Hazard Score
				- 위험 등급별 격자 수
		"""
		logger.info("Calculating aggregate statistics...")

		# TODO: 실제 구현 시 DB에서 집계 쿼리 사용
		# 예: SELECT risk_type, AVG(hazard_score), MAX(hazard_score), MIN(hazard_score)
		#     FROM hazard_scores
		#     GROUP BY risk_type

		statistics = {
			'total_grids': len(grid_coordinates),
			'by_risk_type': {},
			'timestamp': datetime.now().isoformat()
		}

		return statistics
