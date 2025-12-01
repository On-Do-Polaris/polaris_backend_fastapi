"""
파일명: logging_config.py
최종 수정일: 2025-12-01
버전: v01
파일 개요: 중앙 로깅 설정 (Python logging 모듈 기반)
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# 로그 디렉토리 생성
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 로그 포맷 (구조화)
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    중앙 로깅 설정

    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        루트 로거 인스턴스
    """
    # 루트 로거 설정
    root_logger = logging.getLogger()

    # 기존 핸들러 제거 (중복 방지)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 1. 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # 2. 파일 핸들러 (날짜별 - 모든 로그)
    today = datetime.now().strftime("%Y-%m-%d")
    file_handler = logging.FileHandler(
        LOG_DIR / f"app_{today}.log",
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(file_handler)

    # 3. 에러 전용 파일 핸들러
    error_handler = logging.FileHandler(
        LOG_DIR / f"error_{today}.log",
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(error_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    로거 인스턴스 반환

    Args:
        name: 로거 이름 (예: 'api.service', 'ai_agent.nodes')

    Returns:
        로거 인스턴스
    """
    return logging.getLogger(name)
