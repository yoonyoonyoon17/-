import subprocess
import sys

task_name = 'JobRecommendation_Daily_0800'
bat_path = r'c:\Users\USER\OneDrive\Desktop\프로젝트_일 별채용공고 자동추천\run_scheduled.bat'

# Delete old task if exists
subprocess.run(['schtasks', '/delete', '/tn', task_name, '/f'], capture_output=True)

# Register with schtasks
cmd = [
    'schtasks', '/create',
    '/tn', task_name,
    '/tr', f'cmd.exe /c "{bat_path}"',
    '/sc', 'daily',
    '/st', '08:00',
    '/f'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='cp949', errors='ignore')
print('Return code:', res.returncode)
print('Output:', res.stdout)
if res.stderr:
    print('Error:', res.stderr)

# Verify task
check = subprocess.run(['schtasks', '/query', '/tn', task_name, '/fo', 'list'], capture_output=True, text=True, encoding='cp949', errors='ignore')
print(check.stdout)
