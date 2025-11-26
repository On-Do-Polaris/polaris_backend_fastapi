# report_generation/utils/markdown_renderer.py
"""
Markdown Renderer Utility
- LangGraph Agent 파이프라인용
- Markdown → HTML / PDF / DOCX / JSON 변환
- 안정적 파일 저장 + 로그 지원
"""

import markdown2
try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from typing import Dict, Any, Optional
import os
import logging
import json
import shutil
import subprocess

logger = logging.getLogger("MarkdownRenderer")
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(ch)
logger.setLevel(logging.INFO)


# ============================================================
# Markdown → HTML 변환
# ============================================================
def render_markdown(md_text: str) -> str:
    """
    Markdown 텍스트를 HTML로 변환
    """
    return markdown2.markdown(md_text)


# ============================================================
# Markdown → PDF 변환
# ============================================================
def export_pdf_from_markdown(md_text: str, output_path: str) -> Optional[str]:
    """
    Markdown → PDF 변환
    - pandoc, pdfkit 등 fallback 지원
    """
    # 1) pdfkit 사용 (if available)
    if PDFKIT_AVAILABLE:
        try:
            html = render_markdown(md_text)
            # wkhtmltopdf 경로 설정 (Windows)
            config = None
            wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
            if os.path.exists(wkhtmltopdf_path):
                config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

            pdfkit.from_string(html, output_path, configuration=config)
            logger.info(f"[PDF] Saved to {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"[PDF] pdfkit 변환 실패: {e}")
    else:
        logger.info(f"[PDF] pdfkit not available, trying pandoc fallback")
    
    # 2) pandoc fallback
    pandoc = shutil.which("pandoc")
    if pandoc:
        tmp_md = output_path + ".tmp.md"
        with open(tmp_md, "w", encoding="utf-8") as f:
            f.write(md_text)
        try:
            subprocess.run([pandoc, tmp_md, "-o", output_path],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            os.remove(tmp_md)
            logger.info(f"[PDF] Saved via pandoc to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"[PDF] pandoc 변환 실패: {e}")
            os.remove(tmp_md)
    return None


# ============================================================
# 단순 텍스트 → DOCX 변환
# ============================================================
def export_docx(text: str, output_path: str) -> Optional[str]:
    try:
        doc = Document()
        doc.add_paragraph(text)
        doc.save(output_path)
        logger.info(f"[DOCX] Saved to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"[DOCX] 변환 실패: {e}")
        return None


# ============================================================
# Dict → JSON 저장
# ============================================================
def export_json(data: Dict[str, Any], output_path: str) -> Optional[str]:
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"[JSON] Saved to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"[JSON] 저장 실패: {e}")
        return None
