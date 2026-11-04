"""
config.py
조윤호 님의 이력서 프로필 및 맞춤형 공고 추천 조건 설정 파일
(자격요건 초과 배제, 현장직 제외/사무관리직 중심, 출퇴근 30분, 5100만+ 기준)
"""

import os

# 1. 구직자 기본 정보 및 이력서 프로필
USER_PROFILE = {
    "name": "조윤호",
    "age": 36,
    "birth_year": 1991,
    "total_experience_months": 98,  # 8년 2개월
    "total_experience_years": 8.2,   # 만 8.2년
    "max_experience_years": 8.5,     # 요구 최소 경력이 8.5년(9년 이상 등)을 초과하면 자격 미달로 탈락
    "current_level": "과장 / 매니저 (Area Manager)",
    "target_roles": [
        "물류센터 센터장", "물류센터 운영팀장", "물류 과장", "물류 차장",
        "풀필먼트 운영 총괄", "스마트 물류센터 관리자", "물류 자동화 설비 운영/관제",
        "SCM 물류기획", "Warehouse Manager", "Operation Manager",
        "물류사무", "물류운영 관리자", "재고관리 관리자", "자재 관리자"
    ],
    # 실제 보유 자격증 목록 (이력서 기준 100% 팩트 기반)
    "held_certifications": [
        "물류관리사",
        "유통관리사 2급", "유통관리사",
        "무역영어 1급", "무역영어",
        "마케팅관리사",
        "한국사능력검정시험 1급",
        "1종보통운전면허", "운전면허",
        "건설기계조종사면허", "건설기계조종사 면허"
    ],
    # 미보유 자격증 목록 (공고에서 필수 또는 주요 자격으로 요구 시 무조건 배제)
    "unheld_certifications": [
        "보세사", "bonded goods specialist",
        "관세사",
        "원산지관리사",
        "국제물류사",
        "위험물안전관리자", "위험물기능사", "위험물운송자", "위험물",
        "화물운송종사자격증", "화물운송종사자",
        "1종대형", "대형면허", "트레일러",
        "소방설비기사", "소방안전관리자", "소방",
        "산업안전기사", "산업안전산업기사", "산업안전",
        "전기기사", "전기산업기사", "전기",
        "공조냉동기계기사",
        "지게차운전기능사", "지게차운전", "지게차면허", "지게차 자격"  # 지게차 운전 자격 필수 공고 배제
    ],
    "skills": [
        "WMS", "TMS", "OMS", "SCADA", "AMS", "WAMAS",
        "DPS", "DAS", "FlowRack", "Shuttle", "Miniload",
        "신규 센터 셋업 (0 to 1)", "운영 효율화 (1 to 10)", "인력 관리 (110명 규모)",
        "운영 KPI 관리", "공정 SOP 제작", "Power BI", "Tableau", "Grafana 대시보드",
        "물류관리사", "유통관리사 2급", "무역영어 1급"
    ]
}

# 2. 통근 거리 및 거주지 기준 (인천역 코아루센트럴시티)
LOCATION_CRITERIA = {
    "home_address": "인천 중구 선린동 (인천역 코아루센트럴시티)",
    "max_commute_minutes": 30,
    
    # Tier 1 (자가 5~15분 / 대중교통 15분 내외 - 초근접)
    "tier1_exact": [
        "인천 중구", "인천동구", "인천 동구", "인천 미추홀구", "인천미추홀구",
        "항동", "신흥동", "북항", "남항", "인천항", "송림동", "주안동", "도화동", "숭의동", "학익동"
    ],
    
    # Tier 2 (자가 15~25분 / 전철 20분대 - 최적 통근권)
    "tier2_exact": [
        "인천 서구", "인천서구", "원창동", "청라", "가좌동", "석남동",
        "인천 연수구", "인천연수구", "송도", "송도동", "옥련동", "동춘동",
        "인천 남동구", "인천남동구", "남동공단", "고잔동", "논현동", "구월동",
        "인천 부평구", "인천 계양구"
    ],
    
    # Tier 3 (자가 25~32분 - 출퇴근 가능 마지노선)
    "tier3_exact": [
        "검단", "오류동", "검단일반산단",
        "부천", "부천시", "오정동", "삼정동",
        "시흥", "시흥시", "정왕동", "시화", "배곧", "신천동", "은계",
        "김포시 고촌", "고촌물류단지"
    ]
}

# 3. 연봉 필터링 조건 (단위: 만원)
SALARY_CRITERIA = {
    "target_salary": 5500,  # 희망 연봉 5,500만원
    "min_salary": 5100,     # 최소 연봉 5,100만원
    "allow_negotiable_for_senior": True
}

# 4. 수집 검색 키워드 목록 (현장 단순직 대신 물류 사무/운영/관리직 위주 검색)
SEARCH_KEYWORDS = [
    "물류센터 운영",
    "풀필먼트 운영",
    "물류사무",
    "물류 과장",
    "물류센터 센터장",
    "물류 관리자",
    "SCM 물류"
]

# 5. 추천 공고 수
DAILY_RECOMMENDATION_LIMIT = 10

# 프로젝트 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_HTML_PATH = os.path.join(BASE_DIR, "recommendations.html")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 클라우드 호스팅 및 카카오톡 설정 파일 경로
KAKAO_CONFIG_PATH = os.path.join(BASE_DIR, "kakao_config.json")
CLOUD_CONFIG_PATH = os.path.join(BASE_DIR, "cloud_config.json")
