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

router = APIRouter(prefix="/api/additional-data", tags=["Additional Data"])


@router.post(
    "",
    response_model=AdditionalDataUploadResponse,
    status_code=201,
    responses={
        201: {"description": "추가 데이터가 성공적으로 업로드됨"},
        401: {"description": "API Key 인증 실패"},
        422: {"description": "입력 데이터 검증 실패"}
    }
)
async def upload_additional_data(
    request: AdditionalDataUploadRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    추가 데이터 업로드 - siteId는 request body에 포함

    카테고리별로 데이터를 저장합니다:
    - building: 건물 정보
    - asset: 자산 정보
    - power: 전력 사용량 정보
    - insurance: 보험 정보
    - custom: 기타 사용자 정의 데이터
    """
    service = AdditionalDataService()
    return await service.upload_additional_data(request.site_id, request)


@router.get(
    "",
    response_model=AdditionalDataGetResponse,
    responses={
        200: {"description": "추가 데이터 조회 성공"},
        404: {
            "description": "추가 데이터를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {"detail": "Additional data not found"}
                }
            }
        },
        401: {"description": "API Key 인증 실패"},
        422: {"description": "입력 데이터 검증 실패"}
    }
)
async def get_additional_data(
    site_id: UUID = Query(..., alias="siteId"),
    data_category: Optional[DataCategory] = Query(None, alias="dataCategory"),
    api_key: str = Depends(verify_api_key),
):
    """추가 데이터 조회 - query parameters 사용"""
    service = AdditionalDataService()
    result = await service.get_additional_data(site_id, data_category)
    if not result:
        raise HTTPException(status_code=404, detail="Additional data not found")
    return result


@router.get(
    "/all",
    response_model=List[AdditionalDataGetResponse],
    responses={
        200: {"description": "모든 추가 데이터 조회 성공"},
        401: {"description": "API Key 인증 실패"},
        422: {"description": "입력 데이터 검증 실패"}
    }
)
async def get_all_additional_data(
    site_id: UUID = Query(..., alias="siteId"),
    api_key: str = Depends(verify_api_key),
):
    """모든 카테고리 추가 데이터 조회 - query parameters 사용"""
    service = AdditionalDataService()
    results = await service.get_all_additional_data(site_id)
    return results


@router.delete(
    "",
    status_code=204,
    responses={
        204: {"description": "추가 데이터가 성공적으로 삭제됨"},
        404: {
            "description": "추가 데이터를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {"detail": "Additional data not found"}
                }
            }
        },
        401: {"description": "API Key 인증 실패"},
        422: {"description": "입력 데이터 검증 실패"}
    }
)
async def delete_additional_data(
    site_id: UUID = Query(..., alias="siteId"),
    data_category: Optional[DataCategory] = Query(None, alias="dataCategory"),
    api_key: str = Depends(verify_api_key),
):
    """추가 데이터 삭제 - query parameters 사용"""
    service = AdditionalDataService()
    success = await service.delete_additional_data(site_id, data_category)
    if not success:
        raise HTTPException(status_code=404, detail="Additional data not found")
    return None


@router.post(
    "/file",
    response_model=AdditionalDataUploadResponse,
    status_code=201,
    responses={
        201: {"description": "파일이 성공적으로 업로드됨"},
        400: {
            "description": "잘못된 요청",
            "content": {
                "application/json": {
                    "examples": {
                        "unsupported_file": {
                            "value": {"detail": "Unsupported file type. Allowed: .txt, .md, .csv, .json"}
                        },
                        "file_too_large": {
                            "value": {"detail": "File size exceeds 10MB limit"}
                        },
                        "encoding_error": {
                            "value": {"detail": "Unable to decode file. Please use UTF-8 or CP949 encoding"}
                        }
                    }
                }
            }
        },
        401: {"description": "API Key 인증 실패"},
        422: {"description": "입력 데이터 검증 실패"}
    }
)
async def upload_additional_data_file(
    site_id: UUID = Query(..., alias="siteId"),
    file: UploadFile = File(...),
    data_category: DataCategory = Query(..., alias="dataCategory"),
    api_key: str = Depends(verify_api_key),
):
    """추가 데이터 파일 업로드 - query parameters로 siteId, dataCategory 전달"""
    # 파일 확장자 체크
    allowed_extensions = ['.txt', '.md', '.csv', '.json']
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''

    if f'.{file_ext}' not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # 파일 크기 체크 (최대 10MB)
    max_size = 10 * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    # 텍스트 디코딩
    try:
        text_content = contents.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text_content = contents.decode('cp949')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Unable to decode file. Please use UTF-8 or CP949 encoding")

    service = AdditionalDataService()
    request = AdditionalDataUploadRequest(
        siteId=site_id,
        dataCategory=data_category,
        rawText=text_content,
        fileName=file.filename,
        fileSize=len(contents),
        fileMimeType=file.content_type,
        metadata={'source_file': file.filename}
    )

    return await service.upload_additional_data(site_id, request)
