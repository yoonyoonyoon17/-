"""
matcher.py
조윤호 님의 이력서 프로필과 수집된 공고 간의 정밀 매칭 및 추천 점수 산출 엔진
(자격요건 초과 배제, 현장직 완전 제외 / 물류사무 및 관리직 중심, 출퇴근 30분, 연봉 5,100만+ 기준)
"""

import re
from config import USER_PROFILE, LOCATION_CRITERIA, SALARY_CRITERIA

# 반드시 포함되어야 하는 물류 관련 핵심 키워드
LOGISTICS_MUST_KEYWORDS = [
    "물류", "풀필먼트", "fulfillment", "창고", "wms", "tms", "scm",
    "물류센터", "물류운영", "물류기획", "물류관리", "유통물류",
    "센터장", "물류자동화", "3pl", "4pl", "자재", "물류사무", "물류팀"
]

# 비물류 무관 직무 배제 키워드
NON_LOGISTICS_EXCLUDE_KEYWORDS = [
    "해외영업", "기술영업", "마케팅리더", "마케팅", "이커머스 마케팅", "크리에이터",
    "투자분석", "특허", "나일론", "뷰티", "화장품 bm", "부동산 개발", "건축시공", "분양",
    "디자이너", "간호사", "보육교사", "보건관리자", "보건", "안전관리자", "산업안전관리자",
    "로봇 티칭", "로봇 프로그래밍", "시운전", "소프트웨어 개발", "웹개발", "개발자",
    "각 분야별", "부문별 채용", "각 부문", "공통 채용"
]

# 현장 실무 / 단순노무 / 생산직 / 현장 노동 배제 키워드 (사용자 요구사항 3: 현장 업무 완전 제외)
# 물류 포장, 피킹, 입고, 하역, 상하차, 단순 지게차, 단순 입출고, 생산직, 단기직, 현장직원 등 배제!
FIELD_WORK_EXCLUDE_KEYWORDS = [
    # 현장직 명칭
    "현장사원", "현장직", "현장 사원", "현장사원 모집", "현장직원", "물류직원 모집", "물류직원",
    "현장관리자", "현장관리", "team captain", "팀캡틴", "캡틴", "조장", "반장",
    "직원채용", "직원 모집", "사원 모집", "현장 입출하",
    # 현장 실무 행위
    "단순 피킹", "피킹", "패킹", "포장원", "단순 포장", "포장직", "포장", "분류원", "물품분류", "분류",
    "상하차", "하역", "입출하", "적재", "방재팀", "방재", "시설관리", "보안팀",
    "지게차운전", "지게차 운전", "지게차 필수", "지게차운전 필수", "지게차 기사", "지게차",
    # 생산/노무/단기/기사
    "생산직", "단순노무", "단기", "투잡", "초보", "초보가능", "초보환영", "알바", "단기알바",
    "물류기사", "배송기사", "화물기사", "지입기사", "배달원", "납품기사", "운전기사",
    "현장직 야간", "야간근무 채용", "입출고 현장", "단순 입출고", "입출고팀", "수기 작업",
    "물류보조", "보조원", "단기 생산직", "시흥허브"
]

# 관리자 / 물류사무직 권장 긍정 키워드 (이 키워드가 있으면 우대)
OFFICE_MANAGEMENT_POSITIVE_KEYWORDS = [
    "센터장", "물류센터장", "총괄 매니저", "운영팀장", "물류팀장", "과장", "차장",
    "물류사무", "물류기획", "물류운영", "scm", "풀필먼트 운영", "area manager",
    "operation manager", "operations manager", "wms", "재고관리", "공정관리",
    "프로세스 개선", "물류관리자", "수불", "erp", "자재관리", "3pl 관리"
]

