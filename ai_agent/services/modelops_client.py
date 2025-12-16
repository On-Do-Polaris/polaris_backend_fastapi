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
		latitude: float,
		longitude: float,
		building_info: Dict[str, Any],
		site_ids: Optional[List[str]] = None,
		asset_info: Optional[Dict[str, Any]] = None
	) -> Dict[str, Any]:
		"""
		사업장 리스크 계산 요청 (H×E×V×AAL 통합 계산)

		Args:
			latitude: 위도 (-90 ~ 90)
			longitude: 경도 (-180 ~ 180)
			building_info: 건물 정보 (필수)
				{
					"building_type": "office",  # office, factory, warehouse, etc.
					"structure": "철근콘크리트",  # 철근콘크리트, 철골, 목조, etc.
					"building_age": 15,  # 건물 연식 (년)
					"total_area_m2": 2500,  # 전체 면적 (m2)
					"ground_floors": 5,  # 지상 층수
					"basement_floors": 1,  # 지하 층수
					"has_piloti": false,  # 필로티 구조 여부
					"elevation_m": 10  # 지면 고도 (m)
				}
			site_ids: 사업장 ID 리스트 (선택)
			asset_info: 자산 정보 (선택)
				{
					"total_value": 50000000000,  # 총 자산 가치 (원)
					"insurance_coverage_rate": 0.3  # 보험 커버리지 비율 (0~1)
				}

		Returns:
			{
				"site_id": str,
				"latitude": float,
				"longitude": float,
				"hazard": {risk_type: {...}, ...},  # 9개 리스크별 H 점수
				"exposure": {risk_type: {...}, ...},  # 9개 리스크별 E 점수
				"vulnerability": {risk_type: {...}, ...},  # 9개 리스크별 V 점수
				"integrated_risk": {risk_type: {...}, ...},  # H×E×V/10000
				"aal_scaled": {risk_type: {...}, ...},  # 최종 AAL
				"summary": {
					"total_integrated_risk": float,  # 9개 리스크 합산
					"total_final_aal": float,  # 9개 AAL 합산
					"risk_count": int  # 평가된 리스크 개수
				},
				"calculated_at": str  # ISO 8601 형식
			}
		"""
		self.logger.info(f"사업장 리스크 계산 요청: lat={latitude}, lng={longitude}, site_ids={site_ids}")

		# 유효성 검증
		if not (-90 <= latitude <= 90):
			raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90.")
		if not (-180 <= longitude <= 180):
			raise ValueError(f"Invalid longitude: {longitude}. Must be between -180 and 180.")
		if not building_info:
			raise ValueError("building_info is required")

		payload = {
			"latitude": latitude,
			"longitude": longitude,
			"building_info": building_info
		}

		if site_ids:
			payload["site_ids"] = site_ids
		if asset_info:
			payload["asset_info"] = asset_info

		try:
			response = self.client.post("/api/site-assessment/calculate", json=payload)
			response.raise_for_status()

			result = response.json()
			total_aal = result.get('summary', {}).get('total_final_aal', 0)
			self.logger.info(f"사업장 리스크 계산 완료: total_aal={total_aal:.6f}")

			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"사업장 리스크 계산 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"사업장 리스크 계산 중 오류: {str(e)}")
			raise

	def recommend_relocation_sites(
		self,
		candidate_grids: List[Dict[str, float]],
		building_info: Dict[str, Any],
		site_ids: Optional[List[str]] = None,
		batch_id: Optional[str] = None,
		asset_info: Optional[Dict[str, Any]] = None,
		max_candidates: int = 3,
		ssp_scenario: str = "ssp2",
		target_year: int = 2040
	) -> Dict[str, Any]:
		"""
		사업장 이전 후보지 추천 요청 (~1000개 격자 평가)

		Args:
			candidate_grids: 후보지 격자 목록
				[
					{"latitude": 37.5665, "longitude": 126.9780},
					{"latitude": 37.5666, "longitude": 126.9781},
					...
				]
			building_info: 건물 정보 (필수)
			site_ids: 사업장 ID 리스트 (선택)
			batch_id: 배치 작업 ID (선택, ModelOps 콜백용)
			asset_info: 자산 정보 (선택)
			max_candidates: 최대 추천 후보지 개수 (기본: 3)
			ssp_scenario: SSP 시나리오 (기본: "ssp2")
			target_year: 목표 연도 (기본: 2040)

		Returns:
			{
				"candidates": [
					{
						"rank": 1,
						"latitude": 37.5665,
						"longitude": 126.9780,
						"total_aal": 0.123456,
						"average_integrated_risk": 45.67,
						"risk_details": {
							"extreme_heat": {...},
							"extreme_cold": {...},
							...  # 9개 리스크
						}
					},
					...
				],
				"total_grids_evaluated": 1000,
				"search_criteria": {
					"max_candidates": 3,
					"ssp_scenario": "ssp2",
					"target_year": 2040
				},
				"calculated_at": "2025-12-11T..."
			}
		"""
		total_grids = len(candidate_grids)
		self.logger.info(f"이전 후보지 추천 요청: {total_grids}개 격자, site_ids={site_ids}")

		# 유효성 검증
		if total_grids == 0:
			raise ValueError("candidate_grids는 최소 1개 이상이어야 합니다.")
		if not building_info:
			raise ValueError("building_info is required")

		payload = {
			"candidate_grids": candidate_grids,
			"building_info": building_info,
			"search_criteria": {
				"max_candidates": max_candidates,
				"ssp_scenario": ssp_scenario,
				"target_year": target_year
			}
		}

		if site_ids:
			payload["site_ids"] = site_ids
		if batch_id:
			payload["batch_id"] = batch_id
		if asset_info:
			payload["asset_info"] = asset_info

		try:
			response = self.client.post("/api/site-assessment/recommend-locations", json=payload)
			response.raise_for_status()

			result = response.json()
			evaluated = result.get('total_grids_evaluated', 0)
			self.logger.info(f"이전 후보지 추천 완료: {evaluated}개 격자 평가")

			if result.get('candidates'):
				top1_aal = result['candidates'][0]['total_aal']
				self.logger.info(f"  Top 1 AAL: {top1_aal:.6f}")

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
