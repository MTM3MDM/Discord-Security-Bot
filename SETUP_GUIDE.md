# 🛡️ Discord 보안봇 설정 가이드

## 📋 설치 전 준비사항

### 1. Discord 봇 토큰 생성
1. [Discord Developer Portal](https://discord.com/developers/applications) 접속
2. "New Application" 클릭하여 새 애플리케이션 생성
3. 좌측 "Bot" 메뉴 클릭
4. "Add Bot" 버튼 클릭
5. "Token" 섹션에서 "Copy" 버튼을 클릭하여 토큰 복사
6. **⚠️ 이 토큰을 안전하게 보관하세요!**

### 2. Google Gemini API 키 생성
1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. "Create API Key" 클릭
3. API 키를 복사하여 안전하게 보관
4. **⚠️ 이 API 키를 안전하게 보관하세요!**

## 🚀 설치 및 설정

### 1단계: 환경변수 설정
```bash
# .env.example 파일을 .env로 복사
copy .env.example .env

# .env 파일을 편집기로 열어서 실제 값들로 변경
# DISCORD_TOKEN=실제_디스코드_봇_토큰
# GEMINI_API_KEY=실제_지미니_API_키
```

### 2단계: 패키지 설치 및 봇 실행
```batch
# 배치 파일로 자동 실행 (권장)
run_discord_bot.bat
```

또는 수동 실행:
```bash
# 패키지 설치
pip install -r requirements_ultra_advanced.txt

# 봇 실행
python discord_bot.py
```

## ⚙️ 환경변수 설정 예시

`.env` 파일을 다음과 같이 작성:

```env
# Discord 봇 토큰
DISCORD_TOKEN=MTM3ODk5MzA4NjIzMzU2MzIwNg.GYpZ6y.example_token_here

# Google Gemini API 키  
GEMINI_API_KEY=AIzaSyA3A0-fCTcWbxkFRoT-example_api_key_here
```

## 🔒 보안 주의사항

### ⚠️ 절대 하지 말아야 할 것들:
- ❌ 토큰이나 API 키를 코드에 직접 입력
- ❌ `.env` 파일을 Git에 커밋  
- ❌ 토큰을 Discord나 공개 채널에 공유
- ❌ 스크린샷에 토큰이 포함되도록 촬영

### ✅ 해야 할 것들:
- ✅ `.env` 파일 사용으로 토큰 분리
- ✅ `.gitignore`에 `.env` 포함 (이미 설정됨)
- ✅ 토큰이 노출되면 즉시 재생성
- ✅ 정기적으로 API 키 갱신

## 🤖 봇 권한 설정

Discord 서버에 봇을 초대할 때 다음 권한들이 필요합니다:

### 필수 권한:
- `View Channels` - 채널 보기
- `Send Messages` - 메시지 전송  
- `Read Message History` - 메시지 기록 읽기
- `Add Reactions` - 리액션 추가
- `Use Slash Commands` - 슬래시 명령 사용

### 관리 권한 (고급 기능용):
- `Manage Messages` - 메시지 관리 (삭제)
- `Kick Members` - 멤버 추방
- `Ban Members` - 멤버 차단
- `Moderate Members` - 멤버 타임아웃
- `Manage Roles` - 역할 관리

## 📊 GUI 사용법

봇 실행 시 GUI 제어판이 함께 실행됩니다:

1. **🚀 봇 시작** - 봇 활성화
2. **⏹️ 봇 중지** - 봇 비활성화
3. **실시간 로그** - 봇 활동 모니터링
4. **사용자 관리** - 사용자 정보 및 통계
5. **AI 모니터링** - AI 판결 현황
6. **설정** - 봇 동작 설정

## 🗣️ 자연어 명령 예시

봇에게 다음과 같이 자연어로 말할 수 있습니다:

```
"위험한 사용자들 보여줘"
"홍길동 사용자 정보 알려줘"  
"서버 통계 분석해줘"
"경고 많은 사용자 찾아줘"
"보안 상태 확인해줘"
"AI 모델 재학습 시켜줄래?"
```

## ❗ 문제 해결

### 토큰 관련 오류
```
❌ DISCORD_TOKEN 환경변수가 설정되지 않았습니다!
```
**해결:** `.env` 파일에 `DISCORD_TOKEN=실제토큰` 추가

### API 키 관련 오류
```
❌ GEMINI_API_KEY 환경변수가 설정되지 않았습니다!
```
**해결:** `.env` 파일에 `GEMINI_API_KEY=실제키` 추가

### 권한 관련 오류
```
❌ discord.errors.Forbidden: 403 Forbidden
```
**해결:** 봇에게 필요한 권한을 Discord 서버에서 부여

### 패키지 설치 오류
```
❌ ModuleNotFoundError: No module named 'dotenv'
```
**해결:** `pip install python-dotenv` 실행

## 💡 추가 팁

1. **로그 확인**: `ultra_bot.log` 파일에서 상세 로그 확인
2. **데이터베이스**: SQLite 파일들은 자동 생성됨
3. **캐시 정리**: 가끔 봇을 재시작하여 메모리 최적화
4. **업데이트**: 정기적으로 패키지 업데이트 (`pip install --upgrade`)

## 📞 지원

문제가 있거나 질문이 있으면:
1. 로그 파일 확인
2. 환경변수 설정 재검토  
3. 봇 권한 확인
4. Discord 서버 상태 점검

**즐거운 서버 관리 되세요! 🎉**