def check_certification_eligibility(title, raw_desc):
    """
    조윤호 님의 보유/미보유 자격증 기준 충족 여부 검증 (요구사항 2)
    공고가 요구하는 자격증이 미보유 자격증인 경우 탈락!
    """
    full_text = f"{title} {raw_desc}".lower()
    title_lower = title.lower()

    # 1. 미보유 자격증이 제목에 있거나 본문에서 필수/자격으로 요구되면 탈락
    for unheld in USER_PROFILE["unheld_certifications"]:
        unheld_lower = unheld.lower()
        if unheld_lower in title_lower:
            return False, f"미보유 필수 자격증 요구로 제외 ({unheld})", []

        # 본문에서 필수/자격요건/소지자 등으로 요구하는 경우
        pattern = rf"{re.escape(unheld_lower)}\s*(?:필수|자격|소지자|보유자|면허|기능사)"
        if re.search(pattern, full_text):
            return False, f"미보유 필수 자격 요건 미달 ({unheld})", []

    # 2. 보유 자격증 매칭 가점
    cert_reasons = []
    cert_tags = []
    if any(k in full_text for k in ["물류관리사"]):
        cert_reasons.append("물류관리사 자격 보유와 정확히 일치")
        cert_tags.append("물류관리사 우대")
    if any(k in full_text for k in ["유통관리사"]):
        cert_reasons.append("유통관리사 2급 자격 보유와 매칭")
        cert_tags.append("유통관리사")
    if any(k in full_text for k in ["무역영어", "toeic", "외국계", "global"]):
        cert_reasons.append("무역영어 1급 및 TOEIC 역량 부합")
        cert_tags.append("글로벌/무역영어")

    return True, cert_reasons, cert_tags

def check_experience_eligibility(career_str, title, raw_desc, min_exp_num=None):
    """
    조윤호 님의 경력(8년 2개월)보다 공고가 요구하는 조건이 더 큰 경우 배제 (요구사항 2)
    공고의 최소 요구 경력이 8.5년(9년 이상, 10년 이상 등)을 초과하면 탈락!
    """
    # 1. min_exp_num이 명시된 경우 (리멤버 등)
    if min_exp_num is not None and min_exp_num > USER_PROFILE["max_experience_years"]:
        return False, f"요구 경력 초과 (최소 {min_exp_num}년 이상 요구 / 보유: 8년 2개월)"

    text = f"{title} {career_str}".lower()

    # 2. 제목에 과도한 연차 요구(9년, 10년 이상, 12년 이상, 15년 이상, 부장급 등) 명시된 경우
    over_exp_title_patterns = [
        r'(?:1[0-9]|[9])년\s*(?:이상|↑|\+)',
        r'부장급\s*\(?(?:1[0-9]|[9])년',
        r'부장급',
        r'임원급',
        r'이사급',
        r'총괄\s*임원'
    ]
    for pat in over_exp_title_patterns:
        if re.search(pat, text):
            return False, "요구 경력(9년~10년 이상/부장·임원급) 초과로 제외"

    # 3. career_str에서 최소 요구 경력 파싱
    # 예: "경력 10년 이상", "경력 10~15년", "경력 9년 이상"
    # "경력 5~10년" -> min_exp는 5년이므로 합격!
    range_match = re.search(r'(\d+)\s*[~-]\s*(\d+)\s*년', career_str)
    if range_match:
        min_years = int(range_match.group(1))
        if min_years > 8:
            return False, f"요구 경력 초과 (최소 {min_years}년 이상 요구 / 보유: 8년 2개월)"
        return True, ""

    single_match = re.search(r'(\d+)\s*년\s*(?:이상|↑|\+)?', career_str)
    if single_match:
        years = int(single_match.group(1))
        if "이상" in career_str or "↑" in career_str or "+" in career_str:
            if years > 8:
                return False, f"요구 경력 초과 (최소 {years}년 이상 요구 / 보유: 8년 2개월)"

    return True, ""

