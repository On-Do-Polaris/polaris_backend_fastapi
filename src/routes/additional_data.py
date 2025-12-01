from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from uuid import UUID
from typing import Optional

from src.schemas.additional_data import (
    AdditionalDataUploadRequest,
    AdditionalDataUploadResponse,
    AdditionalDataGetResponse,
)
from src.services.additional_data_service import AdditionalDataService
from src.core.auth import verify_api_key

router = APIRouter(prefix="/api/sites", tags=["Additional Data"])


@router.post("/{site_id}/additional-data", response_model=AdditionalDataUploadResponse, status_code=201)
async def upload_additional_data(
    site_id: UUID,
    request: AdditionalDataUploadRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    사이트별 추가 데이터 업로드

    사용자가 제공하는 자유 형식 텍스트 데이터를 저장합니다.
    이 데이터는 AI Agent의 분석 시 컨텍스트로 활용됩니다.

    예시:
    - 건물의 특수한 상황 설명
    - 과거 재난 경험
    - 내부 대응 계획
    - 기타 참고 사항
    """
    service = AdditionalDataService()
    return await service.upload_additional_data(site_id, request)


@router.get("/{site_id}/additional-data", response_model=AdditionalDataGetResponse)
async def get_additional_data(
    site_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """사이트별 추가 데이터 조회"""
    service = AdditionalDataService()
    result = await service.get_additional_data(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="Additional data not found")
    return result


@router.delete("/{site_id}/additional-data", status_code=204)
async def delete_additional_data(
    site_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """사이트별 추가 데이터 삭제"""
    service = AdditionalDataService()
    success = await service.delete_additional_data(site_id)
    if not success:
        raise HTTPException(status_code=404, detail="Additional data not found")
    return None


@router.post("/{site_id}/additional-data/file", response_model=AdditionalDataUploadResponse, status_code=201)
async def upload_additional_data_file(
    site_id: UUID,
    file: UploadFile = File(..., description="텍스트 파일 (txt, md, csv 등)"),
    api_key: str = Depends(verify_api_key),
):
    """
    사이트별 추가 데이터 파일 업로드

    텍스트 파일을 업로드하여 추가 데이터로 저장합니다.
    """
    # 파일 확장자 체크
    allowed_extensions = ['.txt', '.md', '.csv', '.json']
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''

    if f'.{file_ext}' not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # 파일 크기 체크 (최대 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    # 텍스트 디코딩
    try:
        text_content = contents.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text_content = contents.decode('cp949')  # Windows 한글 인코딩
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Unable to decode file. Please use UTF-8 or CP949 encoding")

    service = AdditionalDataService()
    request = AdditionalDataUploadRequest(
        raw_text=text_content,
        metadata={'source_file': file.filename}
    )

    return await service.upload_additional_data(site_id, request)
