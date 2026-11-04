"""
kakao_setup.py
카카오톡 '나에게 보내기' 원클릭 토큰 발급 및 연동 마법사
"""

import sys
import os
import json
import webbrowser
import requests
from config import KAKAO_CONFIG_PATH

# UTF-8 출력 설정
sys.stdout.reconfigure(encoding='utf-8')

REDIRECT_URI = "https://localhost:5000"

def setup_kakao():
    print("=" * 65)
    print("  카카오톡 '나에게 채용공고 알림 보내기' 간편 연동 마법사")
    print("=" * 65)
    print("\n[안내] 매일 아침 08:00에 조윤호 님의 카카오톡으로 채용공고 링크를 보내기 위해")
    print("카카오 디벨로퍼스(무료) 앱 설정이 필요합니다. (1분 소요)\n")

    print("1단계: 카카오 디벨로퍼스 사이트 열기")
    print("   → 브라우저에서 https://developers.kakao.com 에 로그인합니다.")
    print("   → [내 애플리케이션] > [애플리케이션 추가하기] (이름: 채용공고알림 등 자유롭게)")
    print("   → [앱 설정] > [요약 정보]에서 'REST API 키'를 복사합니다.")
    print("   → [제품 설정] > [카카오 로그인] > 활성화 설정 'ON'")
    print("   → [카카오 로그인] > [Redirect URI] 등록에 다음 주소를 추가합니다:")
    print(f"        👉 {REDIRECT_URI}")
    print("   → [카카오 로그인] > [동의항목] > '카카오톡 메시지 전송(talk_message)'을 '이용 중 동의' 또는 '필수 동의'로 설정\n")

    # 기존 설정이 있으면 표시
    existing_rest_key = ""
    if os.path.exists(KAKAO_CONFIG_PATH):
        try:
            with open(KAKAO_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_rest_key = data.get("rest_api_key", "")
        except Exception:
            pass

    prompt_msg = f"REST API 키를 입력하세요 [{existing_rest_key}]: " if existing_rest_key else "REST API 키를 입력하세요: "
    rest_api_key = input(prompt_msg).strip()
    if not rest_api_key and existing_rest_key:
        rest_api_key = existing_rest_key

    if not rest_api_key:
        print("[오류] REST API 키가 입력되지 않았습니다. 프로그램을 종료합니다.")
        return

    # 2단계: 인증 코드(Code) 발급을 위한 브라우저 오픈
    auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={rest_api_key}&redirect_uri={REDIRECT_URI}&response_type=code&scope=talk_message"
    print("\n2단계: 카카오 계정 로그인 및 권한 동의")
    print("브라우저에서 로그인 창을 엽니다. 로그인 후 동의를 완료해 주세요...")
    webbrowser.open(auth_url)

    print("\n동의 완료 후 브라우저 주소창이 'https://localhost:5000/?code=xxxxxx...' 형태로 바뀝니다.")
    print("(브라우저에 '연결할 수 없음' 에러가 떠도 정상입니다! 주소창의 URL만 복사하시면 됩니다.)")
    redirected_url = input("\n주소창 전체 URL 또는 code 값을 복사하여 붙여넣으세요: ").strip()

    if "code=" in redirected_url:
        code = redirected_url.split("code=")[1].split("&")[0].strip()
    else:
        code = redirected_url

    if not code:
        print("[오류] 인가 코드(Code)가 입력되지 않았습니다.")
        return

    # 3단계: Access Token 및 Refresh Token 발급
    print("\n3단계: 토큰 발급 진행 중...")
    token_url = "https://kauth.kakao.com/oauth/token"
    token_payload = {
        "grant_type": "authorization_code",
        "client_id": rest_api_key,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    try:
        res = requests.post(token_url, data=token_payload, timeout=10)
        res_data = res.json()

        if "access_token" in res_data:
            config_data = {
                "rest_api_key": rest_api_key,
                "access_token": res_data["access_token"],
                "refresh_token": res_data.get("refresh_token", ""),
                "token_type": res_data.get("token_type", "bearer"),
                "scope": res_data.get("scope", "")
            }
            with open(KAKAO_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)

            print("✓ [성공] 카카오톡 토큰이 발급되어 안전하게 저장되었습니다!")
            print(f"  설정 파일: {KAKAO_CONFIG_PATH}")

            # 4단계: 테스트 메시지 발송
            print("\n4단계: 조윤호 님의 카카오톡으로 테스트 메시지를 발송합니다...")
            from notifier import send_kakao_recommendation_message
            test_jobs = [
                {"rank": 1, "total_score": 80, "company": "에이원엔지니어링코리아", "title": "[인천 송도] 자재/물류 팀장 경력직 모집", "commute_time_text": "편도 약 20~25분"}
            ]
            test_url = "https://github.com"
            success = send_kakao_recommendation_message(test_jobs, test_url)
            if success:
                print("🎉 축하합니다! 스마트폰 카카오톡 '나와의 채팅방'을 확인해 보세요. 메시지가 도착했습니다!")
            else:
                print("메시지 발송 테스트에 실패했습니다. 동의항목에서 '카카오톡 메시지 전송'이 체크되었는지 확인하세요.")
        else:
            print(f"[토큰 발급 실패] {res_data}")
    except Exception as e:
        print(f"[통신 에러] {e}")

if __name__ == '__main__':
    setup_kakao()
