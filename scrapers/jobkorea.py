"""
scrapers/jobkorea.py
잡코리아 채용공고 수집 모듈 (개별 카드 정밀 파싱 및 다중 공고 텍스트 오염 방지 버전)
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
            
            # 1. 모던 잡코리아 카드 컨테이너(shadow-list) 탐색
            cards = soup.find_all('div', class_=re.compile(r'shadow-list'))
            
            if cards:
                for c in cards:
                    gi_links = [a for a in c.find_all('a') if a.get('href') and '/Recruit/GI_Read/' in a.get('href')]
                    if not gi_links:
                        continue
                    
                    # 제목 링크 추출
                    title_a = None
                    for a in gi_links:
                        txt = a.get_text(strip=True)
                        if txt and len(txt) >= 4 and not any(x in txt for x in ['스크랩', '지원하기', '즉시지원']):
                            title_a = a
                            break
                    if not title_a and len(gi_links) >= 2:
                        title_a = gi_links[1]
                    elif not title_a:
                        title_a = gi_links[0]
                    
                    title = title_a.get_text(strip=True)
                    if not title or len(title) < 4:
                        continue
                    
                    href = title_a.get('href', '')
                    m = re.search(r'/Recruit/GI_Read/(\d+)', href)
                    if not m:
                        continue
                    gi_id = m.group(1)
                    if gi_id in seen_ids:
                        continue
                    seen_ids.add(gi_id)
                    
                    # 기업명 추출 (보통 3번째 링크나 회사 태그)
                    corp_name = ""
                    c_link = c.find('a', href=re.compile(r'/(?:Company|co)/\d+'))
                    if c_link:
                        corp_name = c_link.get_text(strip=True)
                    if not corp_name and len(gi_links) >= 3:
                        c_txt = gi_links[2].get_text(strip=True)
                        if c_txt and c_txt != title and len(c_txt) < 30:
                            corp_name = c_txt
                    
                    strings = list(c.stripped_strings)
                    
                    if not corp_name or corp_name == "기업명 미상":
                        for s in strings:
                            if s != title and any(p in s for p in ['(주)', '㈜', '유한회사', '로지스', '물류', '풀필먼트', '컴퍼니', '코리아']):
                                corp_name = s
                                break
                    
                    location = ""
                    career = ""
                    salary = ""
                    for s in strings:
                        if any(loc in s for loc in ["인천", "부천", "시흥", "중구", "서구", "남동구", "연수구", "부평구", "김포", "서울", "경기"]):
                            if not location and len(s) < 25 and s != corp_name and s != title:
                                location = s
                        if any(car in s for car in ["경력", "신입", "무관"]):
                            if not career and len(s) < 15 and s != title:
                                career = s
                        if any(sal in s for sal in ["만원", "연봉", "월급"]):
                            if not salary and len(s) < 20:
                                salary = s
                    
                    jobs.append({
                        "id": f"jobkorea_{gi_id}",
                        "source": "잡코리아",
                        "title": title,
                        "company": corp_name if corp_name else "잡코리아 등록기업",
                        "location": location if location else "인천",
                        "career": career if career else "경력",
                        "education": "",
                        "sectors": "물류",
                        "deadline": "채용시 마감",
                        "salary_text": salary if salary else "회사내규 / 협의",
                        "url": f"https://www.jobkorea.co.kr/Recruit/GI_Read/{gi_id}",
                        "keyword": keyword,
                        "raw_desc": " ".join(strings)
                    })
            else:
                # 레거시 구조 폴백 (최대 3레벨 부모로 제한하여 다른 공고 텍스트 유입 차단)
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
                        
                    curr = a.parent
                    if curr and curr.parent:
                        curr = curr.parent
                    raw_texts = list(curr.stripped_strings) if curr else [title]
                    
                    jobs.append({
                        "id": f"jobkorea_{gi_id}",
                        "source": "잡코리아",
                        "title": title,
                        "company": "잡코리아 등록기업",
                        "location": "인천",
                        "career": "경력",
                        "education": "",
                        "sectors": "물류",
                        "deadline": "채용시 마감",
                        "salary_text": "회사내규 / 협의",
                        "url": f"https://www.jobkorea.co.kr/Recruit/GI_Read/{gi_id}",
                        "keyword": keyword,
                        "raw_desc": " ".join(raw_texts)
                    })
        except Exception as e:
            print(f"[잡코리아 수집 에러] 키워드: {keyword}, 에러: {e}")

    return jobs
