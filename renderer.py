"""
renderer.py
조윤호 님을 위한 맞춤형 채용공고 HTML 웹 대시보드 생성 모듈
"""

from datetime import datetime
import json

def render_html_dashboard(top_jobs, total_collected, total_qualified, output_path):
    """
    선별된 상위 10개 공고 및 사용자 조건을 바탕으로 독립 실행형 HTML 대시보드 생성
    """
    now_str = datetime.now().strftime("%Y년 %m월 %d일 %H:%M 기준")
    today_date = datetime.now().strftime("%Y.%m.%d")

    avg_score = round(sum(j["total_score"] for j in top_jobs) / len(top_jobs), 1) if top_jobs else 0
    tier1_count = sum(1 for j in top_jobs if "10~15분" in j.get("commute_time_text", "") or "18~25분" in j.get("commute_time_text", ""))

    cards_html = ""
    for j in top_jobs:
        rank = j.get("rank", 1)
        score = j.get("total_score", 0)
        source = j.get("source", "사람인")
        
        # 플랫폼별 뱃지 스타일
        if source == "사람인":
            source_badge = '<span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 border border-blue-200">사람인 Saramin</span>'
            btn_color = "bg-blue-600 hover:bg-blue-700 focus:ring-blue-500"
        elif source == "잡코리아":
            source_badge = '<span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800 border border-orange-200">잡코리아 JobKorea</span>'
            btn_color = "bg-amber-600 hover:bg-amber-700 focus:ring-amber-500"
        else:
            source_badge = '<span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200">리멤버 Remember</span>'
            btn_color = "bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500"

        # 점수 게이지 색상
        if score >= 90:
            score_color = "text-emerald-600 bg-emerald-50 border-emerald-200"
            bar_color = "bg-emerald-500"
        elif score >= 80:
            score_color = "text-blue-600 bg-blue-50 border-blue-200"
            bar_color = "bg-blue-500"
        else:
            score_color = "text-amber-600 bg-amber-50 border-amber-200"
            bar_color = "bg-amber-500"

        # 태그 목록
        tags_html = "".join([f'<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 mr-1.5 mb-1.5">#{t}</span>' for t in j.get("matched_tags", [])])

        # 추천 사유 목록
        reasons_html = "".join([f'<li class="flex items-start text-xs text-slate-700 leading-relaxed mb-1"><svg class="w-3.5 h-3.5 text-emerald-500 mr-1.5 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>{r}</li>' for r in j.get("match_reasons", [])])

        card = f"""
        <div class="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-all duration-200 relative overflow-hidden flex flex-col justify-between">
            <div>
                <!-- 상단 헤더: 순위, 플랫폼, 점수 -->
                <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-2">
                        <span class="w-8 h-8 rounded-full bg-slate-900 text-white font-bold flex items-center justify-center text-sm shadow-sm">{rank}</span>
                        {source_badge}
                    </div>
                    <div class="flex items-center px-3 py-1 rounded-full border {score_color}">
                        <span class="text-xs font-medium mr-1.5">적합도</span>
                        <span class="text-sm font-extrabold">{score}점</span>
                    </div>
                </div>

                <!-- 기업명 및 공고 제목 -->
                <div class="mb-4">
                    <p class="text-xs font-semibold text-slate-500 tracking-wide uppercase mb-1">{j.get("company", "기업명 미상")}</p>
                    <h3 class="text-lg font-bold text-slate-900 leading-snug hover:text-blue-600 transition-colors">
                        <a href="{j.get('url', '#')}" target="_blank" rel="noopener noreferrer">{j.get("title", "")}</a>
                    </h3>
                </div>

                <!-- 3대 핵심 조건 카드 (위치/통근, 연봉, 경력) -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-2.5 bg-slate-50 rounded-xl p-3 mb-4 text-xs">
                    <div class="flex items-start space-x-2">
                        <div class="p-1.5 bg-emerald-100 rounded-lg text-emerald-700 shrink-0">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                        </div>
                        <div>
                            <span class="text-slate-400 block font-medium">통근 (인천역 기준)</span>
                            <span class="font-bold text-slate-800">{j.get("commute_time_text", "")}</span>
                            <span class="text-[11px] text-slate-500 block">{j.get("location", "인천")}</span>
                        </div>
                    </div>
                    <div class="flex items-start space-x-2">
                        <div class="p-1.5 bg-blue-100 rounded-lg text-blue-700 shrink-0">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        </div>
                        <div>
                            <span class="text-slate-400 block font-medium">연봉 조건</span>
                            <span class="font-bold text-slate-800">{j.get("salary_display", "")}</span>
                            <span class="text-[11px] text-slate-500 block">희망 5,500만 / 최소 5,100만</span>
                        </div>
                    </div>
                    <div class="flex items-start space-x-2">
                        <div class="p-1.5 bg-amber-100 rounded-lg text-amber-700 shrink-0">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                        </div>
                        <div>
                            <span class="text-slate-400 block font-medium">경력 요건</span>
                            <span class="font-bold text-slate-800">{j.get("career", "경력 5~10년")}</span>
                            <span class="text-[11px] text-slate-500 block">조윤호 님 경력: 8년 2개월</span>
                        </div>
                    </div>
                </div>

                <!-- 이력서 기반 추천 사유 -->
                <div class="mb-3.5">
                    <span class="text-xs font-bold text-slate-900 block mb-1.5 flex items-center">
                        <svg class="w-3.5 h-3.5 text-blue-600 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"></path></svg>
                        이력서 1:1 맞춤 추천 포인트
                    </span>
                    <ul class="pl-0.5">
                        {reasons_html}
                    </ul>
                </div>

                <!-- 매칭 태그 -->
                <div class="mb-4">
                    {tags_html}
                </div>

                <!-- 지원 전략 팁 -->
                <div class="bg-blue-50/70 border border-blue-100 rounded-xl p-3 mb-4 text-xs text-blue-900">
                    <span class="font-bold flex items-center mb-0.5 text-blue-800">
                        <svg class="w-3.5 h-3.5 mr-1" fill="currentColor" viewBox="0 0 20 20"><path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14H8a4 4 0 01-.82-7.915 4.962 4.962 0 012.82-1.085 4.96 4.96 0 012.82 1.085A4 4 0 0112 14z"></path></svg>
                        윤호 님 맞춤 합격 전략
                    </span>
                    <p class="leading-relaxed text-blue-950">{j.get("strategy_tips", "")}</p>
                </div>
            </div>

            <!-- 하단 버튼: 공고 바로가기 -->
            <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span class="text-[11px] text-slate-400">마감: {j.get("deadline", "상시채용")}</span>
                <a href="{j.get('url', '#')}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg text-white {btn_color} transition-all shadow-sm">
                    {source}에서 공고 확인 & 지원
                    <svg class="w-3.5 h-3.5 ml-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                </a>
            </div>
        </div>
        """
        cards_html += card

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>조윤호 님 채용공고 일별 자동추천 (매일 08:00 최신화)</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/pretendard/1.3.9/static/pretendard.min.css">
    <style>
        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
            background-color: #f8fafc;
        }}
    </style>
