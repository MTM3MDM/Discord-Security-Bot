# 🛡️ Discord 보안봇

AI 기반 지능형 Discord 서버 보안 시스템

## ⚡ 빠른 시작

1. `.env.example`을 복사해서 `.env` 파일 생성
2. `.env` 파일에 Discord 토큰과 Gemini API 키 입력
3. `run_discord_bot.bat` 실행

## 🔑 필요한 키

- **Discord Bot Token**: [Discord Developer Portal](https://discord.com/developers/applications)에서 생성
- **Gemini API Key**: [Google AI Studio](https://makersuite.google.com/app/apikey)에서 생성

## 📁 주요 파일

- `discord_bot.py` - 메인 봇 프로그램
- `core_ai_system.py` - AI 판사 시스템
- `advanced_user_system.py` - 사용자 관리
- `natural_language_command_system.py` - 자연어 처리
- `run_discord_bot.bat` - 실행 스크립트

## 🤖 주요 기능

- 실시간 AI 위협 탐지
- 자연어 명령 처리
- 사용자 신뢰도 관리
- GUI 제어판
- 감정 및 행동 분석

## 📝 자연어 명령 예시

```
"위험한 사용자들 보여줘"
"서버 통계 알려줘"
"보안 상태 확인해줘"
```

## ❗ 문제 해결

자세한 설치 및 문제 해결 가이드는 `SETUP_GUIDE.md`를 참조하세요.

## 📊 시스템 요구사항

- Python 3.8+
- 최소 2GB RAM
- 인터넷 연결 (Gemini API 사용)