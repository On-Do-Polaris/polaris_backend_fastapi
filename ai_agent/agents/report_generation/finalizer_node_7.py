# finalizer_node_7.py
"""
파일명: finalizer_node_7.py
버전: v03
최종 수정일: 2025-11-24

개요:
    - LangGraph 멀티에이전트 파이프라인 최종 단계 Finalizer Node
    - RefinerAgent에서 전달받은 refined_markdown / refined_json 저장
    - RAG/Research Agent 기반 citations_final 저장
    - Markdown / JSON / PDF 파일 생성
    - DB 또는 로컬 로그 저장
    - 반복 파이프라인 대응 및 export_formats 선택 가능

주요 기능:
    1. Markdown, JSON, PDF 최종 저장
    2. citations 최종 파일 저장
    3. DB 또는 fallback 로컬 로그 저장
    4. 파일명, 버전, 시설 기반 구조화된 저장
    5. 예외 처리 및 상태(status) 명확화

변경 이력:
    - v01 (2025-11-14): 초안 작성
        * Markdown/JSON 저장 skeleton
        * citations 저장 구조 반영
    - v02 (2025-11-21): async 루프 반영 전
        * PDF 생성 및 fallback 로직 추가
        * DB 연결 및 로컬 로그 fallback 구조 추가
        * export_formats 지원
    - v03 (2025-11-24, 최신):
        * metadata 기반 파일명/디렉토리 구조 개선
        * DB 저장 시 inserted_primary_key 추출
        * 최종 Output 경로 및 citations JSON 포함
        * 예외 처리 강화, 상태(status) 명확화
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import os
import json
import logging
from datetime import datetime
import subprocess
import shutil

logger = logging.getLogger("FinalizerNode")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(ch)


# ----------------------------
# 기본 저장 경로
# ----------------------------
OUTPUT_DIR = os.environ.get("REPORT_OUTPUT_DIR", "report_outputs")
DB_CONNECTION_URI = os.environ.get("REPORT_DB_URI", "")


# ----------------------------
# Pydantic I/O Schemas
# ----------------------------
class FinalizerInput(BaseModel):
    """
    RefinerAgent → FinalizerNode 입력 구조
    """
    refined_markdown: str
    refined_json: Dict[str, Any]
    citations_final: List[str]
    validation_result: Dict[str, Any]
    metadata: Dict[str, Any]
    export_formats: Optional[List[str]] = ["json", "md", "pdf"]


class FinalizerOutput(BaseModel):
    md_path: Optional[str] = None
    json_path: Optional[str] = None
    pdf_path: Optional[str] = None
    db_log_id: Optional[int] = None
    status: str = "completed"
    details: Dict[str, Any] = {}


# ----------------------------
# Helper functions
# ----------------------------
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def safe_write_text(path: str, text: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def safe_write_json(path: str, obj: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def try_generate_pdf_from_markdown(md_path: str, pdf_path: str) -> bool:
    pandoc = shutil.which("pandoc")
    if pandoc:
        try:
            subprocess.run([pandoc, md_path, "-o", pdf_path],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("PDF generated with pandoc.")
            return True
        except Exception:
            pass
        try:
            subprocess.run([pandoc, md_path, "-o", pdf_path, "--pdf-engine=xelatex"],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("PDF generated with pandoc + xelatex.")
            return True
        except Exception:
            pass
    logger.info("PDF generation skipped (no tool available).")
    return False


def save_db_log(metadata: Dict[str, Any], paths: Dict[str, Optional[str]], validation: Dict[str, Any]):
    if not DB_CONNECTION_URI:
        fallback_dir = os.path.join(OUTPUT_DIR, "logs")
        ensure_dir(fallback_dir)
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        log_path = os.path.join(fallback_dir, f"log_{metadata.get('report_name','report')}_{stamp}.json")
        safe_write_json(log_path, {
            "metadata": metadata,
            "paths": paths,
            "validation": validation,
            "created_at": datetime.utcnow().isoformat()
        })
        return None
    try:
        from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Text, DateTime
        engine = create_engine(DB_CONNECTION_URI)
        meta = MetaData()
        logs = Table(
            "report_generation_logs", meta,
            Column("id", Integer, primary_key=True),
            Column("report_name", String(255)),
            Column("version", String(64)),
            Column("facility", String(128)),
            Column("md_path", String(1024)),
            Column("json_path", String(1024)),
            Column("pdf_path", String(1024)),
            Column("validation_json", Text),
            Column("created_at", DateTime)
        )
        meta.create_all(engine)
        ins = logs.insert().values(
            report_name=metadata.get("report_name"),
            version=metadata.get("version"),
            facility=metadata.get("facility"),
            md_path=paths.get("md"),
            json_path=paths.get("json"),
            pdf_path=paths.get("pdf"),
            validation_json=json.dumps(validation, ensure_ascii=False),
            created_at=datetime.utcnow()
        )
        conn = engine.connect()
        result = conn.execute(ins)
        conn.close()
        return int(result.inserted_primary_key[0])
    except:
        return None


# ----------------------------
# FinalizerNode main class
# ----------------------------
class FinalizerNode:
    def __init__(self):
        ensure_dir(OUTPUT_DIR)
        logger.info("FinalizerNode initialized.")

    def run(self, input_data: FinalizerInput) -> FinalizerOutput:
        logger.info("FinalizerNode started.")
        try:
            stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            report_name = input_data.metadata.get("report_name", f"report_{stamp}")
            version = input_data.metadata.get("version", "v0")
            facility = input_data.metadata.get("facility", "unknown")
            base_name = f"{facility}_physical_risk_{version}_{stamp}"
            out_dir = os.path.join(OUTPUT_DIR, base_name)
            ensure_dir(out_dir)

            # Save Markdown
            md_path = os.path.join(out_dir, f"{base_name}.md")
            safe_write_text(md_path, input_data.refined_markdown)

            # Save JSON
            json_path = os.path.join(out_dir, f"{base_name}.json")
            final_payload = {
                "metadata": input_data.metadata,
                "report_json": input_data.refined_json,
                "citations": input_data.citations_final,
                "validation": input_data.validation_result,
                "generated_at": datetime.utcnow().isoformat()
            }
            safe_write_json(json_path, final_payload)

            # PDF
            pdf_path = None
            if "pdf" in input_data.export_formats:
                pdf_path = os.path.join(out_dir, f"{base_name}.pdf")
                pdf_created = try_generate_pdf_from_markdown(md_path, pdf_path)
                if not pdf_created:
                    pdf_path = None

            # citations JSON
            citations_path = os.path.join(out_dir, f"{base_name}_citations.json")
            safe_write_json(citations_path, {"citations": input_data.citations_final})

            # DB log
            paths = {"md": md_path, "json": json_path, "pdf": pdf_path}
            db_id = save_db_log(input_data.metadata, paths, input_data.validation_result)

            return FinalizerOutput(
                md_path=md_path,
                json_path=json_path,
                pdf_path=pdf_path,
                db_log_id=db_id,
                status="completed",
                details={
                    "md": md_path,
                    "json": json_path,
                    "pdf": pdf_path,
                    "citations_json": citations_path,
                    "db_log_id": db_id
                }
            )
        except Exception as e:
            logger.exception("FinalizerNode failed.")
            return FinalizerOutput(
                status="failed",
                details={"error": str(e)}
            )
