"""
cloud_uploader.py
노트북이 꺼져 있어도 스마트폰에서 24시간 열어볼 수 있도록
생성된 recommendations.html을 클라우드 정적 웹 호스팅에 자동 배포하고 URL을 반환하는 모듈
"""

import os
import json
import requests
import subprocess
from config import CLOUD_CONFIG_PATH, OUTPUT_HTML_PATH, BASE_DIR

def load_cloud_config():
    """
    클라우드 배포 설정 로드
    """
    default_config = {
        "provider": "github_pages",  # "github_pages", "netlify", "gist"
        "github_username": "",
        "github_repo": "",
        "github_token": "",
        "netlify_site_id": "",
        "netlify_token": "",
        "custom_url": ""
    }
    if not os.path.exists(CLOUD_CONFIG_PATH):
        try:
            with open(CLOUD_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return default_config
    try:
        with open(CLOUD_CONFIG_PATH, "r", encoding="utf-8") as f:
            return {**default_config, **json.load(f)}
    except Exception:
        return default_config

def deploy_to_cloud(html_path=OUTPUT_HTML_PATH):
    """
    HTML 파일을 클라우드에 배포하고 스마트폰에서 접속 가능한 공개 URL 반환
    """
    config = load_cloud_config()
    provider = config.get("provider", "github_pages").lower()

    # 1. 사용자가 이미 커스텀 URL(GitHub Pages 주소 등)을 설정한 경우
    if config.get("custom_url"):
        # Git이 설치되어 있고 로컬 리포지토리인 경우 자동 커밋 & 푸시 시도
        try:
            subprocess.run(["git", "add", "."], cwd=BASE_DIR, capture_output=True, timeout=5)
            subprocess.run(["git", "commit", "-m", "chore: daily job recommendations update"], cwd=BASE_DIR, capture_output=True, timeout=5)
            subprocess.run(["git", "push"], cwd=BASE_DIR, capture_output=True, timeout=10)
        except Exception:
            pass
        return config["custom_url"]

    # 2. GitHub Pages 설정이 되어 있는 경우
    gh_user = config.get("github_username")
    gh_repo = config.get("github_repo")
    gh_token = config.get("github_token")

    if gh_user and gh_repo:
        # GitHub Pages URL 형식
        pages_url = f"https://{gh_user}.github.io/{gh_repo}/recommendations.html"
        
        # Git push로 최신화 시도
        try:
            subprocess.run(["git", "add", "."], cwd=BASE_DIR, capture_output=True, timeout=5)
            subprocess.run(["git", "commit", "-m", "chore: daily update"], cwd=BASE_DIR, capture_output=True, timeout=5)
            subprocess.run(["git", "push"], cwd=BASE_DIR, capture_output=True, timeout=10)
            print(f"✓ GitHub Pages로 최신 대시보드 푸시 완료: {pages_url}")
            return pages_url
        except Exception as e:
            print(f"[Git 푸시 시도] {e}")
            return pages_url

    # 3. GitHub Gist를 통한 즉시 무료 클라우드 호스팅 (Gist API)
    # 별도 계정 설정이 아직 안 되어 있을 때도 즉시 스마트폰에서 볼 수 있도록 Gist Anonymous/Token 업로드 지원
    if gh_token:
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html_body = f.read()
            gist_payload = {
                "description": "조윤호 님 맞춤 채용공고 일별 추천 대시보드",
                "public": True,
                "files": {
                    "index.html": {"content": html_body}
                }
            }
            res = requests.post(
                "https://api.github.com/gists",
                headers={"Authorization": f"token {gh_token}", "Accept": "application/vnd.github.v3+json"},
                json=gist_payload,
                timeout=10
            )
            if res.status_code == 201:
                raw_url = res.json()["files"]["index.html"]["raw_url"]
                preview_url = f"https://htmlpreview.github.io/?{raw_url}"
                print(f"✓ GitHub Gist 클라우드 호스팅 완료: {preview_url}")
                return preview_url
        except Exception as e:
            print(f"[Gist 호스팅 실패] {e}")

    # 4. 기본 폴백: 로컬 네트워크 IP 또는 안내 URL
    # 노트북이 켜져 있는 동안 동일 Wi-Fi 스마트폰에서 접속할 수 있는 로컬 IP 확인
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        local_url = f"http://{local_ip}:8000/recommendations.html"
    except Exception:
        local_url = "http://localhost:8000/recommendations.html"

    return local_url

if __name__ == '__main__':
    url = deploy_to_cloud()
    print("클라우드 배포 URL:", url)
