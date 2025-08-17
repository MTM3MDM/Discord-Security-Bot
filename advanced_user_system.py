import sqlite3
import json
import time
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import hashlib
import numpy as np
from dataclasses import dataclass, asdict
import threading
from enum import Enum

logger = logging.getLogger(__name__)

class UserTier(Enum):
    """사용자 등급"""
    NEWCOMER = "신규"      # 0-30일
    MEMBER = "일반"        # 31-90일
    REGULAR = "정회원"     # 91-365일
    VETERAN = "베테랑"     # 365일+
    TRUSTED = "신뢰멤버"   # 고신뢰도
    MODERATOR = "준관리자" # 특별권한
    VIP = "VIP"           # 특별회원

class RiskLevel(Enum):
    """위험도 등급"""
    VERY_LOW = "매우낮음"
    LOW = "낮음"
    MEDIUM = "보통"
    HIGH = "높음"
    VERY_HIGH = "매우높음"
    CRITICAL = "치명적"

@dataclass
class UserBehaviorPattern:
    """사용자 행동 패턴"""
    hourly_activity: List[int]      # 24시간 활동 패턴
    daily_activity: List[int]       # 7일 활동 패턴
    channel_preferences: Dict[str, int]  # 채널별 활동
    message_length_dist: List[int]  # 메시지 길이 분포
    emoji_usage: Dict[str, int]     # 이모지 사용 패턴
    reaction_patterns: Dict[str, int]  # 반응 패턴
    mention_patterns: Dict[str, int]   # 멘션 패턴
    link_sharing: Dict[str, int]    # 링크 공유 패턴
    voice_activity: List[int]       # 음성 채널 활동
    game_activity: Dict[str, int]   # 게임 활동
    
    def __post_init__(self):
        # 기본값 초기화
        if not self.hourly_activity:
            self.hourly_activity = [0] * 24
        if not self.daily_activity:
            self.daily_activity = [0] * 7
        if not self.channel_preferences:
            self.channel_preferences = {}
        if not self.message_length_dist:
            self.message_length_dist = [0] * 10  # 0-9: 각 길이 범위
        if not self.emoji_usage:
            self.emoji_usage = {}
        if not self.reaction_patterns:
            self.reaction_patterns = {}
        if not self.mention_patterns:
            self.mention_patterns = {}
        if not self.link_sharing:
            self.link_sharing = {}
        if not self.voice_activity:
            self.voice_activity = [0] * 24
        if not self.game_activity:
            self.game_activity = {}

@dataclass
class UserProfile:
    """고급 사용자 프로필"""
    user_id: int
    username: str
    guild_id: int
    
    # 기본 정보
    join_date: datetime
    first_seen: datetime
    last_activity: datetime
    
    # 신뢰도 시스템
    trust_score: float = 50.0
    reputation_score: float = 50.0
    reliability_score: float = 50.0
    
    # 활동 통계
    total_messages: int = 0
    total_reactions: int = 0
    total_voice_time: int = 0  # 분
    total_warnings: int = 0
    total_violations: int = 0
    
    # 등급 및 상태
    user_tier: UserTier = UserTier.NEWCOMER
    risk_level: RiskLevel = RiskLevel.MEDIUM
    
    # 행동 패턴
    behavior_pattern: UserBehaviorPattern = None
    
    # 특별 플래그
    is_verified: bool = False
    is_premium: bool = False
    is_bot: bool = False
    special_permissions: List[str] = None
    
    # 제재 이력
    mute_count: int = 0
    kick_count: int = 0
    ban_count: int = 0
    timeout_count: int = 0
    
    # AI 분석 결과
    personality_analysis: Dict[str, float] = None
    communication_style: Dict[str, float] = None
    interests: Dict[str, float] = None
    
    def __post_init__(self):
        if self.behavior_pattern is None:
            self.behavior_pattern = UserBehaviorPattern([], [], {}, [], {}, {}, {}, {}, [], {})
        if self.special_permissions is None:
            self.special_permissions = []
        if self.personality_analysis is None:
            self.personality_analysis = {}
        if self.communication_style is None:
            self.communication_style = {}
        if self.interests is None:
            self.interests = {}

