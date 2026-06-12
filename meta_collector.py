"""
Meta Ad Library API 경쟁사 광고 수집기

pip install requests
"""

import requests
import json
import os
from datetime import datetime

# ── 설정 ──────────────────────────────────────────────
META_ACCESS_TOKEN = "EAAYAvLXUIqUBRnNnPKgEiwjpXrRkqhFlyxLghZBNKkqNdoQZCSrTZBXZBGUDGIdt98zqxZCQ33EZBwQOGtBNnRaVOtW1PFZAdQNER4SZCTK1PmPV6ASbtpqAlLNM9apFhSXYrigzBr6faKo5mZAxDeVPrRA5iUqzZBntRRs6JYcPd7ZApMSdC2q7NOGKfZCtuDVTzpZBwTDjpr6CjoZBCZAPKO2ZA7erhYVKGNA0l1tngpFwLUnsRNmxQIZCFDavOvhDensxvCWQDnRe1QKaUsDtgJAyhPAvsAM5zYeLXN9bEP7013uCTHh76ElNlZBay8zKTzzTMviFbTNEwrZCTZAc64ia"
BRAND_LIST = ["뉴트리코어", "여에스더", "솔티스", "아이클리어", "닥터파이토", "뉴트리원", "종근당건강"]
OUTPUT_FILE = "ads_data.json"
AD_REACHED_COUNTRIES = ["KR"]   # ISO 국가코드
AD_TYPE = "ALL"                  # ALL | POLITICAL_AND_ISSUE_ADS
LIMIT = 50                       # 페이지당 최대 50
# ──────────────────────────────────────────────────────

BASE_URL = "https://graph.facebook.com/v19.0/ads_archive"

FIELDS = ",".join([
    "id",
    "page_name",
    "ad_creative_bodies",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "ad_snapshot_url",
    "delivery_by_region",
    "impressions",
    "publisher_platforms",
    "ad_creative_link_captions",
    "ad_creative_link_descriptions",
    "ad_creative_link_titles",
])


def fetch_ads_for_brand(brand: str) -> list[dict]:
    """단일 브랜드의 광고 전체 페이지 수집"""
    ads = []
    params = {
        "access_token": META_ACCESS_TOKEN,
        "search_terms": brand,
        "ad_reached_countries": AD_REACHED_COUNTRIES,
        "ad_type": AD_TYPE,
        "fields": FIELDS,
        "limit": LIMIT,
    }

    page = 1
    url = BASE_URL
    while url:
        print(f"  [{brand}] 페이지 {page} 수집 중...")
        resp = requests.get(url, params=params if page == 1 else {})
        resp.raise_for_status()
        data = resp.json()

        raw_ads = data.get("data", [])
        for ad in raw_ads:
            ads.append(normalize(ad, brand))

        # 다음 페이지
        url = data.get("paging", {}).get("next")
        params = {}   # next URL에는 파라미터 포함됨
        page += 1

    print(f"  [{brand}] 총 {len(ads)}개 수집 완료")
    return ads


def normalize(ad: dict, brand: str) -> dict:
    """API 응답을 통일된 형식으로 변환"""
    bodies = ad.get("ad_creative_bodies") or []
    platforms = ad.get("publisher_platforms") or []
    snapshot_url = ad.get("ad_snapshot_url", "")

    # 스냅샷 URL에서 이미지/영상 URL 직접 추출은 API 제한으로 불가,
    # snapshot_url 자체를 image_url 로 활용 (썸네일 대용)
    return {
        "ad_id": ad.get("id", ""),
        "brand": brand,
        "page_name": ad.get("page_name", ""),
        "body": bodies[0] if bodies else "",
        "start_date": ad.get("ad_delivery_start_time", ""),
        "end_date": ad.get("ad_delivery_stop_time", ""),
        "status": "inactive" if ad.get("ad_delivery_stop_time") else "active",
        "platforms": platforms,
        "image_url": snapshot_url,   # 스냅샷 미리보기 URL
        "video_url": "",             # 영상 URL (별도 크리에이티브 API 필요)
        "snapshot_url": snapshot_url,
        "collected_at": datetime.utcnow().isoformat(),
    }


def load_existing(path: str) -> dict[str, dict]:
    """기존 JSON 파일 로드 → {ad_id: ad} 딕셔너리 반환"""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        ads = json.load(f)
    return {a["ad_id"]: a for a in ads if a.get("ad_id")}


def save(path: str, ads_by_id: dict[str, dict]) -> None:
    ads_list = list(ads_by_id.values())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ads_list, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {path} ({len(ads_list)}개 광고)")


def main():
    print("=== Meta Ad Library 수집 시작 ===\n")

    existing = load_existing(OUTPUT_FILE)
    before = len(existing)
    print(f"기존 데이터: {before}개\n")

    for brand in BRAND_LIST:
        new_ads = fetch_ads_for_brand(brand)
        for ad in new_ads:
            ad_id = ad["ad_id"]
            if ad_id and ad_id not in existing:
                existing[ad_id] = ad

    after = len(existing)
    print(f"\n신규 추가: {after - before}개 / 누적 합계: {after}개")
    save(OUTPUT_FILE, existing)


if __name__ == "__main__":
    main()
