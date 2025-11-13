"""
SKAX Physical Risk Analyzer - Entry Point
AI Agent 시스템 실행 스크립트
"""
import sys
import os

# ai_agent 패키지를 import 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_agent.main import main

if __name__ == "__main__":
    main()