def is_field_work_job(title, raw_desc, sectors):
    """
    주 업무가 현장 업무(피킹, 패킹, 포장, 상하차, 입고, 하역, 지게차 등)가
    주인 경우 배제 (요구사항 3: 물류사무직/관리직 OK, 현장 업무는 제외)
    """
    title_lower = title.lower()
    text = f"{title} {raw_desc} {sectors}".lower()

    # 1. 계약직 공고 배제 (정규직 과장급 타깃)
    if "계약직" in title_lower:
        return True, "계약직 공고 배제"

    # 2. 제목에 현장직/피킹/포장/하역/지게차/생산직 등이 명시된 경우 즉시 탈락
    for excl in FIELD_WORK_EXCLUDE_KEYWORDS:
        if excl in title_lower:
            return True, f"현장 실무/노무 배제 ({excl})"

    # 3. 파견/도급/단기 아웃소싱 키워드
    if any(k in title_lower for k in ["긴급", "투잡", "단기 생산직", "일급", "주급"]):
        return True, "단기/생산직 배제"

    # 4. 본문에서 현장 노동이 주 업무인지 검사
    field_keywords = ["피킹", "패킹", "포장", "상하차", "단순입출고", "지게차운전", "지게차", "하역", "까나리", "랩핑", "파렛트 적재"]
    field_work_count = sum(1 for kw in field_keywords if kw in text)
    
    office_mgmt_count = sum(1 for kw in OFFICE_MANAGEMENT_POSITIVE_KEYWORDS if kw in text)

    # 현장 키워드가 관리/사무 키워드보다 많거나, 관리 키워드가 전무한 경우
    if field_work_count >= 2 and office_mgmt_count < 2:
        return True, "현장 실무 위주 업무로 제외"

    return False, ""

def is_valid_logistics_job(title, sectors, raw_desc):
    """
    해당 공고가 물류/풀필먼트/SCM 사무 및 관리자 직무인지 엄격 검증
    """
    title_lower = title.lower()
    text = f"{title} {sectors} {raw_desc}".lower()

    # 1. 비물류 배제 키워드
    for excl in NON_LOGISTICS_EXCLUDE_KEYWORDS:
        if excl in title_lower:
            return False

    # 2. 물류 필수 키워드
    has_logistics = any(kw in text for kw in LOGISTICS_MUST_KEYWORDS)
    return has_logistics

def evaluate_commute(location_str):
    """
    인천역 코아루센트럴시티 기준 편도 통근 시간 및 적합도 평가 (편도 30분 이내)
    반환: (score [0~25], commute_time_text, is_within_30min, commute_details)
    """
    loc = location_str.strip()
    if not loc:
        return 15, "위치 확인 필요 (약 20~25분 추정)", True, "공고 내 상세 근무지 확인 요망"

    # 서울 지역 처리 (서울 도심/동부/남부는 30분 초과 탈락)
    if "서울" in loc or "서울특별시" in loc:
        if any(g in loc for g in ["강서", "마곡", "양천"]):
            return 12, "편도 약 30~35분 (경계선)", True, "경인고속 경유 강서권 통근"
        return 0, "통근 45분~1시간 이상 (서울 도심/동부)", False, "서울 도심 지역으로 인천역 기준 30분 초과"

    # 경기 원거리 제외
    for excl in ["용인", "이천", "안성", "평택", "여주", "화성", "오산", "수원", "성남", "분당", "판교", "남양주", "구리", "의정부", "포천", "파주"]:
        if excl in loc:
            return 0, "통근 40분~1시간 이상", False, f"원거리 지역({excl})으로 30분 초과"

    # Tier 1: 초근접 권역 (자가 5~15분 / 대중교통 15분 내외)
    for t1 in LOCATION_CRITERIA["tier1_exact"]:
        if t1 in loc:
            return 25, "편도 약 10~15분 (초근접)", True, "인천역에서 자가 10~15분 또는 버스/전철 15분 내외 초근접"

    # Tier 2: 최적 통근권 (자가 15~25분 / 수인분당선 20분대)
    for t2 in LOCATION_CRITERIA["tier2_exact"]:
        if t2 in loc:
            return 23, "편도 약 18~25분 (최적)", True, "제2외곽/인천대로/제2경인 자가 20분 또는 수인선 직결 20분대"

    # Tier 3: 출퇴근 가능 마지노선 (자가 25~32분)
    for t3 in LOCATION_CRITERIA["tier3_exact"]:
        if t3 in loc:
            return 19, "편도 약 25~30분 (가능권)", True, "자가 기준 약 25~30분 소요 (출퇴근 정체 고려 필요)"

    # 기타 인천 권역
    if "인천" in loc:
        return 22, "편도 약 20~25분 (인천 시내)", True, "인천 광역 권역으로 30분 이내 접근 가능"

    return 0, "통근 35분 이상", False, "거주지 기준 30분 초과 지역"

