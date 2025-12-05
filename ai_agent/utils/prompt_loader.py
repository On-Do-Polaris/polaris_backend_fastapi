# report_generation/utils/prompt_loader.py
"""
Prompt Loader Utility
- 프롬프트 템플릿 로딩
- Agent별 프롬프트 템플릿 제공
- 출력 언어 지시자 삽입
"""

import os
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class PromptLoader:
    """
    프롬프트 템플릿 로더

    역할:
    - 프롬프트 파일 로딩 및 캐싱
    - Agent별 프롬프트 템플릿 관리
    - 출력 언어 지시자 자동 추가

    사용법:
        loader = PromptLoader()
        prompt = loader.load('impact_analysis', output_language='ko')
    """

    # 언어별 출력 지시자
    LANGUAGE_INSTRUCTIONS = {
        'ko': '\n\n<OUTPUT_LANGUAGE>\nYou MUST write your entire response in Korean (한국어). All analysis, explanations, and content must be in Korean.\n</OUTPUT_LANGUAGE>',
        'en': '\n\n<OUTPUT_LANGUAGE>\nYou MUST write your entire response in English.\n</OUTPUT_LANGUAGE>'
    }

    def __init__(self):
        """
        PromptLoader 초기화
        """
        # ai_agent/utils/prompt_loader.py -> ai_agent/agents/report_generation/prompts
        self.prompt_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'agents',
            'report_generation',
            'prompts'
        )

        # 프롬프트 캐시
        self._cache: Dict[str, str] = {}

        logger.info(f"PromptLoader 초기화 완료 (dir={self.prompt_dir})")

    def load(self, prompt_name: str, output_language: str = 'en', use_cache: bool = True) -> str:
        """
        프롬프트 템플릿 로드 및 출력 언어 지시자 추가

        Args:
            prompt_name: 프롬프트 파일 이름 (확장자 제외)
                예: 'executive_summary', 'section_generation', etc.
            output_language: 출력 언어 ('ko' or 'en')
            use_cache: 캐시 사용 여부 (기본값: True)

        Returns:
            출력 언어 지시자가 포함된 프롬프트 템플릿 문자열

        Raises:
            FileNotFoundError: 프롬프트 파일이 없는 경우

        Example:
            >>> loader = PromptLoader()
            >>> prompt = loader.load('executive_summary', output_language='ko')
        """
        # 캐시 확인
        cache_key = f"{prompt_name}:{output_language}"
        if use_cache and cache_key in self._cache:
            logger.debug(f"캐시에서 프롬프트 로드: {prompt_name} (output={output_language})")
            return self._cache[cache_key]

        # 프롬프트 파일 로드
        path = os.path.join(self.prompt_dir, f"{prompt_name}_prompt.txt")

        if not os.path.exists(path):
            error_msg = f"프롬프트 파일을 찾을 수 없습니다: {path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        with open(path, 'r', encoding='utf-8') as f:
            base_prompt = f.read()

        # 출력 언어 지시자 추가
        language_instruction = self.LANGUAGE_INSTRUCTIONS.get(output_language, self.LANGUAGE_INSTRUCTIONS['en'])
        full_prompt = base_prompt + language_instruction

        # 캐시 저장
        self._cache[cache_key] = full_prompt
        logger.info(f"프롬프트 로드 성공: {prompt_name} (output={output_language})")

        return full_prompt

    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        logger.info("프롬프트 캐시 초기화 완료")

    def get_supported_prompts(self) -> list:
        """
        지원되는 프롬프트 목록 반환

        Returns:
            프롬프트 이름 리스트 (확장자 제외)
        """
        prompts = []

        if os.path.exists(self.prompt_dir):
            for filename in os.listdir(self.prompt_dir):
                if filename.endswith('_prompt.txt'):
                    prompt_name = filename.replace('_prompt.txt', '')
                    prompts.append(prompt_name)

        logger.debug(f"지원 프롬프트 목록: {prompts}")
        return prompts

    def validate_prompts(self, required_prompts: list) -> Dict[str, bool]:
        """
        필수 프롬프트 존재 여부 검증

        Args:
            required_prompts: 필수 프롬프트 이름 리스트

        Returns:
            {prompt_name: exists} 딕셔너리
        """
        results = {}

        for prompt_name in required_prompts:
            path = os.path.join(self.prompt_dir, f"{prompt_name}_prompt.txt")
            exists = os.path.exists(path)
            results[prompt_name] = exists

        return results

    def __repr__(self):
        return f"PromptLoader(dir={self.prompt_dir})"
