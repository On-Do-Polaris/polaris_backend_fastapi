from uuid import UUID
from typing import Optional
from datetime import datetime

from src.schemas.additional_data import (
    AdditionalDataUploadRequest,
    AdditionalDataUploadResponse,
    AdditionalDataGetResponse,
)


class AdditionalDataService:
    """추가 데이터 관리 서비스"""

    def __init__(self):
        """서비스 초기화"""
        # 실제 구현에서는 DB 사용
        # 현재는 메모리 캐시로 간단 구현
        self._data_store = {}

    async def upload_additional_data(
        self,
        site_id: UUID,
        request: AdditionalDataUploadRequest
    ) -> AdditionalDataUploadResponse:
        """추가 데이터 업로드"""
        now = datetime.now()

        # 데이터 저장
        self._data_store[site_id] = {
            'raw_text': request.raw_text,
            'metadata': request.metadata or {},
            'uploaded_at': now,
            'updated_at': now,
        }

        return AdditionalDataUploadResponse(
            siteId=site_id,
            uploadedAt=now,
            textLength=len(request.raw_text),
            message="Additional data uploaded successfully"
        )

    async def get_additional_data(
        self,
        site_id: UUID
    ) -> Optional[AdditionalDataGetResponse]:
        """추가 데이터 조회"""
        data = self._data_store.get(site_id)

        if not data:
            return None

        return AdditionalDataGetResponse(
            siteId=site_id,
            rawText=data['raw_text'],
            metadata=data.get('metadata'),
            uploadedAt=data['uploaded_at'],
            updatedAt=data.get('updated_at'),
        )

    async def delete_additional_data(self, site_id: UUID) -> bool:
        """추가 데이터 삭제"""
        if site_id in self._data_store:
            del self._data_store[site_id]
            return True
        return False

    async def get_additional_data_dict(self, site_id: UUID) -> Optional[dict]:
        """
        추가 데이터를 dict 형태로 반환
        (AI Agent 전달용)
        """
        data = self._data_store.get(site_id)

        if not data:
            return None

        return {
            'raw_text': data['raw_text'],
            'metadata': data.get('metadata', {})
        }
