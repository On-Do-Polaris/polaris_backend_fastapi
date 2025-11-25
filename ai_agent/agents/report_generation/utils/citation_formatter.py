# report_generation/utils/citation_formatter.py
"""
Citation Formatter Utility
- LangGraph Agent 파이프라인용
- Markdown inline, reference list 생성
- JSON citations 연동 가능
"""

from typing import List, Dict, Optional

# ============================================================
# Inline citation 추가
# ============================================================
def format_citations_inline(text: str, citations: Optional[List[str]] = None) -> str:
    """
    텍스트에 inline citation을 추가 (Markdown 스타일)
    
    Args:
        text: 원본문
        citations: citation 문자열 리스트
    
    Returns:
        text + inline citation 문자열
        예: "기후 리스크 분석 결과는 심각합니다 [1] [2]"
    """
    if not citations:
        return text

    citation_str = " ".join([f"[{i+1}]" for i in range(len(citations))])
    return f"{text} {citation_str}"


# ============================================================
# Markdown reference list 생성
# ============================================================
def format_references(citations: Optional[List[str]] = None) -> str:
    """
    Citation 리스트를 Markdown 참고문헌 목록으로 변환
    
    Args:
        citations: citation 문자열 리스트
    
    Returns:
        Markdown reference string
        예:
        [1] 논문 제목1
        [2] 보고서 제목2
    """
    if not citations:
        return ""
    return "\n".join([f"[{i+1}] {c}" for i, c in enumerate(citations)])


# ============================================================
# JSON citations 객체 변환
# ============================================================
def citations_to_json(citations: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    Citation 리스트를 JSON 객체로 변환
    [{ "id": "ref-1", "text": "..."}]
    
    Args:
        citations: citation 문자열 리스트
    
    Returns:
        List[Dict]: JSON-friendly citation list
    """
    if not citations:
        return []
    return [{"id": f"ref-{i+1}", "text": c} for i, c in enumerate(citations)]


# ============================================================
# 모든 citations 수집 (Finalizer용 통합)
# ============================================================
def collect_all(text: str = "", citations: Optional[List[str]] = None) -> List[str]:
    """
    Finalizer / Refiner에서 호출용
    - 기존 text에서 inline 추출 + citations 합치기
    """
    collected = []
    if citations:
        collected.extend(citations)
    # TODO: text에서 [[ref-id]] 형식 파싱 가능
    return collected
