"""
파일명: modelops_client.py
최종 수정일: 2025-12-11
버전: v03
파일 개요: ModelOps API 호출 클라이언트 (Site Assessment API)

역할:
	- ModelOps FastAPI 서버와 통신
	- 사업장 리스크 계산 (H×E×V×AAL)
	- 이전 후보지 추천 (~1000개 격자 평가)
	- Health check 엔드포인트 지원

변경사항 (v03):
	- API 엔드포인트 변경: /api/v1/risk-assessment/* → /api/site-assessment/*
	- WebSocket 지원 제거 (동기 API로 변경)
	- status 폴링 제거 (동기 계산으로 변경)
	- cached results 조회 제거
	- 사업장 이전 후보지 추천 API 추가
"""

import httpx
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ModelOpsClient:
	"""
	ModelOps API 클라이언트 (Site Assessment)

	역할:
	- 사업장 리스크 계산 (H×E×V×AAL)
	- 이전 후보지 추천 (~1000개 격자 평가)
	- Health check 및 재시도 로직
	"""

	def __init__(
		self,
		base_url: Optional[str] = None,
		api_key: Optional[str] = None,
		timeout: float = 300.0,
		max_retries: int = 3
	):
		"""
		ModelOpsClient 초기화

		Args:
			base_url: ModelOps API Base URL (None인 경우 환경변수 MODELOPS_URL 사용)
			api_key: API 인증 키 (선택)
			timeout: 요청 타임아웃 (초) - 기본 300초 (후보지 추천은 시간이 오래 걸림)
			max_retries: 최대 재시도 횟수
		"""
		import os

		# 환경변수에서 URL 로드 (base_url이 None인 경우)
		if base_url is None:
			base_url = os.getenv('MODELOPS_URL', 'http://localhost:8001')

		self.base_url = base_url.rstrip('/')
		self.api_key = api_key
		self.timeout = timeout
		self.max_retries = max_retries
		self.logger = logger

		# HTTP 클라이언트 설정
		headers = {}
		if api_key:
			headers['Authorization'] = f'Bearer {api_key}'

		self.client = httpx.Client(
			base_url=self.base_url,
			headers=headers,
			timeout=self.timeout
		)

		self.logger.info(f"ModelOpsClient 초기화: {self.base_url}")

	def __del__(self):
		"""리소스 정리"""
		if hasattr(self, 'client'):
			self.client.close()

	def calculate_site_risk(
		self,
		sites: Dict[str, Dict[str, float]],
		building_info: Optional[Dict[str, Any]] = None,
		asset_info: Optional[Dict[str, Any]] = None
	) -> Dict[str, Any]:
		"""
		사업장 리스크 계산 요청 (다중 사업장 병렬 처리)

		Args:
			sites: 사업장 위치 정보 딕셔너리 (필수)
				{
					"site_01": {"latitude": 37.5665, "longitude": 126.9780},
					"site_02": {"latitude": 35.1796, "longitude": 129.0756},
					...
				}
			building_info: 건물 정보 (선택)
				{
					"building_type": "office",
					"structure": "철근콘크리트",
					"building_age": 15,
					"total_area_m2": 2500,
					"ground_floors": 5,
					"basement_floors": 1,
					"has_piloti": false,
					"elevation_m": 10
				}
			asset_info: 자산 정보 (선택)
				{
					"total_value": 50000000000,  # 총 자산 가치 (원)
					"insurance_coverage_rate": 0.3  # 보험 커버리지 비율 (0~1)
				}

		Returns:
			{
				"status": "success" | "partial" | "failed",
				"total_sites": int,
				"successful_sites": int,
				"failed_sites": int,
				"message": str,
				"calculated_at": str  # ISO 8601 형식
			}
		"""
		self.logger.info(f"사업장 리스크 계산 요청: {len(sites)}개 사업장")

		# 유효성 검증
		if not sites or len(sites) == 0:
			raise ValueError("sites dictionary is required and must not be empty")

		# sites의 각 위치에 대한 유효성 검증
		for site_id, location in sites.items():
			lat = location.get('latitude')
			lon = location.get('longitude')
			if not lat or not lon:
				raise ValueError(f"Invalid location for site {site_id}: latitude and longitude are required")
			if not (-90 <= lat <= 90):
				raise ValueError(f"Invalid latitude for site {site_id}: {lat}. Must be between -90 and 90.")
			if not (-180 <= lon <= 180):
				raise ValueError(f"Invalid longitude for site {site_id}: {lon}. Must be between -180 and 180.")

		payload = {
			"sites": sites
		}

		if building_info:
			payload["building_info"] = building_info
		if asset_info:
			payload["asset_info"] = asset_info

		try:
			response = self.client.post("/api/site-assessment/calculate", json=payload)
			response.raise_for_status()

			result = response.json()
			status = result.get('status', 'unknown')
			successful = result.get('successful_sites', 0)
			failed = result.get('failed_sites', 0)
			self.logger.info(f"사업장 리스크 계산 완료: status={status}, successful={successful}, failed={failed}")

			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"사업장 리스크 계산 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"사업장 리스크 계산 중 오류: {str(e)}")
			raise

	def recommend_relocation_sites(
		self,
		sites: Dict[str, Dict[str, float]],
		candidate_grids: Optional[List[Dict[str, float]]] = None,
		building_info: Optional[Dict[str, Any]] = None,
		batch_id: Optional[str] = None,
		asset_info: Optional[Dict[str, Any]] = None,
		max_candidates: int = 3,
		ssp_scenario: str = "SSP245",
		target_year: int = 2040
	) -> Dict[str, Any]:
		"""
		사업장 이전 후보지 추천 요청 (다중 사업장 병렬 처리)

		Args:
			sites: 사업장 위치 정보 딕셔너리 (필수)
				{
					"site_01": {"latitude": 37.5665, "longitude": 126.9780},
					"site_02": {"latitude": 35.1796, "longitude": 129.0756},
					...
				}
			candidate_grids: 후보지 격자 목록 (선택, 없으면 고정 위치 사용)
				[
					{"latitude": 37.5665, "longitude": 126.9780},
					{"latitude": 37.5666, "longitude": 126.9781},
					...
				]
			building_info: 건물 정보 (선택)
			batch_id: 배치 작업 ID (선택, ModelOps 콜백용)
			asset_info: 자산 정보 (선택)
			max_candidates: 최대 추천 후보지 개수 (기본: 3)
			ssp_scenario: SSP 시나리오 (기본: "SSP245")
			target_year: 목표 연도 (기본: 2040)

		Returns:
			{
				"status": "success" | "failed",
				"message": str
			}
		"""
		self.logger.info(f"이전 후보지 추천 요청: {len(sites)}개 사업장, batch_id={batch_id}")

		# 유효성 검증
		if not sites or len(sites) == 0:
			raise ValueError("sites dictionary is required and must not be empty")

		payload = {
			"sites": sites,
			"search_criteria": {
				"max_candidates": max_candidates,
				"ssp_scenario": ssp_scenario,
				"target_year": target_year
			}
		}

		if candidate_grids:
			payload["candidate_grids"] = candidate_grids
		if building_info:
			payload["building_info"] = building_info
		if batch_id:
			payload["batch_id"] = batch_id
		if asset_info:
			payload["asset_info"] = asset_info

		try:
			response = self.client.post("/api/site-assessment/recommend-locations", json=payload)
			response.raise_for_status()

			result = response.json()
			status = result.get('status', 'unknown')
			self.logger.info(f"이전 후보지 추천 완료: status={status}")

			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"이전 후보지 추천 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"이전 후보지 추천 중 오류: {str(e)}")
			raise

	def health_check(self) -> Dict[str, Any]:
		"""
		ModelOps 서버 상태 확인

		Returns:
			{
				"status": str,
				"service": str,
				"timestamp": str
			}
		"""
		self.logger.debug("Health check 요청")

		try:
			response = self.client.get("/health")
			response.raise_for_status()

			result = response.json()
			self.logger.debug(f"Health check 완료: status={result.get('status')}")

			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"Health check 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"Health check 중 오류: {str(e)}")
			raise

	def database_health(self) -> Dict[str, Any]:
		"""
		ModelOps 데이터베이스 연결 확인

		Returns:
			{
				"status": str,
				"database": str,
				"timestamp": str
			}
		"""
		self.logger.debug("Database health check 요청")

		try:
			response = self.client.get("/health/db")
			response.raise_for_status()

			result = response.json()
			self.logger.debug(f"Database health check 완료: status={result.get('status')}")

			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"Database health check 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"Database health check 중 오류: {str(e)}")
			raise


# 싱글톤 인스턴스
_modelops_client: Optional[ModelOpsClient] = None


def get_modelops_client() -> ModelOpsClient:
	"""
	ModelOpsClient 싱글톤 인스턴스 반환

	Returns:
		ModelOpsClient 인스턴스
	"""
	global _modelops_client

	if _modelops_client is None:
		# 환경 변수에서 설정 로드
		import os
		base_url = os.getenv('MODELOPS_URL', 'http://localhost:8001')
		api_key = os.getenv('MODELOPS_API_KEY')

		_modelops_client = ModelOpsClient(
			base_url=base_url,
			api_key=api_key,
			timeout=300.0,  # 후보지 추천은 시간이 오래 걸릴 수 있음
			max_retries=3
		)

	return _modelops_client
