# finalizer_node_7.py
"""
파일명: finalizer_node_7.py
버전: v04
최종 수정일: 2025-11-24

개요:
    - LangGraph 기반 멀티에이전트 파이프라인의 마지막 단계 Finalizer Node
    - Validation/Refiner 단계를 통과한 "최종 Markdown / JSON / Citations"를 받아
      파일 저장 + PDF 변환 + DB 로그 + 최종 산출물 패키징 수행
    - 실패 시에도 경로/로그를 남기도록 설계된 안정형 Node

주요 기능:
    1. Markdown, JSON, PDF, Citations JSON 최종 저장
    2. metadata 기반 구조 폴더 자동 생성
    3. DB 또는 로컬 JSON 로그 저장 (fallback 지원)
    4. export_formats=["md","json","pdf"] 제어
    5. 전처리/예외 처리 일원화로 안정성 개선

변경 이력:
    - v01 (2025-11-14): 저장 스켈레톤 작성
    - v02 (2025-11-21): DB + PDF 변환 추가
    - v03 (2025-11-24): metadata 기반 파일명 구조 개선
    - v04 (2025-11-24): 안정성/예외 처리/경로 구조 개선 및 운영 버전 완성
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


# =========================================
# 환경 설정
# =========================================
OUTPUT_DIR = os.environ.get("REPORT_OUTPUT_DIR", "report_outputs")
DB_CONNECTION_URI = os.environ.get("REPORT_DB_URI", "")


# =========================================
# Pydantic Schemas
# =========================================
class FinalizerInput(BaseModel):
    """RefinerAgent → FinalizerNode 입력"""
    refined_markdown: str
    refined_json: Dict[str, Any]
    citations_final: List[str]
    validation_result: Dict[str, Any]
    metadata: Dict[str, Any]
    export_formats: Optional[List[str]] = ["md", "json", "pdf"]


class FinalizerOutput(BaseModel):
    md_path: Optional[str] = None
    json_path: Optional[str] = None
    pdf_path: Optional[str] = None
    db_log_id: Optional[int] = None
    status: str = "completed"
    details: Dict[str, Any] = {}


# =========================================
# Helper functions
# =========================================
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def safe_write_text(path: str, text: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def safe_write_json(path: str, obj: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def try_generate_pdf_from_markdown(md_path: str, pdf_path: str) -> bool:
    """
    pandoc 또는 xelatex가 있을 경우 PDF 생성 시도.
    둘 다 없어도 장애가 발생하지 않고 False 반환.
    """
    pandoc = shutil.which("pandoc")
    if not pandoc:
        logger.info("Pandoc not found → PDF 생성 건너뜀.")
        return False

    for args in [
        [pandoc, md_path, "-o", pdf_path],
        [pandoc, md_path, "-o", pdf_path, "--pdf-engine=xelatex"]
    ]:
        try:
            subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"PDF 생성 성공: {' '.join(args)}")
            return True
        except Exception:
            continue

    logger.warning("PDF 변환 실패 → PDF 스킵.")
    return False


def save_db_log(metadata: Dict[str, Any], paths: Dict[str, Optional[str]], validation: Dict[str, Any]):
    """
    DB 연결 실패 시 자동 fallback → 로컬 logs 디렉토리에 JSON 저장.
    """
    if not DB_CONNECTION_URI:
        return _save_local_log(metadata, paths, validation)

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
            Column("created_at", DateTime),
        )

        meta.create_all(engine)
        conn = engine.connect()

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
        result = conn.execute(ins)
        conn.close()

        return int(result.inserted_primary_key[0])

    except Exception:
        logger.warning("DB 저장 실패 → 로컬 로그로 fallback.")
        return _save_local_log(metadata, paths, validation)


def _save_local_log(metadata, paths, validation):
    fallback_dir = os.path.join(OUTPUT_DIR, "logs")
    ensure_dir(fallback_dir)

    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"log_{metadata.get('report_name','report')}_{stamp}.json"
    log_path = os.path.join(fallback_dir, filename)

    safe_write_json(log_path, {
        "metadata": metadata,
        "paths": paths,
        "validation": validation,
        "created_at": datetime.utcnow().isoformat()
    })

    logger.info(f"로컬 로그 저장: {log_path}")
    return None


# =========================================
# FinalizerNode
# =========================================
class FinalizerNode:
    def __init__(self):
        ensure_dir(OUTPUT_DIR)
        logger.info("FinalizerNode initialized.")

    def run(self, input_data: FinalizerInput) -> FinalizerOutput:
        logger.info("FinalizerNode 실행 시작.")

        try:
            # -------------------------
            # 파일명 및 디렉토리 구조 생성
            # -------------------------
            stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            report_name = input_data.metadata.get("report_name", f"report_{stamp}")
            version = input_data.metadata.get("version", "v0")
            facility = input_data.metadata.get("facility", "unknown")

            base_name = f"{facility}_physical_risk_{version}_{stamp}"
            out_dir = os.path.join(OUTPUT_DIR, base_name)
            ensure_dir(out_dir)

            # -------------------------
            # 1) Markdown 저장
            # -------------------------
            md_path = os.path.join(out_dir, f"{base_name}.md")
            safe_write_text(md_path, input_data.refined_markdown)

            # -------------------------
            # 2) JSON 저장
            # -------------------------
            json_path = os.path.join(out_dir, f"{base_name}.json")
            final_payload = {
                "metadata": input_data.metadata,
                "report_json": input_data.refined_json,
                "citations": input_data.citations_final,
                "validation": input_data.validation_result,
                "generated_at": datetime.utcnow().isoformat()
            }
            safe_write_json(json_path, final_payload)

            # -------------------------
            # 3) PDF 생성
            # -------------------------
            pdf_path = None
            if "pdf" in (input_data.export_formats or []):
                pdf_path = os.path.join(out_dir, f"{base_name}.pdf")
                if not try_generate_pdf_from_markdown(md_path, pdf_path):
                    pdf_path = None

            # -------------------------
            # 4) citations JSON 저장
            # -------------------------
            citations_path = os.path.join(out_dir, f"{base_name}_citations.json")
            safe_write_json(citations_path, {"citations": input_data.citations_final})

            # -------------------------
            # 5) DB / 로컬 로그
            # -------------------------
            paths = {"md": md_path, "json": json_path, "pdf": pdf_path}
            db_id = save_db_log(input_data.metadata, paths, input_data.validation_result)

            # -------------------------
            # 최종 Output
            # -------------------------
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
            logger.exception("FinalizerNode 실패.")
            return FinalizerOutput(
                status="failed",
                details={"error": str(e)}
            )