def evaluate_salary(salary_text, title, career_str):
    """
    연봉 조건 충족 여부 및 점수 평가 (최소 5,100만원 이상 / 희망 5,500만원)
    반환: (score [0~10], salary_display, is_qualified, salary_reason)
    """
    text = f"{salary_text} {title}".replace(",", "")

    # 만원 단위 숫자 추출
    amounts = [int(m) for m in re.findall(r'(\d{4,5})\s*만?원?', text) if 2000 <= int(m) <= 15000]

    if amounts:
        max_amt = max(amounts)
        min_amt = min(amounts)

        if max_amt < SALARY_CRITERIA["min_salary"]:
            return 0, f"연봉 {min_amt:,}~{max_amt:,}만원", False, f"최소 연봉선(5,100만원) 미달 ({max_amt:,}만원)"

        if min_amt >= SALARY_CRITERIA["target_salary"]:
            return 10, f"연봉 {min_amt:,}~{max_amt:,}만원", True, "희망 연봉(5,500만원) 이상 충족 포지션"
        elif min_amt >= SALARY_CRITERIA["min_salary"] or max_amt >= SALARY_CRITERIA["target_salary"]:
            return 9, f"연봉 {min_amt:,}~{max_amt:,}만원", True, "최소 연봉(5,100만원) 충족 및 5,500만원 협상 가능"
        else:
            return 7, f"연봉 {min_amt:,}~{max_amt:,}만원", True, "경력에 따른 5,100만원+ 협의 가능"

    # 명시된 금액이 없는 경우 (회사내규 / 면접후결정)
    is_senior = any(kw in title for kw in ["과장", "차장", "팀장", "센터장", "매니저", "총괄", "책임", "파트장", "실장"])
    has_exp = any(kw in career_str for kw in ["5년", "6년", "7년", "8년", "과장", "차장"])

    if any(kw in title for kw in ["신입", "인턴", "아르바이트", "주부", "사원급", "보조"]):
        return 0, "회사내규 (신입/사원급)", False, "신입/사원급으로 5,100만 미달"

    if is_senior or has_exp:
        return 8, "회사내규 / 협의 (5,100만~6,000만 가능 포지션)", True, "과장~차장/팀장급 직책으로 직전연봉(5,100만) 기반 5,500만원 협상 유력"

    return 7, "회사내규 / 면접 후 결정 (협상 가능)", True, "경력 8년차 과장급 처우 협의 대상"

