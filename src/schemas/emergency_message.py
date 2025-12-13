from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class EmergencyMessage(BaseModel):
    """긴급재난문자 레코드 (ERD api_emergency_messages 테이블 기준)"""
    id: int = Field(..., description="PK, 고유 식별자")
    alert_date: date = Field(..., alias="alertDate", description="재난문자 발령 일자 (YYYY-MM-DD)")
    disaster_type: str = Field(..., alias="disasterType", description="재난 유형 (9종: 강풍/풍랑/호우/대설/건조/지진해일/한파/태풍/황사/폭염)")
    severity: str = Field(..., description="강도 (주의보/경보)")
    region: str = Field(..., description="수신 지역명 (복수 지역 쉼표 구분 가능)")
    created_at: Optional[datetime] = Field(None, alias="createdAt", description="레코드 생성 시각")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt", description="레코드 수정 시각")

    class Config:
        populate_by_name = True


class EmergencyMessageListResponse(BaseModel):
    """긴급재난문자 목록 응답"""
    total: int = Field(..., description="전체 메시지 수")
    data: List[EmergencyMessage] = Field(..., description="긴급재난문자 목록")

    class Config:
        populate_by_name = True


class EmergencyMessageFilter(BaseModel):
    """긴급재난문자 필터 (쿼리 파라미터)"""
    disaster_type: Optional[str] = Field(None, alias="disasterType", description="재난 유형으로 필터링")
    severity: Optional[str] = Field(None, description="강도로 필터링 (주의보/경보)")
    region: Optional[str] = Field(None, description="지역명으로 필터링 (부분 매칭)")
    start_date: Optional[date] = Field(None, alias="startDate", description="시작 날짜 (이후 발생)")
    end_date: Optional[date] = Field(None, alias="endDate", description="종료 날짜 (이전 발생)")
    limit: int = Field(100, description="조회 개수 제한", ge=1, le=1000)
    offset: int = Field(0, description="조회 시작 위치", ge=0)

    class Config:
        populate_by_name = True


class EmergencyMessageStatistics(BaseModel):
    """긴급재난문자 통계"""
    total_messages: int = Field(..., alias="totalMessages", description="총 메시지 건수")
    most_common_type: Optional[str] = Field(None, alias="mostCommonType", description="가장 빈번한 재난 유형")
    by_type: dict = Field(default_factory=dict, alias="byType", description="재난 유형별 통계")
    by_severity: dict = Field(default_factory=dict, alias="bySeverity", description="강도별 통계")
    by_region: dict = Field(default_factory=dict, alias="byRegion", description="지역별 통계")

    class Config:
        populate_by_name = True
