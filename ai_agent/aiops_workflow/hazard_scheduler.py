'''
파일명: hazard_scheduler.py
최종 수정일: 2025-11-22
버전: v02
파일 개요: Hazard Score(H) 배치 계산 스케줄러
	- 연 1회 자동 실행
	- 크론잡, Airflow, Celery Beat 등과 통합 가능
	- 격자 좌표는 외부에서 제공 (DB에서 조회)
변경 이력:
	- 2025-11-22: v01 - 초기 생성
	- 2025-11-22: v02 - grid_processor 의존성 제거
'''

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .hazard_batch import HazardBatchProcessor

logger = logging.getLogger(__name__)


class HazardScheduler:
	"""
	Hazard Score(H) 배치 계산 스케줄러
	연 1회 전체 격자 좌표에 대해 위험 점수 계산 실행
	"""

	def __init__(self, config: Dict[str, Any]):
		"""
		Args:
			config: 스케줄러 설정
				- schedule: 스케줄 설정 (cron 표현식 또는 interval)
				- batch_config: 배치 프로세서 설정
				- enable_scheduler: 스케줄러 활성화 여부
		"""
		self.config = config
		self.batch_config = config.get('batch_config', {})
		self.enable_scheduler = config.get('enable_scheduler', True)

		# 스케줄러 초기화
		self.scheduler = BackgroundScheduler() if self.enable_scheduler else None

		# 프로세서 초기화
		self.batch_processor = HazardBatchProcessor(self.batch_config)

		logger.info("HazardScheduler initialized")


	def start(self, grid_coordinates_callback=None) -> None:
		"""
		스케줄러 시작
		기본: 매년 1월 1일 오전 4시 실행 (P(H) 계산 이후)

		Args:
			grid_coordinates_callback: 격자 좌표를 가져오는 콜백 함수
				예: lambda: db.query("SELECT lat, lon FROM grid_coordinates")
		"""
		if not self.enable_scheduler:
			logger.warning("Scheduler is disabled in config")
			return

		# 스케줄 설정 (기본: 매년 1월 1일 04:00 - P(H) 이후 실행)
		schedule_config = self.config.get('schedule', {
			'type': 'cron',
			'month': 1,
			'day': 1,
			'hour': 4,
			'minute': 0
		})

		if schedule_config['type'] == 'cron':
			trigger = CronTrigger(
				month=schedule_config.get('month', 1),
				day=schedule_config.get('day', 1),
				hour=schedule_config.get('hour', 4),
				minute=schedule_config.get('minute', 0)
			)

			self.scheduler.add_job(
				lambda: self.run_batch_calculation(grid_coordinates_callback() if grid_coordinates_callback else []),
				trigger=trigger,
				id='annual_hazard_batch',
				name='Annual Hazard Score Batch Calculation',
				replace_existing=True
			)

			logger.info(f"Scheduler configured: Annual run on {schedule_config['month']}/{schedule_config['day']} at {schedule_config['hour']:02d}:{schedule_config['minute']:02d}")

		elif schedule_config['type'] == 'interval':
			# 테스트용 interval 스케줄
			interval_hours = schedule_config.get('hours', 24)
			self.scheduler.add_job(
				lambda: self.run_batch_calculation(grid_coordinates_callback() if grid_coordinates_callback else []),
				'interval',
				hours=interval_hours,
				id='interval_hazard_batch',
				name=f'Hazard Score Batch Calculation (every {interval_hours}h)',
				replace_existing=True
			)

			logger.info(f"Scheduler configured: Interval run every {interval_hours} hours")

		self.scheduler.start()
		logger.info("Scheduler started")


	def stop(self) -> None:
		"""
		스케줄러 중지
		"""
		if self.scheduler and self.scheduler.running:
			self.scheduler.shutdown()
			logger.info("Scheduler stopped")


	def run_batch_calculation(self, grid_coordinates: List[Dict[str, float]], dry_run: bool = False) -> Optional[Dict[str, Any]]:
		"""
		배치 계산 실행 (스케줄러 또는 수동 호출)

		Args:
			grid_coordinates: 격자 좌표 리스트 (DB 또는 외부에서 제공)
				예: [{'lat': 37.5665, 'lon': 126.9780}, ...]
			dry_run: True일 경우 실제 계산 없이 테스트만 수행

		Returns:
			배치 실행 결과
		"""
		start_time = datetime.now()
		logger.info(f"=== Starting Annual Hazard Score Batch Calculation {'(DRY RUN)' if dry_run else ''} ===")
		logger.info(f"Start time: {start_time.isoformat()}")
		logger.info(f"Grid coordinates: {len(grid_coordinates)}")

		try:
			if dry_run:
				logger.info("DRY RUN: Skipping actual calculation")
				return {
					'status': 'dry_run',
					'grid_count': len(grid_coordinates),
					'message': 'Dry run completed successfully'
				}

			# 배치 처리 실행
			logger.info("Running batch hazard score calculation...")
			result = self.batch_processor.process_all_grids(grid_coordinates)

			# 결과 요약
			end_time = datetime.now()
			duration = (end_time - start_time).total_seconds()

			summary = {
				'status': 'completed',
				'execution_time': start_time.isoformat(),
				'total_grids': result['total_grids'],
				'processed': result['processed'],
				'failed': result['failed'],
				'success_rate': round(result['processed'] / result['total_grids'] * 100, 2) if result['total_grids'] > 0 else 0,
				'duration_seconds': duration,
				'duration_hours': round(duration / 3600, 2)
			}

			logger.info("=== Batch Calculation Completed ===")
			logger.info(f"Total grids: {summary['total_grids']}")
			logger.info(f"Processed: {summary['processed']}")
			logger.info(f"Failed: {summary['failed']}")
			logger.info(f"Success rate: {summary['success_rate']}%")
			logger.info(f"Duration: {summary['duration_hours']} hours")

			return summary

		except Exception as e:
			logger.error(f"Batch calculation failed: {str(e)}", exc_info=True)

			return {
				'status': 'failed',
				'error': str(e),
				'execution_time': start_time.isoformat()
			}


	def get_next_run_time(self) -> Optional[datetime]:
		"""
		다음 실행 예정 시간 조회

		Returns:
			다음 실행 시간
		"""
		if not self.scheduler or not self.scheduler.running:
			return None

		job = self.scheduler.get_job('annual_hazard_batch') or self.scheduler.get_job('interval_hazard_batch')

		if job:
			return job.next_run_time

		return None


	def trigger_manual_run(self, grid_coordinates: List[Dict[str, float]], dry_run: bool = False) -> Dict[str, Any]:
		"""
		수동 실행 트리거

		Args:
			grid_coordinates: 격자 좌표 리스트
			dry_run: True일 경우 테스트 실행

		Returns:
			실행 결과
		"""
		logger.info("Manual hazard batch calculation triggered")
		return self.run_batch_calculation(grid_coordinates, dry_run=dry_run)