def evaluate_job_match(title, raw_desc, career_str, sectors):
    """
    직무 및 경력 적합도 평가 (최대 65점: 직무 40점 + 경력 25점)
    반환: (job_score, career_score, match_reasons, matched_tags)
    """
    job_score = 0
    career_score = 0
    match_reasons = []
    matched_tags = []

    combined_text = f"{title} {raw_desc} {sectors}".lower()

    # 1. 직책 및 총괄 관리자 / 사무직 매칭
    if any(k in combined_text for k in ["센터장", "부센터장", "물류센터장", "총괄 매니저", "물류 팀장", "물류팀장"]):
        job_score += 15
        match_reasons.append("물류센터 총괄/팀장 포지션으로 BGF검단 신규센터 셋업 및 상온 총괄 경력과 직결")
        matched_tags.append("물류센터 총괄/팀장")
    elif any(k in combined_text for k in ["운영팀장", "운영 매니저", "operation manager", "area manager", "과장", "차장"]):
        job_score += 14
        match_reasons.append("쿠팡 INC11 Area Manager(과장) 직무와 일치하는 풀필먼트 운영 관리자 포지션")
        matched_tags.append("풀필먼트 운영팀장/AM")
    elif any(k in combined_text for k in ["물류사무", "물류기획", "scm", "자재", "물류관리"]):
        job_score += 13
        match_reasons.append("물류사무·기획 및 5,000 SKUs 재고/SCM 운영 전문성 부합")
        matched_tags.append("물류사무/SCM기획")
    elif any(k in combined_text for k in ["물류센터 운영", "풀필먼트 운영"]):
        job_score += 12
        match_reasons.append("8년 2개월간의 대규모 물류센터 운영 전문성과 높은 직무 일치도")
        matched_tags.append("물류센터 운영관리")

    # 2. 자동화 설비 및 시스템 역량 매칭
    if any(k in combined_text for k in ["자동화", "스마트물류", "shuttle", "셔틀", "미니로드", "scada", "ams", "das", "dps"]):
        job_score += 15
        match_reasons.append("자동화 설비(Shuttle/Miniload/FlowRack 등) 셋업 및 관제 경험과 최적 부합")
        matched_tags.append("자동화 설비 셋업/관제")
    elif any(k in combined_text for k in ["wms", "tms", "oms", "시스템", "프로세스 개선", "sop"]):
        job_score += 10
        match_reasons.append("WMS/TMS 활용 능력 및 SOP 제작을 통한 공정 운영 표준화 역량 어필 가능")
        matched_tags.append("WMS/SOP 표준화")

    # 3. 인력 관리 및 데이터 대시보드
    if any(k in combined_text for k in ["인력관리", "노무", "kpi", "대시보드", "grafana", "power bi", "지표관리"]):
        job_score += 10
        match_reasons.append("일평균 110명 규모 공정 인력 관리 및 대시보드(Grafana/Power BI) 기반 KPI 관리 경험 보유")
        matched_tags.append("110명 인력관리/KPI")

    job_score = min(40, max(20, job_score))

    # 4. 경력 연차 적합도 (조윤호 님: 8년 2개월)
    exp_nums = [int(n) for n in re.findall(r'(\d+)\s*년', career_str)]
    if exp_nums:
        req_exp = exp_nums[0]
        if 5 <= req_exp <= 8:
            career_score = 25
            match_reasons.append(f"요구 경력({req_exp}년 이상)과 조윤호 님의 8년 2개월 경력이 황금 연차 매칭")
            matched_tags.append("황금 연차(8년차)")
        elif req_exp < 5:
            career_score = 21
            match_reasons.append("요구 연차를 상회하는 풍부한 셋업 및 총괄 리더십 보유로 즉시 전력화")
        else:
            career_score = 23
            match_reasons.append(f"요구 경력({req_exp}년)에 부합하는 과장~차장급 포지션")
    else:
        career_score = 23
        match_reasons.append("경력 8년차 과장급 실무 총괄자로서 즉시 현장 투입 가능")

    if not match_reasons:
        match_reasons.append("물류센터 운영, 재고관리, 배차 및 공정 효율화 경험과 전반적 부합")

    return job_score, career_score, match_reasons, matched_tags