class AdvancedUserManager:
    """고급 사용자 관리 시스템"""
    
    def __init__(self):
        self.user_profiles: Dict[int, UserProfile] = {}
        self.user_sessions: Dict[int, Dict] = defaultdict(dict)
        self.reputation_system = ReputationSystem()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.trust_calculator = TrustCalculator()
        
        # 실시간 추적
        self.active_users: Dict[int, datetime] = {}
        self.message_buffers: Dict[int, deque] = defaultdict(lambda: deque(maxlen=50))
        
        # 통계
        self.daily_stats = defaultdict(lambda: defaultdict(int))
        
        self.init_database()
        self.load_user_profiles()
    
    def init_database(self):
        """데이터베이스 초기화 (에러 처리 강화)"""
        try:
            conn = sqlite3.connect('security_bot.db')
            cursor = conn.cursor()
            
            # 고급 사용자 프로필 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS advanced_users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                guild_id INTEGER,
                join_date TIMESTAMP,
                first_seen TIMESTAMP,
                last_activity TIMESTAMP,
                trust_score REAL DEFAULT 50.0,
                reputation_score REAL DEFAULT 50.0,
                reliability_score REAL DEFAULT 50.0,
                total_messages INTEGER DEFAULT 0,
                total_reactions INTEGER DEFAULT 0,
                total_voice_time INTEGER DEFAULT 0,
                total_warnings INTEGER DEFAULT 0,
                total_violations INTEGER DEFAULT 0,
                user_tier TEXT DEFAULT 'NEWCOMER',
                risk_level TEXT DEFAULT 'MEDIUM',
                is_verified BOOLEAN DEFAULT FALSE,
                is_premium BOOLEAN DEFAULT FALSE,
                is_bot BOOLEAN DEFAULT FALSE,
                mute_count INTEGER DEFAULT 0,
                kick_count INTEGER DEFAULT 0,
                ban_count INTEGER DEFAULT 0,
                timeout_count INTEGER DEFAULT 0,
                behavior_pattern TEXT,
                personality_analysis TEXT,
                communication_style TEXT,
                interests TEXT,
                special_permissions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 사용자 활동 로그 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guild_id INTEGER,
                activity_type TEXT,
                activity_data TEXT,
                channel_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES advanced_users (user_id)
            )
            ''')
            
            # 신뢰도 변화 이력 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS trust_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                old_score REAL,
                new_score REAL,
                change_reason TEXT,
                change_amount REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES advanced_users (user_id)
            )
            ''')
            
            # 사용자 관계 테이블 (친구, 적대 관계)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                relationship_type TEXT,
                strength REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ 사용자 데이터베이스 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
            # 백업 데이터베이스 생성 시도
            try:
                conn = sqlite3.connect(':memory:')
                logger.info("메모리 데이터베이스로 폴백")
            except:
                logger.critical("데이터베이스 초기화 완전 실패")
    
    def load_user_profiles(self):
        """사용자 프로필 로드"""
        try:
            conn = sqlite3.connect('security_bot.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM advanced_users')
            users = cursor.fetchall()
            
            for user_data in users:
                user_profile = self._create_user_profile_from_db(user_data)
                self.user_profiles[user_profile.user_id] = user_profile
            
            conn.close()
            logger.info(f"{len(self.user_profiles)}개의 사용자 프로필을 로드했습니다")
            
        except Exception as e:
            logger.error(f"사용자 프로필 로드 오류: {e}")
    
    def _create_user_profile_from_db(self, user_data) -> UserProfile:
        """DB 데이터로부터 사용자 프로필 생성"""
        try:
            # 기본 정보 추출 (개선된 JSON 파싱)
            def safe_json_loads(data, default):
                try:
                    if not data or data.strip() == '':
                        return default
                    # 문자열이 날짜 형식인지 확인
                    if isinstance(data, str) and (
                        data.count('-') >= 2 or 
                        data.count('T') == 1 or 
                        data.count(':') >= 2
                    ):
                        # 날짜 문자열은 그대로 반환하거나 기본값 사용
                        return default
                    return json.loads(data)
                except (json.JSONDecodeError, TypeError, ValueError):
                    # 조용히 기본값 반환 (로그 스팸 방지)
                    return default
            
            behavior_pattern = safe_json_loads(user_data[25] if len(user_data) > 25 else None, {})
            personality = safe_json_loads(user_data[26] if len(user_data) > 26 else None, {})
            communication = safe_json_loads(user_data[27] if len(user_data) > 27 else None, {})
            interests = safe_json_loads(user_data[28] if len(user_data) > 28 else None, {})
            permissions = safe_json_loads(user_data[29] if len(user_data) > 29 else None, [])
            
            # UserBehaviorPattern 객체 생성 (안전한 처리)
            if not isinstance(behavior_pattern, dict):
                behavior_pattern = {}
            if not isinstance(personality, dict):
                personality = {}
            if not isinstance(communication, dict):
                communication = {}
            if not isinstance(interests, dict):
                interests = {}
            if not isinstance(permissions, list):
                permissions = []
                
            behavior_obj = UserBehaviorPattern(
                hourly_activity=behavior_pattern.get('hourly_activity', [0]*24),
                daily_activity=behavior_pattern.get('daily_activity', [0]*7),
                channel_preferences=behavior_pattern.get('channel_preferences', {}),
                message_length_dist=behavior_pattern.get('message_length_dist', [0]*10),
                emoji_usage=behavior_pattern.get('emoji_usage', {}),
                reaction_patterns=behavior_pattern.get('reaction_patterns', {}),
                mention_patterns=behavior_pattern.get('mention_patterns', {}),
                link_sharing=behavior_pattern.get('link_sharing', {}),
                voice_activity=behavior_pattern.get('voice_activity', [0]*24),
                game_activity=behavior_pattern.get('game_activity', {})
            )
            
            return UserProfile(
                user_id=user_data[0],
                username=user_data[1],
                guild_id=user_data[2],
                join_date=datetime.fromisoformat(user_data[3]) if user_data[3] else datetime.now(),
                first_seen=datetime.fromisoformat(user_data[4]) if user_data[4] else datetime.now(),
                last_activity=datetime.fromisoformat(user_data[5]) if user_data[5] else datetime.now(),
                trust_score=user_data[6],
                reputation_score=user_data[7],
                reliability_score=user_data[8],
                total_messages=user_data[9],
                total_reactions=user_data[10],
                total_voice_time=user_data[11],
                total_warnings=user_data[12],
                total_violations=user_data[13],
                user_tier=UserTier(user_data[14]) if user_data[14] else UserTier.NEWCOMER,
                risk_level=RiskLevel(user_data[15]) if user_data[15] else RiskLevel.MEDIUM,
                is_verified=bool(user_data[16]),
                is_premium=bool(user_data[17]),
                is_bot=bool(user_data[18]),
                mute_count=user_data[19],
                kick_count=user_data[20],
                ban_count=user_data[21],
                timeout_count=user_data[22],
                behavior_pattern=behavior_obj,
                personality_analysis=personality,
                communication_style=communication,
                interests=interests,
                special_permissions=permissions
            )
            
        except Exception as e:
            logger.error(f"사용자 프로필 생성 오류: {e}")
            # 기본 프로필 반환
            return UserProfile(
                user_id=user_data[0],
                username=user_data[1] or "Unknown",
                guild_id=user_data[2] or 0,
                join_date=datetime.now(),
                first_seen=datetime.now(),
                last_activity=datetime.now()
            )
    
    async def get_or_create_user_profile(self, user_id: int, username: str = None, 
                                       guild_id: int = None) -> UserProfile:
        """사용자 프로필 가져오기 또는 생성"""
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            # 기본 정보 업데이트
            if username and profile.username != username:
                profile.username = username
            profile.last_activity = datetime.now()
            return profile
        
        # 새 프로필 생성
        profile = UserProfile(
            user_id=user_id,
            username=username or f"User{user_id}",
            guild_id=guild_id or 0,
            join_date=datetime.now(),
            first_seen=datetime.now(),
            last_activity=datetime.now(),
            behavior_pattern=UserBehaviorPattern([], [], {}, [], {}, {}, {}, {}, [], {})
        )
        
        self.user_profiles[user_id] = profile
        await self.save_user_profile(profile)
        
        logger.info(f"새 사용자 프로필 생성: {username} ({user_id})")
        return profile
    
    async def save_user_profile(self, profile: UserProfile):
        """사용자 프로필 저장"""
        try:
            conn = sqlite3.connect('security_bot.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO advanced_users (
                    user_id, username, guild_id, join_date, first_seen, last_activity,
                    trust_score, reputation_score, reliability_score,
                    total_messages, total_reactions, total_voice_time,
                    total_warnings, total_violations,
                    user_tier, risk_level, is_verified, is_premium, is_bot,
                    mute_count, kick_count, ban_count, timeout_count,
                    behavior_pattern, personality_analysis, communication_style,
                    interests, special_permissions, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile.user_id, profile.username, profile.guild_id,
                profile.join_date.isoformat(), profile.first_seen.isoformat(),
                profile.last_activity.isoformat(),
                profile.trust_score, profile.reputation_score, profile.reliability_score,
                profile.total_messages, profile.total_reactions, profile.total_voice_time,
                profile.total_warnings, profile.total_violations,
                profile.user_tier.value, profile.risk_level.value,
                profile.is_verified, profile.is_premium, profile.is_bot,
                profile.mute_count, profile.kick_count, profile.ban_count, profile.timeout_count,
                json.dumps(asdict(profile.behavior_pattern), ensure_ascii=False),
                json.dumps(profile.personality_analysis, ensure_ascii=False),
                json.dumps(profile.communication_style, ensure_ascii=False),
                json.dumps(profile.interests, ensure_ascii=False),
                json.dumps(profile.special_permissions, ensure_ascii=False),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"사용자 프로필 저장 오류: {e}")
    
    async def update_user_activity(self, user_id: int, activity_type: str, 
                                 activity_data: Dict, channel_id: int = None):
        """사용자 활동 업데이트"""
        profile = await self.get_or_create_user_profile(user_id)
        
        # 활동 통계 업데이트
        if activity_type == "message":
            profile.total_messages += 1
            await self._update_message_patterns(profile, activity_data, channel_id)
        elif activity_type == "reaction":
            profile.total_reactions += 1
            await self._update_reaction_patterns(profile, activity_data)
        elif activity_type == "voice":
            voice_time = activity_data.get('duration', 0)
            profile.total_voice_time += voice_time
            await self._update_voice_patterns(profile, activity_data)
        elif activity_type == "game":
            await self._update_game_patterns(profile, activity_data)
        
        # 활동 시간 패턴 업데이트
        current_hour = datetime.now().hour
        current_day = datetime.now().weekday()
        
        profile.behavior_pattern.hourly_activity[current_hour] += 1
        profile.behavior_pattern.daily_activity[current_day] += 1
        
        # 마지막 활동 시간 업데이트
        profile.last_activity = datetime.now()
        self.active_users[user_id] = datetime.now()
        
        # 등급 업데이트
        await self._update_user_tier(profile)
        
        # DB에 활동 로그 저장
        await self._log_user_activity(user_id, profile.guild_id, activity_type, activity_data, channel_id)
        
        # 프로필 저장
        await self.save_user_profile(profile)
    
    async def _update_message_patterns(self, profile: UserProfile, message_data: Dict, channel_id: int):
        """메시지 패턴 분석 및 업데이트"""
        content = message_data.get('content', '')
        
        # 채널 선호도 업데이트
        if channel_id:
            channel_key = str(channel_id)
            profile.behavior_pattern.channel_preferences[channel_key] = \
                profile.behavior_pattern.channel_preferences.get(channel_key, 0) + 1
        
        # 메시지 길이 분포 업데이트
        length = len(content)
        length_category = min(9, length // 10)  # 0-9 카테고리
        profile.behavior_pattern.message_length_dist[length_category] += 1
        
        # 이모지 사용 패턴 분석
        import re
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+",
            flags=re.UNICODE
        )
        emojis = emoji_pattern.findall(content)
        for emoji in emojis:
            profile.behavior_pattern.emoji_usage[emoji] = \
                profile.behavior_pattern.emoji_usage.get(emoji, 0) + 1
        
        # 멘션 패턴 분석
        mentions = message_data.get('mentions', [])
        if mentions:
            mention_count = len(mentions)
            mention_key = f"mentions_{min(10, mention_count)}"
            profile.behavior_pattern.mention_patterns[mention_key] = \
                profile.behavior_pattern.mention_patterns.get(mention_key, 0) + 1
        
        # 링크 공유 패턴 분석
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        for url in urls:
            domain = url.split('/')[2] if '://' in url else 'unknown'
            profile.behavior_pattern.link_sharing[domain] = \
                profile.behavior_pattern.link_sharing.get(domain, 0) + 1
        
        # 메시지 버퍼에 추가 (최근 메시지 분석용)
        self.message_buffers[profile.user_id].append({
            'content': content,
            'timestamp': datetime.now(),
            'channel_id': channel_id,
            'length': length
        })
    
    async def _update_reaction_patterns(self, profile: UserProfile, reaction_data: Dict):
        """반응 패턴 업데이트"""
        emoji = reaction_data.get('emoji', '')
        reaction_type = reaction_data.get('type', 'add')  # add, remove
        
        key = f"{emoji}_{reaction_type}"
        profile.behavior_pattern.reaction_patterns[key] = \
            profile.behavior_pattern.reaction_patterns.get(key, 0) + 1
    
    async def _update_voice_patterns(self, profile: UserProfile, voice_data: Dict):
        """음성 활동 패턴 업데이트"""
        current_hour = datetime.now().hour
        duration = voice_data.get('duration', 1)  # 분 단위
        
        profile.behavior_pattern.voice_activity[current_hour] += duration
    
    async def _update_game_patterns(self, profile: UserProfile, game_data: Dict):
        """게임 활동 패턴 업데이트"""
        game_name = game_data.get('name', 'Unknown')
        duration = game_data.get('duration', 1)  # 분 단위
        
        profile.behavior_pattern.game_activity[game_name] = \
            profile.behavior_pattern.game_activity.get(game_name, 0) + duration
    
    async def _update_user_tier(self, profile: UserProfile):
        """사용자 등급 업데이트"""
        account_age = (datetime.now() - profile.first_seen).days
        
        # 기본 등급 결정
        if account_age < 30:
            base_tier = UserTier.NEWCOMER
        elif account_age < 90:
            base_tier = UserTier.MEMBER
        elif account_age < 365:
            base_tier = UserTier.REGULAR
        else:
            base_tier = UserTier.VETERAN
        
        # 신뢰도 기반 추가 등급
        if profile.trust_score >= 85 and profile.total_messages >= 100:
            profile.user_tier = UserTier.TRUSTED
        elif profile.is_verified and profile.trust_score >= 70:
            profile.user_tier = UserTier.VIP
        elif 'moderator' in profile.special_permissions:
            profile.user_tier = UserTier.MODERATOR
        else:
            profile.user_tier = base_tier
        
        # 위험도 레벨 업데이트
        await self._update_risk_level(profile)
    
    async def _update_risk_level(self, profile: UserProfile):
        """위험도 레벨 업데이트"""
        risk_score = 0.0
        
        # 신뢰도 기반 위험도
        trust_risk = (100 - profile.trust_score) / 100.0
        risk_score += trust_risk * 0.4
        
        # 제재 이력 기반 위험도
        total_sanctions = profile.total_warnings + profile.mute_count + profile.kick_count + profile.ban_count
        if total_sanctions > 0:
            risk_score += min(0.5, total_sanctions * 0.1)
        
        # 활동 패턴 기반 위험도
        behavior_risk = await self._calculate_behavior_risk(profile)
        risk_score += behavior_risk * 0.3
        
        # 최근 활동 기반 위험도
        if profile.last_activity:
            days_inactive = (datetime.now() - profile.last_activity).days
            if days_inactive > 30:
                risk_score += 0.1
        
        # 위험도 레벨 결정
        if risk_score < 0.2:
            profile.risk_level = RiskLevel.VERY_LOW
        elif risk_score < 0.4:
            profile.risk_level = RiskLevel.LOW
        elif risk_score < 0.6:
            profile.risk_level = RiskLevel.MEDIUM
        elif risk_score < 0.8:
            profile.risk_level = RiskLevel.HIGH
        elif risk_score < 0.95:
            profile.risk_level = RiskLevel.VERY_HIGH
        else:
            profile.risk_level = RiskLevel.CRITICAL
    
    async def _calculate_behavior_risk(self, profile: UserProfile) -> float:
        """행동 패턴 기반 위험도 계산"""
        risk = 0.0
        
        # 활동 시간 분석 (새벽 시간대 활동이 많으면 위험도 증가)
        if profile.behavior_pattern.hourly_activity:
            night_hours = sum(profile.behavior_pattern.hourly_activity[0:6])
            total_activity = sum(profile.behavior_pattern.hourly_activity)
            if total_activity > 0:
                night_ratio = night_hours / total_activity
                if night_ratio > 0.3:  # 30% 이상 새벽 활동
                    risk += 0.1
        
        # 메시지 길이 패턴 분석
        if profile.behavior_pattern.message_length_dist:
            # 너무 짧거나 너무 긴 메시지만 보내는 경우
            very_short = profile.behavior_pattern.message_length_dist[0]  # 0-9자
            very_long = sum(profile.behavior_pattern.message_length_dist[7:])  # 70자 이상
            total_messages = sum(profile.behavior_pattern.message_length_dist)
            
            if total_messages > 0:
                short_ratio = very_short / total_messages
                long_ratio = very_long / total_messages
                
                if short_ratio > 0.8 or long_ratio > 0.5:
                    risk += 0.1
        
        # 링크 공유 패턴 분석
        if profile.behavior_pattern.link_sharing:
            suspicious_domains = ['bit.ly', 'tinyurl.com', 'discord-nitro', 'free-nitro']
            suspicious_count = sum(
                count for domain, count in profile.behavior_pattern.link_sharing.items()
                if any(sus in domain.lower() for sus in suspicious_domains)
            )
            if suspicious_count > 0:
                risk += min(0.3, suspicious_count * 0.1)
        
        return min(1.0, risk)
    
    async def update_user_risk_level(self, user_id: int, risk_level: RiskLevel, reason: str = ""):
        """사용자 위험도 레벨 업데이트"""
        try:
            profile = await self.get_or_create_user_profile(user_id, "Unknown", 0)
            
            old_risk = profile.risk_level
            profile.risk_level = risk_level
            
            # 위험도 변경 로그 기록
            if old_risk != risk_level:
                conn = sqlite3.connect('security_bot.db')
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO trust_history (user_id, old_score, new_score, change_reason, change_amount)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    float(old_risk.value if hasattr(old_risk, 'value') else 0),
                    float(risk_level.value if hasattr(risk_level, 'value') else 0),
                    f"위험도 변경: {reason}",
                    1.0
                ))
                
                conn.commit()
                conn.close()
                
                logger.info(f"사용자 {user_id}의 위험도가 {old_risk.value} → {risk_level.value}로 변경됨: {reason}")
            
            # 데이터베이스 업데이트
            await self.save_user_profile(profile)
            
        except Exception as e:
            logger.error(f"위험도 레벨 업데이트 실패: {e}")
    
    async def _log_user_activity(self, user_id: int, guild_id: int, activity_type: str, 
                               activity_data: Dict, channel_id: int):
        """사용자 활동 로그 저장"""
        try:
            conn = sqlite3.connect('security_bot.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_activity_logs (
                    user_id, guild_id, activity_type, activity_data, channel_id
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id, guild_id, activity_type,
                json.dumps(activity_data, ensure_ascii=False),
                channel_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"활동 로그 저장 오류: {e}")
    
    async def get_user_context(self, user_id: int) -> Dict[str, Any]:
        """사용자 컨텍스트 정보 반환"""
        profile = self.user_profiles.get(user_id)
        if not profile:
            return {
                'user_id': user_id,
                'trust_score': 50.0,
                'warnings': 0,
                'account_age': 0,
                'join_days': 0,
                'activity_pattern': '신규사용자'
            }
        
        account_age = (datetime.now() - profile.first_seen).days
        join_days = (datetime.now() - profile.join_date).days if profile.join_date else 0
        
        # 최근 메시지 분석
        recent_messages = list(self.message_buffers[user_id])
        avg_length = sum(msg['length'] for msg in recent_messages) / len(recent_messages) if recent_messages else 0
        
        return {
            'user_id': user_id,
            'trust_score': profile.trust_score,
            'reputation_score': profile.reputation_score,
            'reliability_score': profile.reliability_score,
            'warnings': profile.total_warnings,
            'violations': profile.total_violations,
            'account_age': account_age,
            'join_days': join_days,
            'user_tier': profile.user_tier.value,
            'risk_level': profile.risk_level.value,
            'total_messages': profile.total_messages,
            'avg_message_length': avg_length,
            'activity_pattern': self._get_activity_pattern_description(profile),
            'last_activity': profile.last_activity.isoformat() if profile.last_activity else None,
            'is_verified': profile.is_verified,
            'is_premium': profile.is_premium,
            'special_permissions': profile.special_permissions
        }
    
    def _get_activity_pattern_description(self, profile: UserProfile) -> str:
        """활동 패턴 설명"""
        if not profile.behavior_pattern.hourly_activity:
            return "활동 데이터 부족"
        
        total_activity = sum(profile.behavior_pattern.hourly_activity)
        if total_activity == 0:
            return "활동 없음"
        
        # 가장 활발한 시간대 찾기
        peak_hour = profile.behavior_pattern.hourly_activity.index(max(profile.behavior_pattern.hourly_activity))
        
        if 6 <= peak_hour <= 11:
            time_desc = "아침형"
        elif 12 <= peak_hour <= 17:
            time_desc = "오후형"
        elif 18 <= peak_hour <= 23:
            time_desc = "저녁형"
        else:
            time_desc = "야행성"
        
        # 활동 빈도
        avg_daily_messages = profile.total_messages / max(1, (datetime.now() - profile.first_seen).days)
        if avg_daily_messages > 50:
            freq_desc = "매우활발"
        elif avg_daily_messages > 20:
            freq_desc = "활발"
        elif avg_daily_messages > 5:
            freq_desc = "보통"
        else:
            freq_desc = "조용함"
        
        return f"{time_desc}_{freq_desc}"
    
    async def update_trust_score(self, user_id: int, change_amount: float, reason: str):
        """신뢰도 점수 업데이트"""
        profile = await self.get_or_create_user_profile(user_id)
        old_score = profile.trust_score
        
        # 신뢰도 업데이트 (0-100 범위)
        profile.trust_score = max(0.0, min(100.0, profile.trust_score + change_amount))
        
        # 변화 기록
        await self._log_trust_change(user_id, old_score, profile.trust_score, reason, change_amount)
        
        # 등급 재계산
        await self._update_user_tier(profile)
        
        # 프로필 저장
        await self.save_user_profile(profile)
        
        logger.info(f"신뢰도 업데이트: {user_id} ({old_score:.1f} -> {profile.trust_score:.1f}) - {reason}")
    
    async def _log_trust_change(self, user_id: int, old_score: float, new_score: float, 
                              reason: str, change_amount: float):
        """신뢰도 변화 기록"""
        try:
            conn = sqlite3.connect('security_bot.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trust_history (
                    user_id, old_score, new_score, change_reason, change_amount
                ) VALUES (?, ?, ?, ?, ?)
            ''', (user_id, old_score, new_score, reason, change_amount))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"신뢰도 변화 기록 오류: {e}")
    
    async def apply_violation(self, user_id: int, violation_type: str, severity: int):
        """위반 사항 적용"""
        profile = await self.get_or_create_user_profile(user_id)
        
        # 위반 카운트 증가
        profile.total_violations += 1
        
        if violation_type == "warning":
            profile.total_warnings += 1
        elif violation_type == "mute":
            profile.mute_count += 1
        elif violation_type == "kick":
            profile.kick_count += 1
        elif violation_type == "ban":
            profile.ban_count += 1
        elif violation_type == "timeout":
            profile.timeout_count += 1
        
        # 심각도에 따른 신뢰도 감소
        trust_penalty = severity * 5.0  # 심각도 1당 5점 감소
        await self.update_trust_score(user_id, -trust_penalty, f"{violation_type} 위반 (심각도: {severity})")
        
        # 프로필 저장
        await self.save_user_profile(profile)
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """사용자 통계 반환"""
        if not self.user_profiles:
            return {"총사용자수": 0}
        
        total_users = len(self.user_profiles)
        active_users = len([p for p in self.user_profiles.values() 
                          if p.last_activity and (datetime.now() - p.last_activity).days < 7])
        
        # 등급별 분포
        tier_counts = defaultdict(int)
        risk_counts = defaultdict(int)
        
        avg_trust = 0
        avg_messages = 0
        
        for profile in self.user_profiles.values():
            tier_counts[profile.user_tier.value] += 1
            risk_counts[profile.risk_level.value] += 1
            avg_trust += profile.trust_score
            avg_messages += profile.total_messages
        
        avg_trust /= total_users
        avg_messages /= total_users
        
        return {
            "총사용자수": total_users,
            "활성사용자수": active_users,
            "평균신뢰도": round(avg_trust, 1),
            "평균메시지수": round(avg_messages, 1),
            "등급별분포": dict(tier_counts),
            "위험도별분포": dict(risk_counts),
            "현재온라인": len(self.active_users)
        }
    
    async def get_risk_users(self, risk_level: RiskLevel = None) -> List[UserProfile]:
        """위험 사용자 목록 반환"""
        risk_users = []
        
        for profile in self.user_profiles.values():
            if risk_level is None:
                if profile.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]:
                    risk_users.append(profile)
            elif profile.risk_level == risk_level:
                risk_users.append(profile)
        
        # 위험도 순으로 정렬
        risk_order = {
            RiskLevel.CRITICAL: 6,
            RiskLevel.VERY_HIGH: 5,
            RiskLevel.HIGH: 4,
            RiskLevel.MEDIUM: 3,
            RiskLevel.LOW: 2,
            RiskLevel.VERY_LOW: 1
        }
        
        risk_users.sort(key=lambda p: risk_order.get(p.risk_level, 0), reverse=True)
        return risk_users
    
    async def analyze_user_relationships(self, user_id: int) -> Dict[str, Any]:
        """사용자 관계 분석"""
        # 간단한 관계 분석 (실제로는 더 복잡한 분석 필요)
        profile = self.user_profiles.get(user_id)
        if not profile:
            return {"관계분석": "사용자 없음"}
        
        relationships = {
            "친밀한사용자": [],
            "충돌사용자": [],
            "멘션빈도높은사용자": [],
            "반응많이주는사용자": []
        }
        
        # 멘션 패턴에서 관계 추출
        mention_patterns = profile.behavior_pattern.mention_patterns
        if mention_patterns:
            # 멘션이 많은 사용자들을 친밀한 사용자로 분류 (예시)
            for pattern, count in mention_patterns.items():
                if count > 10:  # 10번 이상 멘션
                    relationships["멘션빈도높은사용자"].append(f"패턴: {pattern} ({count}회)")
        
        return relationships


class ReputationSystem:
    """평판 시스템"""
    
    def __init__(self):
        self.reputation_factors = {
            'message_quality': 0.3,
            'helpful_reactions': 0.2,
            'positive_feedback': 0.2,
            'consistency': 0.15,
            'community_contribution': 0.15
        }
    
    def calculate_reputation(self, user_profile: UserProfile) -> float:
        """평판 점수 계산"""
        reputation = 50.0  # 기본 점수
        
        # 메시지 품질 (길이, 이모지 사용 등)
        if user_profile.total_messages > 0:
            avg_length = sum(user_profile.behavior_pattern.message_length_dist) / len(user_profile.behavior_pattern.message_length_dist)
            if 20 <= avg_length <= 200:  # 적절한 길이
                reputation += 5.0
        
        # 리액션 비율
        if user_profile.total_messages > 0:
            reaction_ratio = user_profile.total_reactions / user_profile.total_messages
            reputation += min(10.0, reaction_ratio * 20)
        
        # 위반 기록에 따른 감점
        violation_penalty = user_profile.total_violations * 3
        reputation -= violation_penalty
        
        return max(0.0, min(100.0, reputation))


class BehaviorAnalyzer:
    """행동 분석 시스템"""
    
    def analyze_communication_style(self, user_profile: UserProfile) -> Dict[str, float]:
        """의사소통 스타일 분석"""
        style = {
            'formal': 0.5,      # 공식적
            'casual': 0.5,      # 캐주얼
            'emoji_heavy': 0.5, # 이모지 많이 사용
            'concise': 0.5,     # 간결함
            'verbose': 0.5      # 장황함
        }
        
        # 이모지 사용 분석
        total_emojis = sum(user_profile.behavior_pattern.emoji_usage.values())
        if user_profile.total_messages > 0:
            emoji_ratio = total_emojis / user_profile.total_messages
            if emoji_ratio > 0.5:
                style['emoji_heavy'] = 0.8
                style['casual'] = 0.7
            elif emoji_ratio < 0.1:
                style['formal'] = 0.7
        
        # 메시지 길이 분석
        if user_profile.behavior_pattern.message_length_dist:
            short_messages = sum(user_profile.behavior_pattern.message_length_dist[:3])  # 0-29자
            long_messages = sum(user_profile.behavior_pattern.message_length_dist[7:])   # 70자+
            total = sum(user_profile.behavior_pattern.message_length_dist)
            
            if total > 0:
                short_ratio = short_messages / total
                long_ratio = long_messages / total
                
                if short_ratio > 0.7:
                    style['concise'] = 0.8
                elif long_ratio > 0.3:
                    style['verbose'] = 0.8
        
        return style
    
    def analyze_personality_traits(self, user_profile: UserProfile) -> Dict[str, float]:
        """성격 특성 분석"""
        traits = {
            'extroversion': 0.5,     # 외향성
            'agreeableness': 0.5,    # 호감성
            'conscientiousness': 0.5, # 성실성
            'neuroticism': 0.5,      # 신경증
            'openness': 0.5          # 개방성
        }
        
        # 활동량 기반 외향성 분석
        if user_profile.total_messages > 100:
            traits['extroversion'] = min(1.0, user_profile.total_messages / 1000)
        
        # 제재 이력 기반 호감성 분석
        if user_profile.total_violations == 0:
            traits['agreeableness'] = 0.8
        else:
            traits['agreeableness'] = max(0.2, 0.8 - user_profile.total_violations * 0.1)
        
        # 일정한 활동 패턴 기반 성실성 분석
        if user_profile.behavior_pattern.daily_activity:
            activity_variance = np.var(user_profile.behavior_pattern.daily_activity)
            if activity_variance < 10:  # 일정한 활동
                traits['conscientiousness'] = 0.7
        
        return traits


class TrustCalculator:
    """신뢰도 계산 시스템"""
    
    def calculate_dynamic_trust(self, user_profile: UserProfile, recent_activity: List[Dict]) -> float:
        """동적 신뢰도 계산"""
        base_trust = user_profile.trust_score
        
        # 최근 활동 기반 조정
        if recent_activity:
            positive_activities = sum(1 for activity in recent_activity 
                                    if activity.get('type') in ['helpful_message', 'positive_reaction'])
            negative_activities = sum(1 for activity in recent_activity 
                                    if activity.get('type') in ['violation', 'warning'])
            
            activity_modifier = (positive_activities - negative_activities) * 2
            adjusted_trust = base_trust + activity_modifier
        else:
            adjusted_trust = base_trust
        
        # 계정 나이에 따른 가중치
        account_age = (datetime.now() - user_profile.first_seen).days
        age_multiplier = min(1.0, account_age / 365)  # 1년 기준
        
        final_trust = adjusted_trust * (0.5 + 0.5 * age_multiplier)
        return max(0.0, min(100.0, final_trust))


# 전역 사용자 관리자 인스턴스
advanced_user_manager = AdvancedUserManager()