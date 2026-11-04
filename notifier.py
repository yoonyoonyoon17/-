"""
notifier.py
카카오톡 '나에게 보내기' 메시지 자동 발송 모듈 (하이퍼링크 활성화 개선 버전)
"""

import os
import json
import requests
from datetime import datetime
from config import KAKAO_CONFIG_PATH

def load_kakao_tokens():
    """
    저장된 카카오 토큰 정보 로드
    """
    if not os.path.exists(KAKAO_CONFIG_PATH):
        return None
    try:
        with open(KAKAO_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[카카오 설정 로드 실패] {e}")
        return None

def save_kakao_tokens(token_data):
    """
    갱신된 카카오 토큰 정보 저장
    """
    try:
        with open(KAKAO_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(token_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[카카오 설정 저장 실패] {e}")

def refresh_kakao_token(token_data):
    """
    Refresh Token을 사용하여 새로운 Access Token 자동 갱신
    """
    refresh_url = "https://kauth.kakao.com/oauth/token"
    client_id = token_data.get("rest_api_key")
    refresh_token = token_data.get("refresh_token")

    if not client_id or not refresh_token:
        print("[카카오 토큰 갱신 실패] rest_api_key 또는 refresh_token이 없습니다.")
        return None

    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token
    }

    try:
        res = requests.post(refresh_url, data=data, timeout=10)
        res_data = res.json()
        if "access_token" in res_data:
            token_data["access_token"] = res_data["access_token"]
            if "refresh_token" in res_data:
                token_data["refresh_token"] = res_data["refresh_token"]
            save_kakao_tokens(token_data)
            print("[카카오 토큰 갱신 성공] 카카오 Access Token이 성공적으로 갱신되었습니다.")
            return token_data
        else:
            print(f"[카카오 토큰 갱신 오류] {res_data}")
            return None
    except Exception as e:
        print(f"[카카오 토큰 갱신 예외] {e}")
        return None

def _send_kakao_chunk(jobs_chunk, chunk_title, footer_text, token_data, dashboard_url):
    """
    지정된 공고 묶음(1~5위 또는 6~10위)을 카카오톡 메시지로 발송하는 내부 헬퍼
    """
    access_token = token_data.get("access_token")
    lines = []
    lines.append("📍 인천역 30분권 / 최소연봉 5,100만원+ 엄선")
    lines.append("🚜 지게차·건설기계 우대 / 현장단순노무 배제")
    lines.append("=" * 24)

    for j in jobs_chunk:
        rank = j.get("rank", 1)
        score = j.get("total_score", 0)
        source = j.get("source", "사람인")
        corp = j.get("company", "기업")
        job_title = j.get("title", "")
        if len(job_title) > 24:
            job_title = job_title[:22] + ".."
        commute = j.get("commute_time_text", "")
        if "(" in commute:
            commute = commute.split("(")[0].strip()
        salary = j.get("salary_display", "협의")
        url = j.get("url", "")

        lines.append(f"\n【{rank}위 ({score}점)】 [{source}] {corp}")
        lines.append(f"  직무: {job_title}")
        lines.append(f"  통근: {commute} | {salary}")
        if url:
            lines.append(f"  👉 바로가기: {url}")

    lines.append("\n" + "=" * 24)
    lines.append(footer_text)
    description = "\n".join(lines)

    template_object = {
        "object_type": "text",
        "text": f"{chunk_title}\n\n{description}",
        "link": {
            "web_url": dashboard_url,
            "mobile_web_url": dashboard_url
        },
        "button_title": "오늘의 추천 대시보드 보기"
    }

    send_url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "template_object": json.dumps(template_object, ensure_ascii=False)
    }

    res = requests.post(send_url, headers=headers, data=payload, timeout=10)

    # 토큰 만료(401) 시 자동 갱신 후 재전송
    if res.status_code == 401:
        print("[카카오 토큰 만료 감지] 토큰을 자동 갱신하고 재전송합니다...")
        token_data = refresh_kakao_token(token_data)
        if token_data and "access_token" in token_data:
            headers["Authorization"] = f"Bearer {token_data['access_token']}"
            res = requests.post(send_url, headers=headers, data=payload, timeout=10)

    return res.status_code == 200, token_data

def send_kakao_recommendation_message(top_jobs, web_dashboard_url=""):
    """
    카카오톡 '나에게 보내기' API로 1위부터 10위까지 모든 추천 포지션을
    글자 수 제한이나 잘림 없이 2회 분할(1~5위, 6~10위)로 완벽 전송
    """
    token_data = load_kakao_tokens()
    if not token_data:
        print("[카카오톡 알림 안내] 카카오 설정(kakao_config.json)이 없습니다.")
        return False

    access_token = token_data.get("access_token")
    if not access_token:
        token_data = refresh_kakao_token(token_data)
        if not token_data:
            return False

    now_str = datetime.now().strftime("%Y년 %m월 %d일")
    dashboard_url = "https://yoonyoonyoon17.github.io/-/index.html"

    has_more = len(top_jobs) > 5

    # 1. 1~5위 메시지 전송
    chunk1 = top_jobs[:5]
    title1 = f"📢 [조윤호 님 채용공고] {now_str} TOP 1~5위" if has_more else f"📢 [조윤호 님 채용공고] {now_str} TOP 추천 포지션"
    footer1 = "※ 이어지는 6~10위 공고는 바로 아래 메시지에서 확인하실 수 있습니다." if has_more else "※ 전체 상세 분석 및 이력서 공략 팁은 대시보드에서 제공됩니다."

    ok1, token_data = _send_kakao_chunk(chunk1, title1, footer1, token_data, dashboard_url)

    # 2. 6~10위 메시지 전송 (5개 초과 시 즉시 발송)
    ok2 = True
    if has_more:
        import time
        time.sleep(0.5)  # 카카오 순차 수신 보장
        chunk2 = top_jobs[5:10]
        title2 = f"📢 [조윤호 님 채용공고] {now_str} TOP 6~10위"
        footer2 = "※ 전체 1~10위 상세 분석 및 이력서 공략 팁은 대시보드에서 제공됩니다."
        ok2, token_data = _send_kakao_chunk(chunk2, title2, footer2, token_data, dashboard_url)

    if ok1 and ok2:
        print("[카카오톡 발송 성공] 1위부터 10위까지 전체 추천 공고(1~5위, 6~10위)가 카카오톡으로 완벽 전송되었습니다!")
        return True
    else:
        print(f"[카카오톡 발송 결과] 1~5위 성공: {ok1}, 6~10위 성공: {ok2}")
        return ok1 or ok2