def score_job(job):
    """
    단일 공고 종합 평가
    1. 물류 직무 기본 검증
    2. 현장 단순노무/피킹/포장 등 현장직 배제 (요구사항 3)
    3. 미보유 자격증 필수 요구 배제 (요구사항 2)
    4. 요구 경력 초과 배제 (요구사항 2)
    5. 통근 거리 및 연봉 평가
    """
    # 0. 물류 직무 기본 검증
    if not is_valid_logistics_job(job.get("title", ""), job.get("sectors", ""), job.get("raw_desc", "")):
        return None

    # 1. 주 업무가 현장 업무(피킹, 포장, 입출하, 지게차 등)인 경우 배제 (요구사항 3)
    is_field, field_reason = is_field_work_job(
        job.get("title", ""), job.get("raw_desc", ""), job.get("sectors", "")
    )
    if is_field:
        return None

    # 2. 미보유 자격증 필수 요구 배제 (요구사항 2)
    cert_ok, cert_reasons, cert_tags = check_certification_eligibility(
        job.get("title", ""), job.get("raw_desc", "")
    )
    if not cert_ok:
        return None

    # 3. 요구 경력 조건 초과 배제 (요구사항 2)
    exp_ok, exp_reason = check_experience_eligibility(
        job.get("career", ""), job.get("title", ""), job.get("raw_desc", "")
    )
    if not exp_ok:
        return None

    # 4. 통근 거리 평가 (편도 30분 이내)
    commute_score, commute_text, is_commute_ok, commute_details = evaluate_commute(job.get("location", ""))
    if not is_commute_ok:
        return None

    # 5. 연봉 조건 평가 (최소 5,100만+)
    salary_score, salary_display, is_salary_ok, salary_reason = evaluate_salary(
        job.get("salary_text", ""), job.get("title", ""), job.get("career", "")
    )
    if not is_salary_ok:
        return None

    # 6. 직무 및 경력 적합도 평가
    job_score, career_score, match_reasons, matched_tags = evaluate_job_match(
        job.get("title", ""), job.get("raw_desc", "") + " " + job.get("sectors", ""),
        job.get("career", ""), job.get("sectors", "")
    )

    if isinstance(cert_reasons, list) and cert_reasons:
        match_reasons.extend(cert_reasons)
    if isinstance(cert_tags, list) and cert_tags:
        matched_tags.extend(cert_tags)

    total_score = commute_score + salary_score + job_score + career_score

    if total_score < 60:
        return None

    # 맞춤 지원 팁
    strategy_tips = []
    if "자동화" in str(matched_tags):
        strategy_tips.append("쿠팡 인천11센터 셔틀/미니로드 설비 셋업 및 Grafana 대시보드 커스터마이징 성과를 이력서 상단에 강조하세요.")
    if "총괄" in str(matched_tags) or "팀장" in str(matched_tags) or "센터장" in str(matched_tags):
        strategy_tips.append("BGF로지스 검단 상온 총괄 시 로스율 역대 1위(0.05%) 달성 및 110명 인력 관리 경험을 핵심 어필하세요.")
    if "자재" in str(matched_tags) or "scm" in str(matched_tags).lower() or "사무" in str(matched_tags):
        strategy_tips.append("물류관리사 자격과 5,000 SKUs 재고 및 운송사 배차 총괄 관리 실적을 집중 어필하세요.")
    if not strategy_tips:
        strategy_tips.append("신규 센터 셋업 2회 경험과 WMS/KPI 지표 개선 실적을 중심으로 실무형 리더십을 부각하세요.")

    return {
        **job,
        "total_score": total_score,
        "commute_score": commute_score,
        "salary_score": salary_score,
        "job_score": job_score,
        "career_score": career_score,
        "commute_time_text": commute_text,
        "commute_details": commute_details,
        "salary_display": salary_display,
        "salary_reason": salary_reason,
        "match_reasons": match_reasons,
        "matched_tags": list(set(matched_tags)),
        "strategy_tips": " ".join(strategy_tips)
    }

def filter_and_rank_jobs(all_jobs, top_n=10):
    """
    수집된 전체 공고 점수화 및 최상위 N개 추출
    """
    scored_jobs = []
    seen_urls = set()
    seen_titles = set()

    for job in all_jobs:
        url = job.get("url")
        title_norm = re.sub(r'[\s\(\)\[\]]', '', job.get("title", ""))
        
        if url in seen_urls or (job.get("company") and (job.get("company"), title_norm) in seen_titles):
            continue
        seen_urls.add(url)
        if job.get("company"):
            seen_titles.add((job.get("company"), title_norm))

        res = score_job(job)
        if res:
            scored_jobs.append(res)

    scored_jobs.sort(key=lambda x: x["total_score"], reverse=True)

    top_jobs = scored_jobs[:top_n]
    for idx, j in enumerate(top_jobs, start=1):
        j["rank"] = idx

    return top_jobs, len(scored_jobs)