</head>
<body class="min-h-screen text-slate-800 antialiased pb-20">

    <!-- 상단 글로벌 네비게이션 -->
    <nav class="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50 shadow-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-inner">
                    YH
                </div>
                <div>
                    <h1 class="text-base font-bold leading-tight flex items-center">
                        조윤호 님 맞춤 채용공고 추천 시스템
                        <span class="ml-2.5 px-2 py-0.5 text-[11px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full">
                            매일 08:00 최신화
                        </span>
                    </h1>
                    <p class="text-[11px] text-slate-400">사람인 · 잡코리아 · 리멤버 실시간 분석 엔진</p>
                </div>
            </div>
            <div class="flex items-center space-x-3">
                <span class="text-xs text-slate-400 hidden sm:inline">{now_str}</span>
                <button onclick="location.reload()" class="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">
                    <svg class="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                    새로고침
                </button>
            </div>
        </div>
    </nav>

    <!-- 메인 컨테이너 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">

        <!-- 프로필 & 핵심 조건 요약 배너 -->
        <div class="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-3xl p-6 sm:p-8 text-white mb-8 shadow-xl relative overflow-hidden">
            <div class="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
                <div class="lg:col-span-8">
                    <div class="flex flex-wrap items-center gap-2 mb-3">
                        <span class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-500/20 text-blue-300 border border-blue-500/30">경력 8년 2개월 (만 35세)</span>
                        <span class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">쿠팡 INC11 과장(Area Manager) & BGF로지스</span>
                        <span class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">센터 셋업 2회(0 to 1)</span>
                    </div>
                    <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
                        조윤호 님을 위한 오늘의 TOP 10 최적 포지션
                    </h2>
                    <p class="text-slate-300 text-sm leading-relaxed max-w-2xl">
                        거주지인 <strong class="text-white">인천역 코아루센트럴시티</strong> 기준 편도 30분 이내 지역, 최소 연봉 <strong class="text-emerald-400">5,100만원 이상</strong>(희망 5,500만원)의 스마트 물류센터 센터장·운영팀장 공고만을 엄선했습니다.
                    </p>
                </div>

                <!-- 4대 핵심 조건 지표 박스 -->
                <div class="lg:col-span-4 grid grid-cols-2 gap-3">
                    <div class="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/10">
                        <span class="text-xs text-slate-300 block mb-1">출퇴근 기준</span>
                        <span class="text-lg font-bold text-emerald-400">편도 30분 이내</span>
                        <span class="text-[11px] text-slate-400 block">인천 중·서·남동·송도 중심</span>
                    </div>
                    <div class="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/10">
                        <span class="text-xs text-slate-300 block mb-1">희망 / 최소연봉</span>
                        <span class="text-lg font-bold text-amber-300">5,500 / 5,100만+</span>
                        <span class="text-[11px] text-slate-400 block">과장·차장급 협상선</span>
                    </div>
                    <div class="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/10">
                        <span class="text-xs text-slate-300 block mb-1">일별 엄선 공고</span>
                        <span class="text-lg font-bold text-blue-400">10개 포지션</span>
                        <span class="text-[11px] text-slate-400 block">매일 08:00 자동 갱신</span>
                    </div>
                    <div class="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/10">
                        <span class="text-xs text-slate-300 block mb-1">평균 적합도</span>
                        <span class="text-lg font-bold text-white">{avg_score}점</span>
                        <span class="text-[11px] text-slate-400 block">100점 만점 기준</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 3개 플랫폼 탐색 현황 바 -->
        <div class="flex flex-wrap items-center justify-between bg-white rounded-2xl px-6 py-4 shadow-sm border border-slate-200 mb-8 gap-4">
            <div class="flex items-center space-x-6 text-xs text-slate-600">
                <span class="font-bold text-slate-900 text-sm">연동 플랫폼:</span>
                <span class="inline-flex items-center"><span class="w-2.5 h-2.5 rounded-full bg-blue-500 mr-2"></span>사람인 (Saramin)</span>
                <span class="inline-flex items-center"><span class="w-2.5 h-2.5 rounded-full bg-orange-500 mr-2"></span>잡코리아 (JobKorea)</span>
                <span class="inline-flex items-center"><span class="w-2.5 h-2.5 rounded-full bg-indigo-500 mr-2"></span>리멤버 (Remember)</span>
            </div>
            <div class="text-xs text-slate-500">
                총 수집 공고: <span class="font-semibold text-slate-800">{total_collected}건</span> 중 조건 충족 <span class="font-semibold text-blue-600">{total_qualified}건</span> → <strong class="text-slate-900 font-bold">최상위 10건 선별 완료</strong>
            </div>
        </div>

        <!-- 추천 공고 카드 그리드 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {cards_html}
        </div>

        <!-- 하단 가이드 및 스케줄러 상태 -->
        <div class="mt-12 bg-slate-100 rounded-2xl p-6 border border-slate-200 text-slate-600 text-xs">
            <div class="flex items-start space-x-3">
                <div class="p-2 bg-slate-200 rounded-xl text-slate-700 shrink-0 mt-0.5">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                </div>
                <div>
                    <h4 class="font-bold text-slate-800 text-sm mb-1">매일 08:00 자동 최신화 안내</h4>
                    <p class="leading-relaxed mb-2">
                        본 시스템은 Windows 작업 스케줄러를 통해 매일 아침 08:00에 사람인, 잡코리아, 리멤버의 최신 채용공고를 자동으로 탐색·평가하여 이 웹페이지를 갱신합니다.
                    </p>
                    <p class="leading-relaxed">
                        수동으로 즉시 새로운 공고를 확인하고 싶으신 경우 프로젝트 폴더의 <code class="bg-white px-2 py-0.5 rounded border border-slate-300 font-mono text-slate-800">run_recommendation.bat</code>을 더블클릭하시면 언제든지 즉시 최신화됩니다.
                    </p>
                </div>
            </div>
        </div>

    </main>

    <!-- 하단 카피라이트 -->
    <footer class="mt-12 text-center text-xs text-slate-400">
        조윤호 님 전용 커스텀 채용공고 추천 시스템 · Powered by Saramin, JobKorea & Remember Career
    </footer>

</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[대시보드 생성 완료] 경로: {output_path}")
    return output_path
