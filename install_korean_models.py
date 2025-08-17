#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini 기반 보안봇 - 추가 설정 스크립트
"""

def check_gemini_setup():
    """Gemini API 설정 확인"""
    
    print("🤖 Gemini 기반 보안봇 설정 확인...")
    print()
    print("ℹ️  이 봇은 Google Gemini API를 사용합니다.")
    print("   별도의 AI 모델 설치가 필요하지 않습니다!")
    print()
    print("📋 필요한 것:")
    print("   1. Google Gemini API 키")
    print("   2. Discord 봇 토큰") 
    print("   3. requirements_ultra_advanced.txt의 패키지들")
    print()
    print("🚀 모든 AI 처리는 Gemini가 담당합니다:")
    print("   • 자연어 명령 이해")
    print("   • 메시지 분석 및 판정")
    print("   • 감정 분석")
    print("   • 한국어/영어 처리")
    print()
    
    try:
        import google.generativeai as genai
        print("✅ Gemini 라이브러리 설치됨")
        
        # API 키 확인 (환경변수에서 직접)
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if api_key and len(api_key) > 10:
            print("✅ Gemini API 키 설정됨")
        else:
            print("⚠️  Gemini API 키를 확인하세요")
            print("   .env 파일에 GEMINI_API_KEY=your_key_here 를 추가하세요")
            
    except ImportError:
        print("❌ Gemini 라이브러리가 설치되지 않았습니다")
        print("   pip install google-generativeai 실행하세요")
    except Exception as e:
        print(f"⚠️  설정 확인 중 오류: {e}")
    
    print()
    print("🎉 Gemini 기반 AI는 별도 모델 다운로드 없이 바로 작동합니다!")

if __name__ == "__main__":
    check_gemini_setup()
    input("\n아무 키나 누르세요...")