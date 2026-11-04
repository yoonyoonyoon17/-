"""
scrapers/remember.py
리멤버 커리어(Remember Career) 채용공고 수집 모듈 (고도화 버전)
"""

import requests
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/plain, */*',
    'Origin': 'https://career.rememberapp.co.kr',
    'Referer': 'https://career.rememberapp.co.kr/'
}

API_URL = 'https://career-api.rememberapp.co.kr/job_postings/search'

def fetch_remember_jobs(keyword, max_pages=1, per_page=30):
    """
    리멤버 API를 통해 주어진 키워드로 채용공고 수집
    """
    jobs = []
    seen_ids = set()

    for page in range(1, max_pages + 1):
        payload = {
            "page": page,
            "per": per_page,
            "search": {
                "keyword": keyword
            }
        }

        try:
            res = requests.post(API_URL, headers=HEADERS, json=payload, timeout=8)
            if res.status_code != 200:
                continue

            data = res.json()
            items = data.get('data', [])

            for item in items:
                posting_id = item.get('id')
                if not posting_id or posting_id in seen_ids:
                    continue
                seen_ids.add(posting_id)

                title = item.get('title', '')
                if not title:
                    continue

                company_obj = item.get('company') or {}
                org_obj = item.get('organization') or {}
                corp_name = company_obj.get('name') or org_obj.get('name') or item.get('company_description') or "리멤버 등록기업"

                norm_addr = item.get('normalized_address') or {}
                l1 = norm_addr.get('level1', '')
                l2 = norm_addr.get('level2', '')
                location = f"{l1} {l2}".strip()
                if not location:
                    addresses = item.get('addresses') or []
                    if addresses:
                        location = f"{addresses[0].get('address_level1', '')} {addresses[0].get('address_level2', '')}".strip()

                min_exp = item.get('min_experience')
                max_exp = item.get('max_experience')
                career_str = ""
                if min_exp is not None and max_exp is not None:
                    career_str = f"경력 {min_exp}~{max_exp}년"
                elif min_exp is not None:
                    career_str = f"경력 {min_exp}년 이상"
                elif max_exp is not None:
                    career_str = f"경력 {max_exp}년 이하"

                min_sal = item.get('min_salary')
                max_sal = item.get('max_salary')
                salary_text = ""
                if min_sal and max_sal:
                    salary_text = f"{min_sal:,} ~ {max_sal:,}만원"
                elif min_sal:
                    salary_text = f"최소 {min_sal:,}만원 이상"
                else:
                    salary_text = "회사내규 / 협의"

                job_desc = item.get('job_description') or ""
                qual = item.get('qualifications') or ""
                pref = item.get('preferred_qualifications') or ""
                sectors = []
                for jc in item.get('job_categories', []):
                    if isinstance(jc, dict):
                        sectors.append(jc.get('level2') or jc.get('level1', ''))

                link = f"https://career.rememberapp.co.kr/job/posting/{posting_id}"

                jobs.append({
                    "id": f"remember_{posting_id}",
                    "source": "리멤버",
                    "title": title,
                    "company": corp_name,
                    "location": location,
                    "career": career_str,
                    "education": item.get('education_requirement') or "",
                    "sectors": ", ".join([s for s in sectors if s]),
                    "deadline": (item.get('ends_at') or "")[:10] if item.get('ends_at') else "상시채용",
                    "salary_text": salary_text,
                    "url": link,
                    "keyword": keyword,
                    "raw_desc": f"{job_desc} {qual} {pref}"[:1000]
                })
        except Exception as e:
            print(f"[리멤버 수집 에러] 키워드: {keyword}, 에러: {e}")

    return jobs
