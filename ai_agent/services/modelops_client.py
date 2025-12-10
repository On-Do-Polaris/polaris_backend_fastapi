"""
파일명: modelops_client.py
최종 수정일: 2025-12-10
버전: v02
파일 개요: ModelOps API 호출 클라이언트 (통합 Risk Assessment API)

역할:
	- ModelOps FastAPI 서버와 통신
	- 통합 H×E×V×AAL 계산 요청
	- WebSocket 실시간 진행상황 지원
	- 비동기 작업 상태 폴링
	- 캐싱된 결과 조회

변경사항:
	- 기존 separate endpoints (vulnerability, exposure, hazard, aal) 제거
	- 신규 unified endpoint (risk-assessment/calculate) 추가
	- WebSocket 지원 추가
	- Health check 엔드포인트 추가
"""

import httpx
import logging
import json
import asyncio
from typing import Dict, Any, Optional, Callable
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ModelOpsClient:
	"""
	ModelOps API 클라이언트 (통합 Risk Assessment)

	역할:
	- 통합 H×E×V×AAL 계산 요청
	- WebSocket 실시간 진행상황 수신
	- 캐싱된 결과 조회
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

	def calculate_risk_assessment(
		self,
		latitude: float,
		longitude: float,
		site_id: Optional[str] = None,
		building_info: Optional[Dict[str, Any]] = None,
		asset_info: Optional[Dict[str, Any]] = None
	) -> Dict[str, Any]:
		"""
		통합 리스크 평가 계산 요청 (H×E×V×AAL 일괄 계산)

		Args:
			latitude: 위도 (-90 ~ 90)
			longitude: 경도 (-180 ~ 180)
			site_id: 사업장 ID (선택)
			building_info: 건물 정보 (선택)
			asset_info: 자산 정보 (선택)

		Returns:
			{
				"request_id": str,
				"status": str,
				"websocket_url": str,
				"message": str,
				"site_id": str (optional)
			}
		"""
		self.logger.info(f"통합 리스크 평가 계산 요청: lat={latitude}, lng={longitude}, site_id={site_id}")

		# 유효성 검증
		if not (-90 <= latitude <= 90):
			raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90.")
		if not (-180 <= longitude <= 180):
			raise ValueError(f"Invalid longitude: {longitude}. Must be between -180 and 180.")

		payload = {
			"latitude": latitude,
			"longitude": longitude
		}

		if site_id:
			payload["site_id"] = site_id
		if building_info:
			payload["building_info"] = building_info
		if asset_info:
			payload["asset_info"] = asset_info

		try:
			response = self.client.post("/api/v1/risk-assessment/calculate", json=payload)
			response.raise_for_status()

			result = response.json()
			self.logger.info(
				f"통합 리스크 평가 계산 시작: request_id={result.get('request_id')}, "
				f"status={result.get('status')}"
			)

			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"통합 리스크 평가 계산 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"통합 리스크 평가 계산 중 오류: {str(e)}")
			raise

	def get_risk_assessment_status(self, request_id: str) -> Dict[str, Any]:
		"""
		리스크 평가 진행 상태 조회

		Args:
			request_id: 요청 ID

		Returns:
			{
				"status": str,  # queued, processing, completed, failed
				"current": int,  # 현재 처리 중인 리스크 번호 (1-9)
				"total": int,  # 전체 리스크 개수 (9)
				"current_risk": str,  # 현재 처리 중인 리스크 타입
				"progress": float  # 진행률 (%)
			}
		"""
		self.logger.debug(f"리스크 평가 상태 조회: request_id={request_id}")

		try:
			response = self.client.get(
				"/api/v1/risk-assessment/status",
				params={"request_id": request_id}
			)
			response.raise_for_status()

			result = response.json()
			self.logger.debug(f"상태 조회 완료: status={result.get('status')}, progress={result.get('progress', 0):.1f}%")

			return result

		except httpx.HTTPStatusError as e:
			self.logger.error(f"상태 조회 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"상태 조회 중 오류: {str(e)}")
			raise

	def get_cached_results(
		self,
		latitude: Optional[float] = None,
		longitude: Optional[float] = None,
		site_id: Optional[str] = None
	) -> Dict[str, Any]:
		"""
		캐싱된 리스크 평가 결과 조회

		Args:
			latitude: 위도 (선택)
			longitude: 경도 (선택)
			site_id: 사업장 ID (선택)

		Note:
			site_id 또는 (latitude AND longitude) 중 하나는 필수

		Returns:
			{
				"latitude": float,
				"longitude": float,
				"site_id": str (optional),
				"hazard": {risk_type: {...}},
				"exposure": {risk_type: {...}},
				"vulnerability": {risk_type: {...}},
				"integrated_risk": {risk_type: {...}},
				"aal_scaled": {risk_type: {...}},
				"summary": {...},
				"calculated_at": str
			}
		"""
		# 유효성 검증
		if not site_id and not (latitude and longitude):
			raise ValueError("site_id 또는 (latitude, longitude)가 필요합니다.")

		self.logger.info(f"캐싱된 결과 조회: lat={latitude}, lng={longitude}, site_id={site_id}")

		params = {}
		if site_id:
			params["site_id"] = site_id
		if latitude is not None:
			params["latitude"] = latitude
		if longitude is not None:
			params["longitude"] = longitude

		try:
			response = self.client.get("/api/v1/risk-assessment/results", params=params)
			response.raise_for_status()

			result = response.json()
			self.logger.info(f"캐싱된 결과 조회 완료: risk_count={result.get('summary', {}).get('risk_count', 0)}")

			return result

		except httpx.HTTPStatusError as e:
			if e.response.status_code == 404:
				self.logger.warning(f"캐싱된 결과 없음: lat={latitude}, lng={longitude}, site_id={site_id}")
				raise ValueError(f"해당 위치의 리스크 평가 결과가 없습니다.")
			self.logger.error(f"캐싱된 결과 조회 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			self.logger.error(f"캐싱된 결과 조회 중 오류: {str(e)}")
			raise

	async def connect_websocket(
		self,
		request_id: str,
		on_progress: Optional[Callable[[Dict], None]] = None,
		on_complete: Optional[Callable[[Dict], None]] = None,
		on_error: Optional[Callable[[str], None]] = None,
		max_retries: int = 3
	) -> None:
		"""
		WebSocket을 통한 실시간 진행상황 수신

		Args:
			request_id: 요청 ID
			on_progress: 진행 상태 업데이트 콜백
			on_complete: 완료 콜백
			on_error: 에러 콜백
			max_retries: 최대 재연결 시도 횟수

		Note:
			이 메서드는 websockets 라이브러리가 필요합니다.
			pip install websockets>=12.0
		"""
		try:
			import websockets
		except ImportError:
			self.logger.error("websockets 라이브러리가 설치되지 않았습니다. pip install websockets>=12.0")
			raise ImportError("websockets 라이브러리가 필요합니다: pip install websockets>=12.0")

		# WebSocket URL 생성
		ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
		ws_url = f"{ws_url}/api/v1/risk-assessment/ws/{request_id}"

		self.logger.info(f"WebSocket 연결 시도: {ws_url}")

		retry_count = 0
		while retry_count < max_retries:
			try:
				async with websockets.connect(ws_url) as websocket:
					self.logger.info(f"WebSocket 연결 성공: request_id={request_id}")

					async for message in websocket:
						try:
							data = json.loads(message)
							status = data.get("status")

							if status == "processing":
								if on_progress:
									on_progress(data)
								self.logger.debug(
									f"진행 중: {data.get('current_risk')} "
									f"({data.get('current')}/{data.get('total')})"
								)

							elif status == "completed":
								if on_complete:
									on_complete(data)
								self.logger.info(f"계산 완료: request_id={request_id}")
								return

							elif status == "failed":
								error_msg = data.get("error", {}).get("message", "Unknown error")
								if on_error:
									on_error(error_msg)
								self.logger.error(f"계산 실패: {error_msg}")
								raise Exception(f"ModelOps 계산 실패: {error_msg}")

						except json.JSONDecodeError as e:
							self.logger.warning(f"WebSocket 메시지 파싱 실패: {e}")
							continue

			except websockets.exceptions.ConnectionClosed as e:
				retry_count += 1
				self.logger.warning(
					f"WebSocket 연결 끊김 (재시도 {retry_count}/{max_retries}): {e}"
				)
				if retry_count < max_retries:
					await asyncio.sleep(2 ** retry_count)  # Exponential backoff
				else:
					self.logger.error("WebSocket 재연결 시도 초과")
					if on_error:
						on_error("WebSocket 연결 실패")
					raise

			except Exception as e:
				self.logger.error(f"WebSocket 오류: {str(e)}")
				if on_error:
					on_error(str(e))
				raise

	def _poll_status(
		self,
		request_id: str,
		poll_interval: float = 2.0,
		max_wait_time: float = 300.0
	) -> Dict[str, Any]:
		"""
		비동기 작업 상태 폴링 (HTTP Polling 방식)

		Args:
			request_id: 요청 ID
			poll_interval: 폴링 간격 (초)
			max_wait_time: 최대 대기 시간 (초)

		Returns:
			완료된 계산 결과 상태
		"""
		self.logger.info(f"작업 상태 폴링 시작: request_id={request_id}")

		import time
		start_time = time.time()

		while True:
			try:
				status_data = self.get_risk_assessment_status(request_id)
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
					current_risk = status_data.get('current_risk', '')
					self.logger.debug(
						f"작업 진행 중: request_id={request_id}, "
						f"progress={progress:.1f}%, current_risk={current_risk}"
					)

					# 타임아웃 체크
					elapsed = time.time() - start_time
					if elapsed > max_wait_time:
						raise TimeoutError(f"작업 타임아웃: request_id={request_id}")

					# 다음 폴링까지 대기
					time.sleep(poll_interval)

				else:
					self.logger.warning(f"알 수 없는 상태: request_id={request_id}, status={status}")
					time.sleep(poll_interval)

			except httpx.HTTPStatusError as e:
				self.logger.error(f"상태 조회 실패 (HTTP {e.response.status_code}): {e.response.text}")
				raise
			except Exception as e:
				self.logger.error(f"상태 폴링 중 오류: {str(e)}")
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
		base_url = os.getenv('MODELOPS_BASE_URL', 'http://localhost:8001')
		api_key = os.getenv('MODELOPS_API_KEY')

		_modelops_client = ModelOpsClient(
			base_url=base_url,
			api_key=api_key,
			timeout=60.0,
			max_retries=3
		)

	return _modelops_client
