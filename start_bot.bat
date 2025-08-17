@echo off
echo 디스코드 보안봇 시작 중...
cd /d "c:\새 폴더"

echo 필요한 패키지 설치 중...
pip install -r requirements.txt

echo 봇 실행 중...
python discord_security_bot.py

pause