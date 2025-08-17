#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discord 보안봇 설정 검증 도구
사용자가 봇을 실행하기 전에 필요한 모든 설정을 확인합니다.
"""

import os
import sys
import importlib
from pathlib import Path

def check_python_version():
    """Python 버전 확인"""
    print("🐍 Python 버전 확인 중...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 이상이 필요합니다!")
        print(f"   현재 버전: {version.major}.{version.minor}.{version.micro}")
        return False
    else:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (적합)")
        return True

def check_required_packages():
    """필수 패키지 확인"""
    print("\n📦 필수 패키지 확인 중...")
    
    required_packages = {
        'discord': 'discord.py',
        'google.generativeai': 'google-generativeai',
        'aiohttp': 'aiohttp',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'PIL': 'Pillow',
        'psutil': 'psutil',
        'requests': 'requests',
        'dotenv': 'python-dotenv'
    }
    
    missing_packages = []
    
    for module_name, package_name in required_packages.items():
        try:
            importlib.import_module(module_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} (누락)")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n⚠️ 누락된 패키지를 설치하세요:")
        print(f"pip install {' '.join(missing_packages)}")
        print("또는:")
        print("pip install -r requirements_ultra_advanced.txt")
        return False
    
    return True

def check_env_file():
    """환경변수 파일 확인"""
    print("\n🔐 환경설정 파일 확인 중...")
    
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env 파일이 없습니다!")
        print("   .env.example을 복사해서 .env 파일을 만드세요:")
        print("   copy .env.example .env")
        return False
    
    print("✅ .env 파일 존재")
    
    # .env 파일 내용 확인
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        discord_token = os.getenv('DISCORD_TOKEN')
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        if not discord_token or discord_token == 'your_discord_bot_token_here':
            print("❌ DISCORD_TOKEN이 설정되지 않았습니다!")
            return False
        print("✅ Discord 토큰 설정됨")
        
        if not gemini_key or gemini_key == 'your_gemini_api_key_here':
            print("❌ GEMINI_API_KEY가 설정되지 않았습니다!")
            return False
        print("✅ Gemini API 키 설정됨")
        
        return True
        
    except Exception as e:
        print(f"❌ .env 파일 읽기 오류: {e}")
        return False

def check_required_files():
    """필수 파일 확인"""
    print("\n📁 필수 파일 확인 중...")
    
    required_files = [
        'discord_bot.py',
        'core_ai_system.py', 
        'advanced_user_system.py',
        'natural_language_command_system.py'
    ]
    
    all_files_exist = True
    
    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} (누락)")
            all_files_exist = False
    
    return all_files_exist

def test_database():
    """데이터베이스 연결 테스트"""
    print("\n🗄️ 데이터베이스 연결 테스트 중...")
    
    try:
        import sqlite3
        conn = sqlite3.connect('security_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        print("✅ 데이터베이스 연결 성공")
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 오류: {e}")
        return False

def main():
    """메인 검증 함수"""
    print("=" * 50)
    print("🛡️ Discord 보안봇 설정 검증 도구")
    print("=" * 50)
    
    checks = [
        ("Python 버전", check_python_version),
        ("필수 패키지", check_required_packages), 
        ("환경설정", check_env_file),
        ("필수 파일", check_required_files),
        ("데이터베이스", test_database)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} 검사 중 오류: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 모든 검증 통과! 봇을 실행할 수 있습니다.")
        print("\n실행 방법:")
        print("  run_discord_bot.bat")
        print("또는:")
        print("  python discord_bot.py")
    else:
        print("⚠️ 일부 검증 실패. 위의 문제들을 해결하세요.")
        print("\n도움이 필요하면 SETUP_GUIDE.md를 확인하세요.")
    
    print("=" * 50)
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()