'''
파일명: langsmith_tracer.py
최종 수정일: 2025-11-17
버전: v01
파일 개요: LangSmith 트레이싱 유틸리티 (25개 Agent 추적용)
'''
import functools
from typing import Any, Dict, Callable
from datetime import datetime
import traceback


class LangSmithTracer:
	"""
	LangSmith 트레이싱 헬퍼 클래스
	AI Agent 실행 추적 및 메트릭 수집
	"""

	def __init__(self, config):
		"""
		LangSmith Tracer 초기화

		Args:
			config: 설정 객체
		"""
		self.config = config
		self.enabled = config.LANGSMITH_CONFIG.get('enabled', False)
		self.project_name = config.LANGSMITH_CONFIG.get('project_name', 'skax-physical-risk')
		self.default_tags = config.LANGSMITH_CONFIG.get('default_tags', [])

		if self.enabled:
			try:
				from langsmith import Client
				from langsmith.run_helpers import traceable
				self.client = Client()
				self.traceable = traceable
				print(f"[LangSmith] Tracing enabled for project: {self.project_name}")
			except ImportError:
				print("[LangSmith] Warning: langsmith package not installed. Tracing disabled.")
				self.enabled = False
		else:
			print("[LangSmith] Tracing disabled")

	def trace_agent(
		self,
		agent_name: str,
		agent_type: str = "agent",
		tags: list = None
	):
		"""
		Agent 실행 추적 데코레이터

		Args:
			agent_name: Agent 이름
			agent_type: Agent 타입 (agent, chain, llm, tool)
			tags: 추가 태그

		Returns:
			데코레이터 함수
		"""
		def decorator(func: Callable) -> Callable:
			if not self.enabled:
				# LangSmith 비활성화 시 원본 함수 반환
				return func

			@functools.wraps(func)
			def wrapper(*args, **kwargs):
				# 실행 시작 시간
				start_time = datetime.now()

				# 태그 설정
				run_tags = self.default_tags.copy()
				if tags:
					run_tags.extend(tags)
				run_tags.append(f"agent:{agent_name}")
				run_tags.append(f"type:{agent_type}")

				try:
					# Agent 실행
					result = func(*args, **kwargs)

					# 실행 시간 계산
					execution_time = (datetime.now() - start_time).total_seconds()

					# LangSmith에 메타데이터 기록
					if self.config.LANGSMITH_CONFIG.get('trace_metadata', True):
						metadata = {
							'agent_name': agent_name,
							'agent_type': agent_type,
							'execution_time': execution_time,
							'status': 'success',
							'timestamp': start_time.isoformat()
						}

						# 결과에 메타데이터 추가 (딕셔너리인 경우)
						if isinstance(result, dict):
							result['_langsmith_metadata'] = metadata

					return result

				except Exception as e:
					# 에러 시간 계산
					execution_time = (datetime.now() - start_time).total_seconds()

					# 에러 추적
					if self.config.LANGSMITH_CONFIG.get('trace_errors', True):
						error_metadata = {
							'agent_name': agent_name,
							'agent_type': agent_type,
							'execution_time': execution_time,
							'status': 'failed',
							'error_type': type(e).__name__,
							'error_message': str(e),
							'traceback': traceback.format_exc(),
							'timestamp': start_time.isoformat()
						}

						print(f"[LangSmith] Error in {agent_name}: {str(e)}")

					# 에러 재발생
					raise

			return wrapper
		return decorator

	def trace_workflow_node(
		self,
		node_name: str,
		tags: list = None
	):
		"""
		LangGraph 워크플로우 노드 추적 데코레이터

		Args:
			node_name: 노드 이름
			tags: 추가 태그

		Returns:
			데코레이터 함수
		"""
		return self.trace_agent(
			agent_name=node_name,
			agent_type="workflow_node",
			tags=tags or []
		)

	def log_metric(
		self,
		metric_name: str,
		value: float,
		metadata: Dict[str, Any] = None
	):
		"""
		메트릭 로깅

		Args:
			metric_name: 메트릭 이름
			value: 메트릭 값
			metadata: 추가 메타데이터
		"""
		if not self.enabled:
			return

		try:
			print(f"[LangSmith Metric] {metric_name}: {value}")
			if metadata:
				print(f"  Metadata: {metadata}")
		except Exception as e:
			print(f"[LangSmith] Warning: Failed to log metric: {e}")

	def log_agent_execution(
		self,
		agent_name: str,
		execution_time: float,
		status: str,
		input_data: Dict = None,
		output_data: Dict = None,
		error: Exception = None
	):
		"""
		Agent 실행 로그 기록

		Args:
			agent_name: Agent 이름
			execution_time: 실행 시간 (초)
			status: 상태 (success, failed)
			input_data: 입력 데이터
			output_data: 출력 데이터
			error: 에러 (있는 경우)
		"""
		if not self.enabled:
			return

		log_data = {
			'agent_name': agent_name,
			'execution_time': execution_time,
			'status': status,
			'timestamp': datetime.now().isoformat()
		}

		if input_data and self.config.LANGSMITH_CONFIG.get('trace_inputs', True):
			log_data['input_summary'] = str(input_data)[:200]  # 처음 200자만

		if output_data and self.config.LANGSMITH_CONFIG.get('trace_outputs', True):
			log_data['output_summary'] = str(output_data)[:200]  # 처음 200자만

		if error and self.config.LANGSMITH_CONFIG.get('trace_errors', True):
			log_data['error'] = str(error)

		print(f"[LangSmith Log] {log_data}")


def get_tracer(config):
	"""
	LangSmith Tracer 인스턴스 생성

	Args:
		config: 설정 객체

	Returns:
		LangSmithTracer 인스턴스
	"""
	return LangSmithTracer(config)
