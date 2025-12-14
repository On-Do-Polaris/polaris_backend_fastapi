import os
from ai_agent.utils.building_data_fetcher import BuildingDataFetcher
from dotenv import load_dotenv # load_dotenv 임포트 추가
from pathlib import Path # Path 임포트 추가

# .env 파일 로드 (프로젝트 루트 또는 ai_agent 디렉토리)
BASE_DIR = Path(__file__).parent.parent.parent # ai_agent/utils에서 프로젝트 루트로
load_dotenv(BASE_DIR / ".env") # 프로젝트 루트의 .env 파일 로드

# --- 실제 API 키 설정 가이드 ---
# 실제 데이터로 테스트를 진행하려면 다음 환경 변수들이 설정되어 있어야 합니다.
# .env 파일에 다음 변수들을 추가하거나, 쉘 환경 변수로 설정해 주세요.
# VWORLD_API_KEY=당신의_VWORLD_API_키 (get_building_code_from_coords에서 필요)
# PUBLICDATA_API_KEY=당신의_건축물대장_API_키
# ROADSEARCH_API_KEY=당신의_juso.go.kr_도로명주소_검색_API_키
# COORDINATESEARCH_API_KEY=당신의_juso.go.kr_주소_좌표_변환_API_키

vworld_api_key = os.getenv("VWORLD_API_KEY")
publicdata_api_key = os.getenv("PUBLICDATA_API_KEY")
road_search_api_key = os.getenv("ROADSEARCH_API_KEY")
coord_search_api_key = os.getenv("COORDINATESEARCH_API_KEY")

if not vworld_api_key or not publicdata_api_key or not road_search_api_key or not coord_search_api_key:
    print("⚠️  필수 환경 변수 중 일부가 설정되지 않았습니다.")
    print("    VWORLD_API_KEY, PUBLICDATA_API_KEY, ROADSEARCH_API_KEY, COORDINATESEARCH_API_KEY")
    print("실제 API 호출을 위해서는 이 키들이 필요합니다.")
    print("테스트를 계속 진행하려면 .env 파일에 키를 설정하거나 쉘 환경 변수로 설정해 주세요.")
    exit(1)

# --- 테스트할 주소 목록 (도로명 주소) ---
addresses_to_test = [
    "경기도 성남시 분당구 판교로 255번길 38",
    "경기도 성남시 분당구 수내로 39 지웰 푸르지오",
    "대전광역시 유성구 엑스포로 325"
]

# --- BuildingDataFetcher 인스턴스 생성 ---
fetcher = BuildingDataFetcher()

print("\n--- 실제 데이터 테스트 시작 ---")

for i, address_str in enumerate(addresses_to_test):
    print(f"\n[{i+1}/{len(addresses_to_test)}] 주소: {address_str}")
    print(f"   juso.go.kr을 통해 주소 구성 요소 검색 중...")
    
    juso_components = fetcher.get_address_components_from_juso(address_str)
    if not juso_components:
        print(f"   ❌ juso.go.kr 주소 구성 요소 검색 실패: {address_str}")
        print("   다음 주소로 건너뜁니다.")
        continue
    
    print(f"   ✅ 주소 구성 요소 검색 성공. 주요 정보: {juso_components.get('siNm')} {juso_components.get('sggNm')} {juso_components.get('roadAddr')}")
    print(f"   juso.go.kr을 통해 위/경도 변환 중...")

    coords = fetcher.get_coords_from_juso_components(juso_components)
    if not coords:
        print(f"   ❌ juso.go.kr을 통한 위/경도 변환 실패: {address_str}")
        print("   다음 주소로 건너뜁니다.")
        continue
        
    lat, lon = coords['lat'], coords['lon']
    print(f"   ✅ 위/경도 변환 성공: (위도: {lat}, 경도: {lon})")
    
    print(f"   BuildingDataFetcher를 통한 TCFD 데이터 수집 중...")
    
    try:
        # fetch_full_tcfd_data는 실제 API 호출을 시도합니다.
        tcfd_data = fetcher.fetch_full_tcfd_data(lat, lon)
        
        if tcfd_data:
            print("   ✅ 데이터 수집 성공:")
            # 주요 정보 요약 출력
            print(f"      - 건물명: {tcfd_data['meta'].get('name', 'N/A')}")
            print(f"      - 주소: {tcfd_data['meta'].get('address', 'N/A')}")
            print(f"      - 시군구코드: {tcfd_data['meta']['admin_codes'].get('sigungu_cd', 'N/A')}")
            print(f"      - 법정동코드: {tcfd_data['meta']['admin_codes'].get('bjdong_cd', 'N/A')}")
            print(f"      - 주용도: {tcfd_data['physical_specs'].get('main_purpose', 'N/A')}")
            print(f"      - 지하층수: {tcfd_data['physical_specs']['floors'].get('underground', 'N/A')}")
            print(f"      - 연면적: {tcfd_data['transition_specs'].get('total_area', 'N/A')} m²")
            print(f"      - 내진능력: {tcfd_data['physical_specs']['seismic'].get('ability', 'N/A')}")
            print(f"      - 층별 상세 (일부):")
            for floor_detail in tcfd_data['floor_details'][:3]: # 상위 3개 층만 출력
                print(f"         - {floor_detail.get('name', 'N/A')}: 용도='{floor_detail.get('usage_main', 'N/A')}', 기타='{floor_detail.get('usage_etc', 'N/A')}', 주요설비여부={floor_detail.get('is_potentially_critical', False)}")
        else:
            print("   ❌ 데이터 수집 실패 또는 결과 없음 (API 키, 네트워크, 데이터 부재 등 확인)")
            
    except Exception as e:
        print(f"   ❌ 데이터 수집 중 예상치 못한 오류 발생: {e}")

print("\n--- 실제 데이터 테스트 완료 ---")
