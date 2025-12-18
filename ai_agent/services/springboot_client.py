"""
파일명: springboot_client.py
최종 수정일: 2025-12-12
버전: v01
파일 개요: Spring Boot API 클라이언트 (FastAPI → Spring Boot 콜백 호출용)

역할:
	- Spring Boot /api/analysis/complete 엔드포인트 호출
	- 분석 완료 알림 (리포트 생성 + 후보지 추천 완료 시)
	- 사용자에게 이메일 발송 트리거
"""

import httpx
import logging
from typing import Dict, Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class SpringBootClient:
	"""
	Spring Boot API 클라이언트

	역할:
	- 분석 완료 콜백 호출
	- FastAPI → Spring Boot 통신
	"""

	def __init__(
		self,
		base_url: Optional[str] = None,
		timeout: float = 30.0
	):
		"""
		SpringBootClient 초기화

		Args:
			base_url: Spring Boot API Base URL (None인 경우 환경변수 SPRING_BOOT_BASE_URL 사용)
			timeout: 요청 타임아웃 (초) - 기본 30초
		"""
		import os

		# 환경변수에서 URL 로드 (base_url이 None인 경우)
		if base_url is None:
			base_url = os.getenv('SPRING_BOOT_BASE_URL', 'http://localhost:8080')

		self.base_url = base_url.rstrip('/')
		self.timeout = timeout

		# HTTP 클라이언트 설정
		self.client = httpx.Client(
			base_url=self.base_url,
			timeout=self.timeout
		)

		logger.info(f"SpringBootClient 초기화: {self.base_url}")

	def __del__(self):
		"""리소스 정리"""
		if hasattr(self, 'client'):
			self.client.close()

	def notify_analysis_completion(self, user_id: UUID, report: bool = False) -> Dict[str, Any]:
		"""
		분석 완료 콜백 호출

		Args:
			user_id: 사용자 ID
			report: additional_data 사용 여부 (True: 사용함, False: 사용하지 않음)

		Returns:
			Spring Boot 응답
			{
				"result": "success",
				"message": "분석 완료 알림이 발송되었습니다."
			}

		Raises:
			httpx.HTTPStatusError: HTTP 에러 발생 시
			Exception: 기타 에러 발생 시
		"""
		logger.info(f"Spring Boot 분석 완료 알림: user_id={user_id}, report={report}")

		try:
			response = self.client.post(
				"/api/analysis/complete",
				json={"userId": str(user_id), "report": report}
			)
			response.raise_for_status()

			result = response.json()
			logger.info(f"분석 완료 알림 성공: {result}")

			return result

		except httpx.HTTPStatusError as e:
			logger.error(f"Spring Boot 알림 실패 (HTTP {e.response.status_code}): {e.response.text}")
			raise
		except Exception as e:
			logger.error(f"Spring Boot 알림 중 오류: {str(e)}")
			raise


# 싱글톤 인스턴스
_springboot_client: Optional[SpringBootClient] = None


def get_springboot_client() -> SpringBootClient:
	"""
	SpringBootClient 싱글톤 인스턴스 반환

	Returns:
		SpringBootClient 인스턴스
	"""
	global _springboot_client

	if _springboot_client is None:
		# 환경 변수에서 설정 로드
		import os
		base_url = os.getenv('SPRING_BOOT_BASE_URL', 'http://localhost:8080')

		_springboot_client = SpringBootClient(
			base_url=base_url,
			timeout=30.0
		)

	return _springboot_client
