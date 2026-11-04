"""
scrapers/jobkorea.py
잡코리아 채용공고 수집 모듈 (기업명 및 상세 파싱 정밀 강화 버전)
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

def fetch_jobkorea_jobs(keyword, local_code="B000", max_pages=2):
    """
    잡코리아에서 주어진 키워드로 공고 수집 (인천 및 인근 지역)
    """
    jobs = []
    seen_ids = set()

    for page in range(1, max_pages + 1):
        encoded_kw = urllib.parse.quote(keyword)
        loc_param = f"&local={local_code}" if local_code else ""
        url = f"https://www.jobkorea.co.kr/Search/?stext={encoded_kw}{loc_param}&Page_No={page}"
        
        try:
            res = requests.get(url, headers=HEADERS, timeout=8)
            if res.status_code != 200:
                continue
            
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'/Recruit/GI_Read/\d+'))
            
            for a in links:
                href = a.get('href', '')
                match = re.search(r'/Recruit/GI_Read/(\d+)', href)
                if not match:
                    continue
                gi_id = match.group(1)
                if gi_id in seen_ids:
                    continue
                seen_ids.add(gi_id)

                title = a.get_text(strip=True)
                if not title or len(title) < 4:
                    continue

                full_url = href if href.startswith('http') else f"https://www.jobkorea.co.kr{href}"

                # 상위 카드 컨테이너에서 기업명 탐색
                curr = a
                corp_name = ""
                raw_texts = []
                for _ in range(7):
                    curr = curr.parent
                    if not curr:
                        break
                    
                    # 1. Company 링크
                    c_tag = curr.find('a', href=re.compile(r'/(?:Company|co)/\d+'))
                    if c_tag and not corp_name:
                        txt = c_tag.get_text(strip=True)
                        if txt and len(txt) < 30 and not any(x in txt for x in ['채용', '스크랩', '지원']):
                            corp_name = txt

                    # 2. 기업명 클래스 탐색
                    c_tag2 = curr.find(class_=re.compile(r'corp_name|name|company|corp', re.I))
                    if c_tag2 and not corp_name:
                        txt = c_tag2.get_text(strip=True)
                        if txt and len(txt) < 30 and not any(x in txt for x in ['채용', '스크랩', '지원']):
                            corp_name = txt
                
                if curr:
                    raw_texts = list(curr.stripped_strings)

                # 제목에 기업명이 [대괄호]나 (주) 등으로 포함된 경우 추출
                if not corp_name or corp_name == "기업명 미상":
                    title_corp_match = re.search(r'\[([^\]]+)\]', title)
                    if title_corp_match and len(title_corp_match.group(1)) <= 15:
                        corp_name = title_corp_match.group(1)
                    else:
                        주_match = re.search(r'(\([주유]\)[가-힣A-Za-z0-9]+|[가-힣A-Za-z0-9]+\([주유]\))', title)
                        if 주_match:
                            corp_name = 주_match.group(1)

                location = ""
                salary_text = ""
                career = ""
                for t in raw_texts:
                    if any(loc in t for loc in ["인천", "부천", "시흥", "서울", "경기", "중구", "서구", "남동구"]):
                        if not location and len(t) < 30:
                            location = t
                    if any(kw in t for kw in ["만원", "연봉", "협의", "내규"]):
                        if not salary_text and t != "연봉":
                            salary_text = t
                    if any(kw in t for kw in ["경력", "신입"]):
                        if not career and len(t) < 20:
                            career = t

                jobs.append({
                    "id": f"jobkorea_{gi_id}",
                    "source": "잡코리아",
                    "title": title,
                    "company": corp_name if corp_name else "잡코리아 등록기업",
                    "location": location if location else "인천/경기",
                    "career": career if career else "경력",
                    "education": "",
                    "sectors": "물류",
                    "deadline": "채용시 마감",
                    "salary_text": salary_text,
                    "url": full_url,
                    "keyword": keyword,
                    "raw_desc": " ".join(raw_texts)
                })
        except Exception as e:
            print(f"[잡코리아 수집 에러] 키워드: {keyword}, 에러: {e}")

    return jobs
