from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class AdditionalDataUploadRequest(BaseModel):
    """추가 데이터 업로드 요청"""
    raw_text: str = Field(..., alias="rawText", description="자유 형식 텍스트")
    metadata: Optional[dict] = Field(None, description="메타데이터 (선택)")

    class Config:
        populate_by_name = True


class AdditionalDataUploadResponse(BaseModel):
    """추가 데이터 업로드 응답"""
    site_id: UUID = Field(..., alias="siteId")
    uploaded_at: datetime = Field(..., alias="uploadedAt")
    text_length: int = Field(..., alias="textLength", description="텍스트 길이 (문자 수)")
    message: str = Field(default="Additional data uploaded successfully")

    class Config:
        populate_by_name = True


class AdditionalDataGetResponse(BaseModel):
    """추가 데이터 조회 응답"""
    site_id: UUID = Field(..., alias="siteId")
    raw_text: str = Field(..., alias="rawText")
    metadata: Optional[dict] = None
    uploaded_at: datetime = Field(..., alias="uploadedAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    class Config:
        populate_by_name = True
