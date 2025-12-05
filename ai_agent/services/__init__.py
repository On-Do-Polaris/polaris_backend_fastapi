'''
파일명: __init__.py
파일 개요: Services 패키지 초기화

변경사항 (2025-12-03):
- AALCalculatorService: ModelOps로 이관 (삭제)
- ModelOpsClient 추가: ModelOps API 호출 클라이언트
'''

from .modelops_client import ModelOpsClient, get_modelops_client

__all__ = [
	'ModelOpsClient',
	'get_modelops_client'
]
