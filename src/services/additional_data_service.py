from uuid import UUID, uuid4
from typing import Optional, List
from datetime import datetime

from src.schemas.additional_data import (
    AdditionalDataUploadRequest,
    AdditionalDataUploadResponse,
    AdditionalDataGetResponse,
    DataCategory,
)


class AdditionalDataService:
    """추가 데이터 관리 서비스 (ERD site_additional_data 테이블 기준)"""

    def __init__(self):
        """서비스 초기화"""
        # 실제 구현에서는 DB 사용
        # 현재는 메모리 캐시로 간단 구현 (site_id + data_category를 키로 사용)
        self._data_store = {}  # Key: (site_id, data_category), Value: record

    async def upload_additional_data(
        self,
        site_id: UUID,
        request: AdditionalDataUploadRequest,
        uploaded_by: Optional[UUID] = None
    ) -> AdditionalDataUploadResponse:
        """추가 데이터 업로드 (ERD 기준)"""
        now = datetime.now()
        record_id = uuid4()

        # 복합 키 생성 (site_id + data_category는 unique)
        key = (site_id, request.data_category)

        # 데이터 저장
        self._data_store[key] = {
            'id': record_id,
            'site_id': site_id,
            'data_category': request.data_category,
            'raw_text': request.raw_text,
            'structured_data': request.structured_data,
            'metadata': request.metadata or {},
            'file_name': request.file_name,
            'file_s3_key': request.file_s3_key,
            'file_size': request.file_size,
            'file_mime_type': request.file_mime_type,
            'uploaded_by': uploaded_by,
            'uploaded_at': now,
            'expires_at': request.expires_at,
        }

        return AdditionalDataUploadResponse(
            id=record_id,
            siteId=site_id,
            dataCategory=request.data_category,
            uploadedAt=now,
            message="Additional data uploaded successfully"
        )

    async def get_additional_data(
        self,
        site_id: UUID,
        data_category: Optional[DataCategory] = None
    ) -> Optional[AdditionalDataGetResponse]:
        """추가 데이터 조회 (ERD 기준)"""
        if data_category:
            # 특정 카테고리만 조회
            key = (site_id, data_category)
            data = self._data_store.get(key)
            if not data:
                return None

            return AdditionalDataGetResponse(
                id=data['id'],
                siteId=site_id,
                dataCategory=data['data_category'],
                rawText=data.get('raw_text'),
                structuredData=data.get('structured_data'),
                metadata=data.get('metadata'),
                fileName=data.get('file_name'),
                fileS3Key=data.get('file_s3_key'),
                fileSize=data.get('file_size'),
                fileMimeType=data.get('file_mime_type'),
                uploadedBy=data.get('uploaded_by'),
                uploadedAt=data['uploaded_at'],
                expiresAt=data.get('expires_at'),
            )
        else:
            # 전체 카테고리 중 첫 번째 반환 (backwards compatibility)
            for key, data in self._data_store.items():
                if key[0] == site_id:
                    return AdditionalDataGetResponse(
                        id=data['id'],
                        siteId=site_id,
                        dataCategory=data['data_category'],
                        rawText=data.get('raw_text'),
                        structuredData=data.get('structured_data'),
                        metadata=data.get('metadata'),
                        fileName=data.get('file_name'),
                        fileS3Key=data.get('file_s3_key'),
                        fileSize=data.get('file_size'),
                        fileMimeType=data.get('file_mime_type'),
                        uploadedBy=data.get('uploaded_by'),
                        uploadedAt=data['uploaded_at'],
                        expiresAt=data.get('expires_at'),
                    )
            return None

    async def get_all_additional_data(
        self,
        site_id: UUID
    ) -> List[AdditionalDataGetResponse]:
        """사업장의 모든 카테고리 추가 데이터 조회"""
        results = []
        for key, data in self._data_store.items():
            if key[0] == site_id:
                results.append(AdditionalDataGetResponse(
                    id=data['id'],
                    siteId=site_id,
                    dataCategory=data['data_category'],
                    rawText=data.get('raw_text'),
                    structuredData=data.get('structured_data'),
                    metadata=data.get('metadata'),
                    fileName=data.get('file_name'),
                    fileS3Key=data.get('file_s3_key'),
                    fileSize=data.get('file_size'),
                    fileMimeType=data.get('file_mime_type'),
                    uploadedBy=data.get('uploaded_by'),
                    uploadedAt=data['uploaded_at'],
                    expiresAt=data.get('expires_at'),
                ))
        return results

    async def delete_additional_data(
        self,
        site_id: UUID,
        data_category: Optional[DataCategory] = None
    ) -> bool:
        """추가 데이터 삭제 (ERD 기준)"""
        if data_category:
            # 특정 카테고리만 삭제
            key = (site_id, data_category)
            if key in self._data_store:
                del self._data_store[key]
                return True
            return False
        else:
            # 사업장의 모든 데이터 삭제
            keys_to_delete = [key for key in self._data_store.keys() if key[0] == site_id]
            if keys_to_delete:
                for key in keys_to_delete:
                    del self._data_store[key]
                return True
            return False

    async def get_additional_data_dict(
        self,
        site_id: UUID
    ) -> Optional[dict]:
        """
        추가 데이터를 dict 형태로 반환 (AI Agent 전달용)
        모든 카테고리 데이터를 통합
        """
        all_data = await self.get_all_additional_data(site_id)

        if not all_data:
            return None

        # 카테고리별로 정리
        result = {
            'raw_text': '',
            'metadata': {},
            'building_info': None,
            'asset_info': None,
            'power_usage': None,
            'insurance': None,
        }

        for data in all_data:
            # raw_text 통합
            if data.raw_text:
                result['raw_text'] += f"\n[{data.data_category}]\n{data.raw_text}"

            # metadata 통합
            if data.metadata:
                result['metadata'][data.data_category] = data.metadata

            # structured_data를 카테고리별로 매핑
            if data.structured_data:
                if data.data_category == DataCategory.BUILDING:
                    result['building_info'] = data.structured_data
                elif data.data_category == DataCategory.ASSET:
                    result['asset_info'] = data.structured_data
                elif data.data_category == DataCategory.POWER:
                    result['power_usage'] = data.structured_data
                elif data.data_category == DataCategory.INSURANCE:
                    result['insurance'] = data.structured_data

        return result
