"""
Analysis Enhance API 테스트 스크립트

이 스크립트는 /api/sites/{site_id}/analysis/enhance API의 동작을 테스트합니다.

실행 방법:
    python test_enhance_api.py

전제조건:
    - FastAPI 서버가 http://localhost:8000 에서 실행 중
    - 유효한 API 키 설정
"""

import requests
import json
from uuid import uuid4

# 설정
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key"  # 실제 API 키로 변경
SITE_ID = str(uuid4())

headers = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json"
}


def test_1_basic_analysis():
    """1차 테스트: 기본 분석 (추가 데이터 없음)"""
    print("=" * 70)
    print("TEST 1: 기본 분석 (추가 데이터 없음)")
    print("=" * 70)

    payload = {
        "site": {
            "id": SITE_ID,
            "name": "서울 본사 테스트",
            "latitude": 37.5665,
            "longitude": 126.9780
        },
        "hazardTypes": ["HIGH_TEMPERATURE", "TYPHOON"],
        "priority": "NORMAL"
    }

    print(f"\n[Request] POST {BASE_URL}/api/sites/{SITE_ID}/analysis/start")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        response = requests.post(
            f"{BASE_URL}/api/sites/{SITE_ID}/analysis/start",
            headers=headers,
            json=payload,
            timeout=300  # 5분 타임아웃
        )

        print(f"\n[Response] Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if response.status_code == 200 and result.get("status") == "completed":
            print("\n✅ TEST 1 PASSED: 기본 분석 성공")
            return result.get("jobId")
        else:
            print("\n❌ TEST 1 FAILED: 기본 분석 실패")
            return None

    except Exception as e:
        print(f"\n❌ TEST 1 ERROR: {e}")
        return None


def test_2_enhance_with_additional_data(job_id):
    """2차 테스트: 추가 데이터 반영 (enhance)"""
    print("\n" + "=" * 70)
    print("TEST 2: 추가 데이터 반영 (enhance)")
    print("=" * 70)

    payload = {
        "jobId": job_id,
        "additionalData": {
            "rawText": """
태양광 발전 시설 200kW 설치 예정 (2025년 3월 준공).
건물 리모델링 2023년 완료 (단열재 교체, 냉난방 시스템 개선).
비상 발전기 50kW 보유 (연료: 경유, 3일 연속 가동 가능).
            """.strip(),
            "metadata": {
                "source": "user_input",
                "category": "facility_improvement"
            }
        }
    }

    print(f"\n[Request] POST {BASE_URL}/api/sites/{SITE_ID}/analysis/enhance")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        response = requests.post(
            f"{BASE_URL}/api/sites/{SITE_ID}/analysis/enhance",
            headers=headers,
            json=payload,
            timeout=300  # 5분 타임아웃
        )

        print(f"\n[Response] Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if response.status_code == 200 and result.get("status") == "completed":
            print("\n✅ TEST 2 PASSED: 추가 데이터 반영 성공")
            print(f"   - 원본 job_id: {job_id}")
            print(f"   - 새 job_id: {result.get('jobId')}")
            return result.get("jobId")
        else:
            print("\n❌ TEST 2 FAILED: 추가 데이터 반영 실패")
            return None

    except Exception as e:
        print(f"\n❌ TEST 2 ERROR: {e}")
        return None


def test_3_enhance_again(job_id):
    """3차 테스트: 추가 향상 (더 많은 정보 반영)"""
    print("\n" + "=" * 70)
    print("TEST 3: 추가 향상 (더 많은 정보 반영)")
    print("=" * 70)

    payload = {
        "jobId": job_id,
        "additionalData": {
            "rawText": """
직원 수: 150명 (24시간 3교대 근무)
연간 전력 사용량: 약 500MWh
냉난방 시스템: 중앙 집중식 (열펌프 방식)
물 사용량: 연간 10,000톤 (재활용 시스템 운영)
            """.strip(),
            "metadata": {
                "source": "facility_manager",
                "category": "operational_data"
            }
        }
    }

    print(f"\n[Request] POST {BASE_URL}/api/sites/{SITE_ID}/analysis/enhance")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        response = requests.post(
            f"{BASE_URL}/api/sites/{SITE_ID}/analysis/enhance",
            headers=headers,
            json=payload,
            timeout=300  # 5분 타임아웃
        )

        print(f"\n[Response] Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if response.status_code == 200 and result.get("status") == "completed":
            print("\n✅ TEST 3 PASSED: 추가 향상 성공")
            print(f"   - 이전 job_id: {job_id}")
            print(f"   - 최종 job_id: {result.get('jobId')}")
            return result.get("jobId")
        else:
            print("\n❌ TEST 3 FAILED: 추가 향상 실패")
            return None

    except Exception as e:
        print(f"\n❌ TEST 3 ERROR: {e}")
        return None


def test_4_invalid_job_id():
    """4차 테스트: 잘못된 job_id (에러 처리 확인)"""
    print("\n" + "=" * 70)
    print("TEST 4: 잘못된 job_id (에러 처리 확인)")
    print("=" * 70)

    invalid_job_id = str(uuid4())
    payload = {
        "jobId": invalid_job_id,
        "additionalData": {
            "rawText": "테스트 데이터"
        }
    }

    print(f"\n[Request] POST {BASE_URL}/api/sites/{SITE_ID}/analysis/enhance")
    print(f"Invalid job_id: {invalid_job_id}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/sites/{SITE_ID}/analysis/enhance",
            headers=headers,
            json=payload,
            timeout=60
        )

        print(f"\n[Response] Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if response.status_code == 404 or (response.status_code == 200 and result.get("status") == "failed"):
            print("\n✅ TEST 4 PASSED: 에러 처리 정상 작동")
        else:
            print("\n❌ TEST 4 FAILED: 에러 처리 미작동")

    except Exception as e:
        print(f"\n❌ TEST 4 ERROR: {e}")


def main():
    """전체 테스트 실행"""
    print("\n" + "=" * 70)
    print("Analysis Enhance API 테스트 시작")
    print("=" * 70)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Site ID: {SITE_ID}")

    # TEST 1: 기본 분석
    job_id_1 = test_1_basic_analysis()
    if not job_id_1:
        print("\n❌ TEST 1 실패로 인해 나머지 테스트 중단")
        return

    # TEST 2: 추가 데이터 반영
    job_id_2 = test_2_enhance_with_additional_data(job_id_1)
    if not job_id_2:
        print("\n⚠️ TEST 2 실패 (TEST 3, 4는 계속 진행)")

    # TEST 3: 추가 향상
    if job_id_2:
        job_id_3 = test_3_enhance_again(job_id_2)
        if job_id_3:
            print(f"\n최종 job_id: {job_id_3}")

    # TEST 4: 에러 처리
    test_4_invalid_job_id()

    print("\n" + "=" * 70)
    print("테스트 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()
