"""
scrapers/saramin.py
사람인 채용공고 수집 모듈
"""

import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}

def fetch_saramin_jobs(keyword, location_code="102000", max_pages=1):
    """
    사람인에서 주어진 키워드로 공고 수집
    location_code: '102000' (인천)
    """
    jobs = []
    seen_ids = set()

    for page in range(1, max_pages + 1):
        encoded_kw = urllib.parse.quote(keyword)
        # 인천 우선 검색 또는 전체 검색
        url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchword={encoded_kw}&loc_mcd={location_code}&recruitPage={page}&recruitSort=relation"
        
        try:
            res = requests.get(url, headers=HEADERS, timeout=8)
            if res.status_code != 200:
                continue
            
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.select('.item_recruit')
            
            for item in items:
                rec_idx = item.get('value', '')
                if not rec_idx:
                    continue
                if rec_idx in seen_ids:
                    continue
                seen_ids.add(rec_idx)

                # 공고 제목 & 링크
                title_tag = item.select_one('.job_tit a')
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                rel_link = title_tag.get('href', '')
                link = f"https://www.saramin.co.kr{rel_link}" if rel_link.startswith('/') else rel_link

                # 회사명
                corp_tag = item.select_one('.corp_name a')
                corp_name = corp_tag.get_text(strip=True) if corp_tag else "기업명 미상"

                # 조건 (지역, 경력, 학력, 고용형태 등)
                conditions = [c.get_text(strip=True) for c in item.select('.job_condition span')]
                location = conditions[0] if len(conditions) > 0 else ""
                career = conditions[1] if len(conditions) > 1 else ""
                education = conditions[2] if len(conditions) > 2 else ""

                # 직무 키워드 / 섹터
                sector_tags = item.select('.job_sector a') or item.select('.job_sector span')
                sectors = [s.get_text(strip=True) for s in sector_tags]

                # 마감일
                deadline_tag = item.select_one('.job_date .date')
                deadline = deadline_tag.get_text(strip=True) if deadline_tag else "상시채용"

                # 연봉 정보가 태그나 본문에 있는지 탐색
                salary_text = ""
                badge = item.select_one('.area_badge .badge')
                for cond in conditions:
                    if '만원' in cond or '연봉' in cond:
                        salary_text = cond

                jobs.append({
                    "id": f"saramin_{rec_idx}",
                    "source": "사람인",
                    "title": title,
                    "company": corp_name,
                    "location": location,
                    "career": career,
                    "education": education,
                    "sectors": ", ".join(sectors),
                    "deadline": deadline,
                    "salary_text": salary_text,
                    "url": link,
                    "keyword": keyword
                })
        except Exception as e:
            print(f"[사람인 수집 에러] 키워드: {keyword}, 에러: {e}")

    return jobs

if __name__ == '__main__':
    results = fetch_saramin_jobs("물류센터", max_pages=1)
    print(f"사람인 테스트 수집 결과: {len(results)}건")
    if results:
        print(results[0])
