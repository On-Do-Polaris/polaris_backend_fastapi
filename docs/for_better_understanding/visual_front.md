1. 시나리오: 온실가스 배출량 (DB -> JSON 변환)
   목표: DB에 저장된 연도별 배출량 데이터를 조회하여, 프론트엔드가 그릴 수 있는 Line Chart JSON으로 변환한다.

1) DB 모델 (SQLAlchemy 예시)
   먼저 데이터베이스에 저장된 형태입니다.

Python

# db/models/climate.py

from sqlalchemy import Column, Integer, Float, String
from db.session import Base

class GHG_Emission(Base):
**tablename** = "tb_ghg_emission"

    id = Column(Integer, primary_key=True)
    year = Column(String(4))   # 예: "2021", "2022"
    scope1 = Column(Float)     # 직접 배출량
    scope2 = Column(Float)     # 간접 배출량
    total = Column(Float)      # 합계

2. 변환 로직 (Service Layer)
   핵심 부분입니다. DB 데이터를 순회하면서 List Comprehension으로 데이터를 뽑아냅니다.

Python

# services/report_builder.py

from typing import List
from db.models.climate import GHG_Emission

# 아까 정의한 Pydantic 모델들 임포트

from models.report import ChartBlock, ChartData, ChartSeries

def build_ghg_chart_block(db_data: List[GHG_Emission]) -> ChartBlock:
"""
DB에서 가져온 GHG_Emission 리스트를 차트용 JSON 블록으로 변환
"""

    # 1. X축 데이터 추출 (연도)
    years = [data.year for data in db_data] # ["2021", "2022", "2023", "2024"]

    # 2. Y축 시리즈 데이터 구성 (DB 컬럼 -> Chart Series 매핑)
    # Scope 1 데이터
    series_scope1 = ChartSeries(
        name="Scope 1 (직접배출)",
        data=[data.scope1 for data in db_data],
        color="#FF6384" # (선택) 프론트랑 협의된 색상
    )

    # Scope 2 데이터
    series_scope2 = ChartSeries(
        name="Scope 2 (간접배출)",
        data=[data.scope2 for data in db_data],
        color="#36A2EB"
    )

    # 3. 차트 데이터 조립
    chart_data = ChartData(
        categories=years,               # X축: 연도
        series=[series_scope1, series_scope2], # Y축: 데이터셋 리스트
        y_unit="tCO2eq"                 # 단위
    )

    # 4. 최종 블록 반환
    return ChartBlock(
        id="chart_ghg_trend",
        title="연도별 온실가스 배출량 추이",
        description="최근 4개년 Scope 1, 2 배출량 변화 (단위: tCO2eq)",
        chart_type="line",
        data=chart_data
    )

3. 결과 JSON (프론트엔드가 받게 될 값)
   위 코드가 실행되면 아래와 같은 JSON이 생성됩니다. Key는 고정되어 있고, Value 부분만 DB 값으로 채워졌습니다.

JSON

{
"type": "chart",
"id": "chart_ghg_trend",
"chart_type": "line",
"title": "연도별 온실가스 배출량 추이",
"description": "최근 4개년 Scope 1, 2 배출량 변화 (단위: tCO2eq)",
"data": {
"categories": ["2021", "2022", "2023", "2024"],
"y_unit": "tCO2eq",
"series": [
{
"name": "Scope 1 (직접배출)",
"data": [1432.0, 1431.0, 1434.0, 1283.0],
"color": "#FF6384"
},
{
"name": "Scope 2 (간접배출)",
"data": [84677.0, 107782.0, 125207.0, 135382.0],
"color": "#36A2EB"
}
]
}
}
💡 개발 팁: "매핑 테이블" 활용하기
만약 차트가 아주 많다면, 하드코딩 대신 '매핑 정보'를 설정 파일로 관리하면 더 세련된 코드가 됩니다.

Python

# config/chart_mapping.py

# 어떤 DB 컬럼을 어떤 차트 시리즈로 매핑할지 정의

GHG_CHART_CONFIG = {
"x_axis": "year",
"series": [
{"column": "scope1", "label": "Scope 1 (직접)", "color": "red"},
{"column": "scope2", "label": "Scope 2 (간접)", "color": "blue"},
]
}

# 이렇게 해두면 루프 돌면서 자동으로 JSON을 만들 수 있습니다.
