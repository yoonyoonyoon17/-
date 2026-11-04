# setup_schedule.ps1 (한글 경로 완전 보존)
$taskName = "JobRecommendation_Daily_0800"
$workingDir = "c:\Users\USER\OneDrive\Desktop\프로젝트_일 별채용공고 자동추천"
$batPath = "$workingDir\run_scheduled.bat"
$pythonPath = "C:\Users\USER\AppData\Local\Programs\Python\Python312\python.exe"

Write-Host "스케줄러 작업 재등록 시작..." -ForegroundColor Cyan

# 기존 작업 삭제
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# 작업 생성: python.exe로 run.py를 직접 실행하고 작업 폴더(WorkingDirectory)를 지정
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "run.py --no-browser" -WorkingDirectory $workingDir
$trigger = New-ScheduledTaskTrigger -Daily -At "08:00AM"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "조윤호 님 매일 08:00 채용공고 자동추천 갱신" -Force

Write-Host "스케줄러 재등록 완료!" -ForegroundColor Green
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State
