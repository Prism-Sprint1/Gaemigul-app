import os
import requests
from dotenv import load_dotenv

# .env 파일 불러오기
load_dotenv()

# API Key 가져오기
api_key = os.getenv("FRED_API_KEY")

print("API Key 존재 여부:", bool(api_key))

if not api_key:
    print("❌ FRED_API_KEY를 찾을 수 없습니다.")
    exit()

# FRED API 호출
url = "https://api.stlouisfed.org/fred/series/observations"

params = {
    "series_id": "CPIAUCSL",
    "api_key": api_key,
    "file_type": "json",
    "limit": 5,
    "sort_order": "desc",
}

response = requests.get(url, params=params)

print("HTTP 상태 코드:", response.status_code)

if response.status_code == 200:
    data = response.json()

    print("✅ FRED API 연결 성공!")
    print("최근 CPI 데이터:")

    for item in data["observations"]:
        print(
            f"날짜: {item['date']} / "
            f"값: {item['value']}"
        )

else:
    print("❌ FRED API 연결 실패")
    print(response.text)ㅅㄱ
