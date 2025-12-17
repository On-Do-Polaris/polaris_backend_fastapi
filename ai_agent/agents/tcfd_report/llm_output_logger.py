"""
LLM Output Logger for TCFD Report Generation
LLM 출력을 개별 파일로 저장하여 품질 검토를 용이하게 함

생성 파일 구조:
    llm_outputs/
    ├── {timestamp}/
    │   ├── node_2a_scenario_analysis.md
    │   ├── node_2b_impact_risk_1_extreme_heat.md
    │   ├── node_2b_impact_risk_2_typhoon.md
    │   ├── ...
    │   ├── node_2c_mitigation_risk_1_extreme_heat.md
    │   ├── node_2c_mitigation_risk_2_typhoon.md
    │   ├── ...
    │   ├── node_3_executive_summary.md
    │   └── _summary.json
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

# 싱글톤 인스턴스
_logger_instance = None


class LLMOutputLogger:
    """LLM 출력 로거"""

    def __init__(self, base_dir: str = None):
        """
        초기화

        Args:
            base_dir: 출력 디렉토리 기본 경로
        """
        if base_dir is None:
            # 기본 경로: ai_agent/agents/tcfd_report/llm_outputs/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.join(current_dir, "llm_outputs")

        self.base_dir = base_dir
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(base_dir, self.session_id)
        self.outputs = {}
        self.enabled = True

        # 디렉토리 생성
        os.makedirs(self.session_dir, exist_ok=True)
        print(f"📁 LLM Output Logger 초기화: {self.session_dir}")

    def log_output(
        self,
        node_name: str,
        output_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        risk_type: Optional[str] = None,
        risk_rank: Optional[int] = None
    ) -> str:
        """
        LLM 출력 저장

        Args:
            node_name: 노드 이름 (예: "node_2a", "node_2b", "node_2c", "node_3")
            output_type: 출력 유형 (예: "scenario_analysis", "impact", "mitigation", "executive_summary")
            content: LLM 출력 텍스트
            metadata: 추가 메타데이터
            risk_type: 리스크 유형 (node_2b, node_2c용)
            risk_rank: 리스크 순위 (node_2b, node_2c용)

        Returns:
            str: 저장된 파일 경로
        """
        if not self.enabled:
            return ""

        # 파일명 생성
        if risk_type and risk_rank:
            filename = f"{node_name}_{output_type}_risk_{risk_rank}_{risk_type}.md"
        else:
            filename = f"{node_name}_{output_type}.md"

        filepath = os.path.join(self.session_dir, filename)

        # 파일 내용 작성
        file_content = self._format_output(
            node_name=node_name,
            output_type=output_type,
            content=content,
            metadata=metadata,
            risk_type=risk_type,
            risk_rank=risk_rank
        )

        # 파일 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)

        # 출력 기록
        key = filename.replace('.md', '')
        self.outputs[key] = {
            "filepath": filepath,
            "node_name": node_name,
            "output_type": output_type,
            "risk_type": risk_type,
            "risk_rank": risk_rank,
            "content_length": len(content),
            "timestamp": datetime.now().isoformat()
        }

        print(f"  📝 LLM 출력 저장: {filename} ({len(content)} chars)")

        return filepath

    def _format_output(
        self,
        node_name: str,
        output_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        risk_type: Optional[str] = None,
        risk_rank: Optional[int] = None
    ) -> str:
        """출력 파일 포맷팅"""
        lines = []

        # 헤더
        lines.append(f"# LLM Output: {node_name.upper()} - {output_type}")
        lines.append("")
        lines.append(f"**생성 시각**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**세션 ID**: {self.session_id}")

        if risk_type:
            lines.append(f"**리스크 유형**: {risk_type}")
        if risk_rank:
            lines.append(f"**리스크 순위**: P{risk_rank}")

        lines.append(f"**문자 수**: {len(content)}")
        lines.append("")

        # 메타데이터
        if metadata:
            lines.append("## Metadata")
            lines.append("```json")
            lines.append(json.dumps(metadata, indent=2, ensure_ascii=False))
            lines.append("```")
            lines.append("")

        # LLM 출력 내용
        lines.append("---")
        lines.append("")
        lines.append("## LLM Output")
        lines.append("")
        lines.append(content)

        return "\n".join(lines)

    def save_summary(self):
        """세션 요약 저장"""
        summary = {
            "session_id": self.session_id,
            "session_dir": self.session_dir,
            "total_outputs": len(self.outputs),
            "outputs": self.outputs,
            "generated_at": datetime.now().isoformat()
        }

        # 노드별 통계
        node_stats = {}
        for key, info in self.outputs.items():
            node = info["node_name"]
            if node not in node_stats:
                node_stats[node] = {"count": 0, "total_chars": 0}
            node_stats[node]["count"] += 1
            node_stats[node]["total_chars"] += info["content_length"]

        summary["node_stats"] = node_stats

        # 요약 파일 저장
        summary_path = os.path.join(self.session_dir, "_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n📊 LLM Output 요약 저장: {summary_path}")
        print(f"   총 {len(self.outputs)}개 출력물")
        for node, stats in node_stats.items():
            print(f"   - {node}: {stats['count']}개 ({stats['total_chars']:,} chars)")

        return summary_path

    def get_session_dir(self) -> str:
        """현재 세션 디렉토리 반환"""
        return self.session_dir


def get_logger(base_dir: str = None) -> LLMOutputLogger:
    """
    LLM Output Logger 싱글톤 인스턴스 반환

    Args:
        base_dir: 출력 디렉토리 기본 경로 (최초 호출 시만 사용)

    Returns:
        LLMOutputLogger: 로거 인스턴스
    """
    global _logger_instance

    if _logger_instance is None:
        _logger_instance = LLMOutputLogger(base_dir)

    return _logger_instance


def reset_logger():
    """로거 인스턴스 초기화 (새 세션 시작)"""
    global _logger_instance
    _logger_instance = None
