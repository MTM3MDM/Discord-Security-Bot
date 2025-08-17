@echo off
chcp 65001 >nul

echo ========================================
echo   Discord 보안봇 설정 검증
echo ========================================
echo.

echo 설정을 검증하는 중입니다...
echo.

python setup_validator.py

echo.
echo 검증 완료!
pause