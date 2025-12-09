from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from uuid import UUID
from typing import Optional, List

from src.schemas.additional_data import (
    AdditionalDataUploadRequest,
    AdditionalDataUploadResponse,
    AdditionalDataGetResponse,
    DataCategory,
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
    사이트별 추가 데이터 업로드 (ERD site_additional_data 기준)

    카테고리별로 데이터를 저장합니다:
    - building: 건물 정보 (구조, 연식, 층수 등)
    - asset: 자산 정보 (자산 가치, 면적 등)
    - power: 전력 사용량 정보
    - insurance: 보험 정보
    - custom: 기타 사용자 정의 데이터

    각 사이트에 대해 카테고리별로 하나씩 저장 가능합니다.
    """
    service = AdditionalDataService()
    return await service.upload_additional_data(site_id, request)


@router.get("/{site_id}/additional-data", response_model=AdditionalDataGetResponse)
async def get_additional_data(
    site_id: UUID,
    data_category: Optional[DataCategory] = Query(None, alias="dataCategory", description="조회할 데이터 카테고리"),
    api_key: str = Depends(verify_api_key),
):
    """
    사이트별 추가 데이터 조회 (ERD 기준)

    - dataCategory가 지정되면 해당 카테고리만 조회
    - 미지정 시 전체 카테고리 중 첫 번째 반환
    """
    service = AdditionalDataService()
    result = await service.get_additional_data(site_id, data_category)
    if not result:
        raise HTTPException(status_code=404, detail="Additional data not found")
    return result


@router.get("/{site_id}/additional-data/all", response_model=List[AdditionalDataGetResponse])
async def get_all_additional_data(
    site_id: UUID,
    api_key: str = Depends(verify_api_key),
):
    """사이트의 모든 카테고리 추가 데이터 조회 (ERD 기준)"""
    service = AdditionalDataService()
    results = await service.get_all_additional_data(site_id)
    return results


@router.delete("/{site_id}/additional-data", status_code=204)
async def delete_additional_data(
    site_id: UUID,
    data_category: Optional[DataCategory] = Query(None, alias="dataCategory", description="삭제할 데이터 카테고리"),
    api_key: str = Depends(verify_api_key),
):
    """
    사이트별 추가 데이터 삭제 (ERD 기준)

    - dataCategory가 지정되면 해당 카테고리만 삭제
    - 미지정 시 사이트의 모든 데이터 삭제
    """
    service = AdditionalDataService()
    success = await service.delete_additional_data(site_id, data_category)
    if not success:
        raise HTTPException(status_code=404, detail="Additional data not found")
    return None


@router.post("/{site_id}/additional-data/file", response_model=AdditionalDataUploadResponse, status_code=201)
async def upload_additional_data_file(
    site_id: UUID,
    file: UploadFile = File(..., description="텍스트 파일 (txt, md, csv 등)"),
    data_category: DataCategory = Query(..., alias="dataCategory", description="데이터 카테고리"),
    api_key: str = Depends(verify_api_key),
):
    """
    사이트별 추가 데이터 파일 업로드 (ERD 기준)

    텍스트 파일을 업로드하여 지정된 카테고리의 추가 데이터로 저장합니다.
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
        dataCategory=data_category,
        rawText=text_content,
        fileName=file.filename,
        fileSize=len(contents),
        fileMimeType=file.content_type,
        metadata={'source_file': file.filename}
    )

    return await service.upload_additional_data(site_id, request)
