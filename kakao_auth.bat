@echo off
chcp 65001 > nul
start "" "https://kauth.kakao.com/oauth/authorize?client_id=1e78d5a5747ccdfc981c16ba97515fc1&redirect_uri=https://localhost:5000&response_type=code&scope=talk_message"
