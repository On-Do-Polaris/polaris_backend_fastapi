'''
파일명: ttl_cleaner.py
최종 수정일: 2025-11-21
버전: v01
파일 개요: Scratch Space TTL 기반 자동 정리 유틸리티
변경 이력:
	- 2025-11-21: v01 - 초기 생성
'''
import logging
from typing import Optional
from .scratch_manager import ScratchSpaceManager


logger = logging.getLogger(__name__)


def cleanup_expired_sessions(
	base_path: str = "./scratch",
	dry_run: bool = False
) -> int:
	"""
	만료된 Scratch Space 세션 정리

	Args:
		base_path: Scratch Space 기본 경로
		dry_run: True이면 실제 삭제 없이 목록만 표시

	Returns:
		정리된 세션 개수
	"""
	manager = ScratchSpaceManager(base_path=base_path)

	logger.info("🧹 Starting Scratch Space cleanup...")

	cleaned = manager.cleanup_expired(dry_run=dry_run)

	if dry_run:
		logger.info(f"[DRY RUN] Would clean {cleaned} session(s)")
	else:
		logger.info(f"✅ Cleaned {cleaned} expired session(s)")

	# 통계 출력
	stats = manager.get_stats()
	logger.info(f"📊 Stats: {stats['active_sessions']} active, "
	           f"{stats['expired_sessions']} expired, "
	           f"{stats['total_size_mb']} MB total")

	return cleaned


def setup_background_cleanup(
	interval_hours: int = 1,
	base_path: str = "./scratch"
):
	"""
	백그라운드 자동 정리 스케줄러 설정 (선택적)

	주의: 이 함수는 별도 스레드에서 실행됩니다.
	FastAPI의 경우 startup 이벤트에서 호출하세요.

	Args:
		interval_hours: 정리 간격 (시간)
		base_path: Scratch Space 기본 경로

	Example:
		# FastAPI startup
		@app.on_event("startup")
		async def startup_event():
		    setup_background_cleanup(interval_hours=1)
	"""
	import threading
	import time

	def cleanup_loop():
		"""백그라운드 정리 루프"""
		while True:
			try:
				cleanup_expired_sessions(base_path=base_path)
			except Exception as e:
				logger.error(f"Cleanup error: {e}")

			time.sleep(interval_hours * 3600)

	# 데몬 스레드로 실행 (메인 프로세스 종료 시 자동 종료)
	thread = threading.Thread(target=cleanup_loop, daemon=True)
	thread.start()

	logger.info(f"🔄 Background cleanup started (interval: {interval_hours}h)")


def get_scratch_stats(base_path: str = "./scratch") -> dict:
	"""
	Scratch Space 통계 조회

	Args:
		base_path: Scratch Space 기본 경로

	Returns:
		통계 정보 딕셔너리
	"""
	manager = ScratchSpaceManager(base_path=base_path)
	return manager.get_stats()
