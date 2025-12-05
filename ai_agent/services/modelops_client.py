"""
파일명: modelops_client.py
최종 수정일: 2025-12-03
버전: v01
파일 개요: ModelOps API 호출 클라이언트

역할:
	- ModelOps FastAPI 서버와 통신
	- Vulnerability, Exposure, Hazard Score, AAL 계산 요청
	- 비동기 작업 상태 폴링
	- ERD 기준 데이터 변환 및 전달
"""

import httpx
import logging
from typing import Dict, Any, Optional
import asyncio
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ModelOpsClient:
	"""
	ModelOps API 클라이언트

	역할:
	- ModelOps 서버에 리스크 계산 요청 (Vulnerability, Exposure, Hazard, AAL)
	- 동기/비동기 응답 처리
	- 재시도 로직 및 타임아웃 관리
	"""

	def __init__(
		self,
		base_url: str = "http://localhost:8001",
		api_key: Optional[str] = None,
		timeout: float = 60.0,
		max_retries: int = 3
	):
		"""
		ModelOpsClient 초기화

		Args:
			base_url: ModelOps API Base URL
			api_key: API 인증 키 (선택)
			timeout: 요청 타임아웃 (초)
			max_retries: 최대 재시도 횟수
		"""
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

	def calculate_vulnerability(
		self,
		site_id: str,
		building_info: Dict[str, Any],
		location: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		Vulnerability 점수 계산 요청 (9대 리스크)

		Args:
			site_id: 사업장 ID
			building_info: 건물 정보 (from additional_data.building_info)
			location: 위치 정보 (latitude, longitude)

		Returns:
			9개 리스크별 vulnerability 점수 (0-100)
		"""
		self.logger.info(f"Vulnerability 계산 요청: site_id={site_id}")

		payload = {
			"site_id": site_id,
			"building_info": building_info or {},
			"location": location
		}

		try:
			response = self.client.post("/api/v1/calculate/vulnerability", json=payload)
			response.raise_for_status()

			result = response.json()
			self.logger.info(f"Vulnerability 계산 완료: status={result.get('status')}")

			# 202 Accepted (비동기)인 경우 상태 폴링
			if response.status_code == 202:
				request_id = result.get('request_id')
				result = self._poll_status(request_id, resource_type='vulnerability')

			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"Vulnerability 계산 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"Vulnerability 계산 중 오류: {str(e)}")
			raise

	def calculate_exposure(
		self,
		site_id: str,
		asset_info: Dict[str, Any],
		location: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		Exposure 점수 계산 요청 (9대 리스크)

		Args:
			site_id: 사업장 ID
			asset_info: 자산 정보 (from additional_data.asset_info)
			location: 위치 정보 (latitude, longitude)

		Returns:
			9개 리스크별 exposure 점수 (0-1)
		"""
		self.logger.info(f"Exposure 계산 요청: site_id={site_id}")

		payload = {
			"site_id": site_id,
			"asset_info": asset_info or {},
			"location": location
		}

		try:
			response = self.client.post("/api/v1/calculate/exposure", json=payload)
			response.raise_for_status()

			result = response.json()
			self.logger.info(f"Exposure 계산 완료: status={result.get('status')}")

			# 202 Accepted (비동기)인 경우 상태 폴링
			if response.status_code == 202:
				request_id = result.get('request_id')
				result = self._poll_status(request_id, resource_type='exposure')

			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"Exposure 계산 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"Exposure 계산 중 오류: {str(e)}")
			raise

	def get_hazard_scores(
		self,
		latitude: float,
		longitude: float,
		scenario_id: int = 2,
		start_year: int = 2025,
		end_year: int = 2050
	) -> Dict[str, Any]:
		"""
		Hazard Score 조회 (배치 처리된 기후 데이터)

		Args:
			latitude: 위도
			longitude: 경도
			scenario_id: SSP 시나리오 ID (1: SSP1-2.6, 2: SSP2-4.5, 3: SSP3-7.0, 4: SSP5-8.5)
			start_year: 시작 연도
			end_year: 종료 연도

		Returns:
			9개 리스크별 hazard 점수 (0-1)
		"""
		self.logger.info(f"Hazard Score 조회: lat={latitude}, lng={longitude}, scenario={scenario_id}")

		params = {
			"latitude": latitude,
			"longitude": longitude,
			"scenario_id": scenario_id,
			"start_year": start_year,
			"end_year": end_year
		}

		try:
			response = self.client.get("/api/v1/hazard-scores", params=params)
			response.raise_for_status()

			result = response.json()
			self.logger.info(f"Hazard Score 조회 완료: grid_id={result.get('grid_id')}")

			return result

		except httpx.HTTPStatusError as e:
			if e.response.status_code == 404:
				self.logger.warning(f"해당 위치의 Hazard 데이터 없음: lat={latitude}, lng={longitude}")
				return None
			self.logger.error(f"Hazard Score 조회 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"Hazard Score 조회 중 오류: {str(e)}")
			raise

	def calculate_aal(
		self,
		site_id: str,
		hazard_scores: Dict[str, Any],
		vulnerability_scores: Dict[str, float],
		asset_info: Dict[str, Any],
		climate_data: Dict[str, Any]
	) -> Dict[str, Any]:
		"""
		AAL (연평균 재무 손실률) 계산 요청

		Args:
			site_id: 사업장 ID
			hazard_scores: 9개 리스크별 hazard 점수 (4개 시나리오별)
			vulnerability_scores: 9개 리스크별 vulnerability 점수
			asset_info: 자산 정보 (총 자산 가치, 보험 가입률)
			climate_data: 기후 데이터 (grid_id, scenario_id, variables)

		Returns:
			9개 리스크별 AAL 결과 (4개 시나리오별)
		"""
		self.logger.info(f"AAL 계산 요청: site_id={site_id}")

		payload = {
			"site_id": site_id,
			"hazard_scores": hazard_scores,
			"vulnerability_scores": vulnerability_scores,
			"asset_info": asset_info,
			"climate_data": climate_data
		}

		try:
			response = self.client.post("/api/v1/calculate/aal", json=payload)
			response.raise_for_status()

			result = response.json()
			self.logger.info(f"AAL 계산 완료: status={result.get('status')}")

			# 202 Accepted (비동기)인 경우 상태 폴링
			if response.status_code == 202:
				request_id = result.get('request_id')
				result = self._poll_status(request_id, resource_type='aal')

			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"AAL 계산 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"AAL 계산 중 오류: {str(e)}")
			raise

	def _poll_status(
		self,
		request_id: str,
		resource_type: str,
		poll_interval: float = 2.0,
		max_wait_time: float = 300.0
	) -> Dict[str, Any]:
		"""
		비동기 작업 상태 폴링

		Args:
			request_id: 요청 ID
			resource_type: 리소스 타입 (vulnerability, exposure, aal)
			poll_interval: 폴링 간격 (초)
			max_wait_time: 최대 대기 시간 (초)

		Returns:
			완료된 계산 결과
		"""
		self.logger.info(f"작업 상태 폴링 시작: request_id={request_id}, type={resource_type}")

		start_time = asyncio.get_event_loop().time()

		while True:
			try:
				response = self.client.get(f"/api/v1/status/{request_id}")
				response.raise_for_status()

				status_data = response.json()
				status = status_data.get('status')

				if status == 'completed':
					self.logger.info(f"작업 완료: request_id={request_id}")
					return status_data

				elif status == 'failed':
					error_msg = status_data.get('error', {}).get('message', 'Unknown error')
					self.logger.error(f"작업 실패: request_id={request_id}, error={error_msg}")
					raise Exception(f"ModelOps 작업 실패: {error_msg}")

				elif status in ['queued', 'processing']:
					progress = status_data.get('progress', 0)
					self.logger.debug(f"작업 진행 중: request_id={request_id}, progress={progress}%")

					# 타임아웃 체크
					elapsed = asyncio.get_event_loop().time() - start_time
					if elapsed > max_wait_time:
						raise TimeoutError(f"작업 타임아웃: request_id={request_id}")

					# 다음 폴링까지 대기
					asyncio.sleep(poll_interval)

				else:
					self.logger.warning(f"알 수 없는 상태: request_id={request_id}, status={status}")
					asyncio.sleep(poll_interval)

			except httpx.HTTPStatusError as e:
				self.logger.error(f"상태 조회 실패 (HTTP {e.response.status_code}): {e.response.text}")
				raise
			except Exception as e:
				self.logger.error(f"상태 폴링 중 오류: {str(e)}")
				raise

	def start_batch_recommendation(
		self,
		sites: list,
		recommendation_type: str = "mitigation_priority",
		scenario: Optional[str] = None
	) -> Dict[str, Any]:
		"""
		배치 추천 작업 시작 (ModelOps)

		Args:
			sites: 사업장 리스크 데이터 리스트
			recommendation_type: 추천 타입 (mitigation_priority, cost_optimization, etc.)
			scenario: 기후 시나리오 (optional)

		Returns:
			{"batch_id": str, "status": str, "created_at": str}
		"""
		self.logger.info(f"배치 추천 작업 시작: sites={len(sites)}, type={recommendation_type}")

		payload = {
			"sites": sites,
			"recommendation_type": recommendation_type,
			"scenario": scenario
		}

		try:
			response = self.client.post("/api/v1/batch/recommend-sites", json=payload)
			response.raise_for_status()

			result = response.json()
			self.logger.info(f"배치 작업 시작 완료: batch_id={result.get('batch_id')}")
			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"배치 추천 시작 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"배치 추천 작업 시작 중 오류: {str(e)}")
			raise

	def get_batch_progress(self, batch_id: str) -> Dict[str, Any]:
		"""
		배치 작업 진행률 조회

		Args:
			batch_id: 배치 작업 ID

		Returns:
			{
				"batch_id": str,
				"status": str,  # "pending", "processing", "completed", "failed"
				"progress": float,  # 0.0 to 1.0
				"processed_count": int,
				"total_count": int,
				"updated_at": str
			}
		"""
		self.logger.info(f"배치 진행률 조회: batch_id={batch_id}")

		try:
			response = self.client.get(f"/api/v1/batch/{batch_id}/progress")
			response.raise_for_status()

			result = response.json()
			self.logger.debug(f"배치 진행률: {result.get('progress', 0):.1%}")
			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"배치 진행률 조회 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"배치 진행률 조회 중 오류: {str(e)}")
			raise

	def get_batch_results(self, batch_id: str) -> Dict[str, Any]:
		"""
		배치 작업 결과 조회

		Args:
			batch_id: 배치 작업 ID

		Returns:
			{
				"batch_id": str,
				"status": str,
				"results": List[Dict],  # 각 사업장별 추천 결과
				"completed_at": str
			}
		"""
		self.logger.info(f"배치 결과 조회: batch_id={batch_id}")

		try:
			response = self.client.get(f"/api/v1/batch/{batch_id}/results")
			response.raise_for_status()

			result = response.json()
			self.logger.info(f"배치 결과 조회 완료: {len(result.get('results', []))} 건")
			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"배치 결과 조회 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"배치 결과 조회 중 오류: {str(e)}")
			raise

	def cancel_batch_job(self, batch_id: str) -> Dict[str, Any]:
		"""
		배치 작업 취소

		Args:
			batch_id: 배치 작업 ID

		Returns:
			{"batch_id": str, "status": "cancelled"}
		"""
		self.logger.info(f"배치 작업 취소: batch_id={batch_id}")

		try:
			response = self.client.delete(f"/api/v1/batch/{batch_id}")
			response.raise_for_status()

			result = response.json()
			self.logger.info(f"배치 작업 취소 완료: batch_id={batch_id}")
			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"배치 작업 취소 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"배치 작업 취소 중 오류: {str(e)}")
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
		base_url = os.getenv('MODELOPS_BASE_URL', 'http://localhost:8001')
		api_key = os.getenv('MODELOPS_API_KEY')

		_modelops_client = ModelOpsClient(
			base_url=base_url,
			api_key=api_key,
			timeout=60.0,
			max_retries=3
		)

	return _modelops_client
