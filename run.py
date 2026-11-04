"""
run.py
일별 채용공고 자동 추천 메인 실행 파이프라인
- 사람인, 잡코리아, 리멤버 실시간 공고 수집
- 자격증 요건(보세사 등 미보유 자격 배제) 및 출퇴근 30분, 연봉 5,100만+ 정밀 필터링
- 상위 10개 최적 포지션 선별 및 HTML 대시보드 생성
- 클라우드 정적 웹 호스팅 배포 (노트북 꺼짐 대비 스마트폰 24시간 접속 보장)
- 스마트폰 카카오톡 '나에게 보내기' 메시지 자동 발송
"""

import sys
import os
import argparse
import webbrowser
from datetime import datetime

# UTF-8 표준 출력 설정
sys.stdout.reconfigure(encoding='utf-8')

# 내부 모듈 임포트
from config import SEARCH_KEYWORDS, DAILY_RECOMMENDATION_LIMIT, OUTPUT_HTML_PATH, BASE_DIR
from scrapers.saramin import fetch_saramin_jobs
from scrapers.jobkorea import fetch_jobkorea_jobs
from scrapers.remember import fetch_remember_jobs
from matcher import filter_and_rank_jobs
from renderer import render_html_dashboard
from cloud_uploader import deploy_to_cloud
from notifier import send_kakao_recommendation_message

def run_pipeline(open_browser=True):
    print("=" * 65)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 조윤호 님 맞춤 채용공고 추천 시스템 가동")
    print("=" * 65)
    print(f"▶ 대상 플랫폼: 사람인(Saramin), 잡코리아(JobKorea), 리멤버(Remember)")
    print(f"▶ 거주지 기준: 인천역 코아루센트럴시티 (편도 30분 이내 집중)")
    print(f"▶ 연봉 기준: 최소 5,100만원 이상 (희망 5,500만원 / 과장~차장급)")
    print(f"▶ 자격 요건: 미보유 자격(보세사 등) 엄격 배제 / 물류관리사·유통관리사 부합")
    print(f"▶ 탐색 키워드: {', '.join(SEARCH_KEYWORDS)}")
    print("-" * 65)

    all_jobs = []

    # 1. 사람인 수집
    print("\n[1/5] 사람인(Saramin) 최신 공고 수집 중...")
    saramin_count = 0
    for kw in SEARCH_KEYWORDS:
        jobs_ic = fetch_saramin_jobs(kw, location_code="102000", max_pages=1)
        all_jobs.extend(jobs_ic)
        saramin_count += len(jobs_ic)
    for kw in ["부천 물류", "시흥 물류"]:
        jobs_near = fetch_saramin_jobs(kw, location_code="", max_pages=1)
        all_jobs.extend(jobs_near)
        saramin_count += len(jobs_near)
    print(f"  → 사람인 수집 완료: {saramin_count}건")

    # 2. 잡코리아 수집
    print("\n[2/5] 잡코리아(JobKorea) 최신 공고 수집 중...")
    jk_count = 0
    for kw in SEARCH_KEYWORDS:
        jobs = fetch_jobkorea_jobs(kw, local_code="B000", max_pages=2)
        all_jobs.extend(jobs)
        jk_count += len(jobs)
    for kw in ["물류센터 과장", "물류센터 센터장", "풀필먼트 운영"]:
        jobs = fetch_jobkorea_jobs(kw, local_code="", max_pages=1)
        all_jobs.extend(jobs)
        jk_count += len(jobs)
    print(f"  → 잡코리아 수집 완료: {jk_count}건")

    # 3. 리멤버 커리어 수집
    print("\n[3/5] 리멤버(Remember) 프리미엄 경력 공고 수집 중...")
    rem_count = 0
    for kw in ["인천 물류", "물류센터", "물류 운영", "풀필먼트", "SCM", "물류 관리자", "물류 과장"]:
        jobs = fetch_remember_jobs(kw, max_pages=1, per_page=30)
        all_jobs.extend(jobs)
        rem_count += len(jobs)
    print(f"  → 리멤버 수집 완료: {rem_count}건")

    total_collected = len(all_jobs)
    print(f"\n총 원시 공고 수집: {total_collected}건")

    # 4. 이력서 기반 매칭 & 필터링 & 랭킹
    print("\n[4/5] 이력서 1:1 정밀 매칭 (자격증·거리·연봉 엄격 필터링) 실행 중...")
    top_jobs, total_qualified = filter_and_rank_jobs(all_jobs, top_n=DAILY_RECOMMENDATION_LIMIT)
    print(f"  → 30분 이내 & 5,100만+ & 자격요건 충족 공고: {total_qualified}건")
    print(f"  → 최종 엄선된 오늘의 추천 포지션: {len(top_jobs)}개")

    # 5. HTML 웹 대시보드 렌더링
    print("\n[5/5] HTML 웹 대시보드 생성 및 배포/전송 진행 중...")
    dashboard_file = render_html_dashboard(top_jobs, total_collected, total_qualified, OUTPUT_HTML_PATH)
    print(f"  ✓ 로컬 대시보드 생성 완료: {dashboard_file}")

    # 6. 클라우드 정적 웹 호스팅 배포 (스마트폰 24시간 접속 URL 확보)
    cloud_url = deploy_to_cloud(dashboard_file)
    print(f"  ✓ 스마트폰 24시간 접속 웹 링크: {cloud_url}")

    # 7. 카카오톡 메시지 발송
    print("\n▶ 카카오톡 메시지 전송 시도 중...")
    kakao_sent = send_kakao_recommendation_message(top_jobs, cloud_url)
    if not kakao_sent:
        print("  ℹ 카카오톡 미연동 상태입니다. 스마트폰 알림을 받으시려면 setup_kakao.bat를 1회 실행해 주세요.")

    # 브라우저 자동 오픈
    if open_browser:
        print("\n▶ 웹 브라우저에서 추천 대시보드를 엽니다...")
        webbrowser.open(f"file:///{dashboard_file.replace(os.sep, '/')}")

    print("\n" + "=" * 65)
    print("오늘의 추천 TOP 10 요약:")
    for j in top_jobs:
        print(f"  [{j['rank']}위 - {j['total_score']}점] [{j['source']}] {j['company']} | {j['title']}")
        print(f"       위치: {j['location']} ({j['commute_time_text']}) | {j['salary_display']}")
    print("=" * 65)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="일별 채용공고 자동 추천 파이프라인")
    parser.add_argument("--no-browser", action="store_true", help="브라우저 자동 열기 비활성화 (스케줄러 모드)")
    args = parser.parse_args()

    run_pipeline(open_browser=not args.no_browser)
