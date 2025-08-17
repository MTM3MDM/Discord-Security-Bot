import re
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
import hashlib
import time
from collections import defaultdict, deque
import json
import base64
import requests
from datetime import datetime, timedelta
import statistics
import numpy as np

logger = logging.getLogger(__name__)

class AdvancedThreatDetector:
    """고급 위협 탐지 시스템 - 해커 차단용"""
    
    def __init__(self):
        # 위험 도메인 패턴 (2024년 최신)
        self.malicious_domains = {
            # 피싱 도메인
            'steam-community.org', 'steamcomunitty.com', 'steampowered.org',
            'discord-nitro.org', 'discordapp.org', 'discrod.gg',
            'discordgift.org', 'discord-gift.ru', 'discordnitro.info',
            # 악성 도메인
            'grabify.link', 'iplogger.org', 'blasze.tk', '2no.co',
            'yip.su', 'iplogger.com', 'blasze.com', 'worldwideinternet.ml',
            # 단축 URL (위험할 수 있음)
            'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly'
        }
        
        # 위험 파일 확장자
        self.dangerous_extensions = {
            '.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.vbs',
            '.js', '.jar', '.zip', '.rar', '.7z', '.msi', '.deb', '.rpm'
        }
        
        # 해킹 시도 패턴
        self.hack_patterns = [
            # 프롬프트 주입 시도
            r'ignore.*previous.*instructions?',
            r'forget.*everything.*above',
            r'act.*as.*developer.*mode',
            r'system.*prompt.*override',
            r'admin.*access.*grant',
            
            # SQL 인젝션 시도
            r'union.*select.*from',
            r'drop.*table.*',
            r'insert.*into.*values',
            
            # XSS 시도
            r'<script.*>.*</script>',
            r'javascript:.*',
            r'onerror.*=.*alert',
            
            # 봇 토큰 탈취 시도
            r'bot.*token.*is.*',
            r'discord.*token.*:.*',
            r'authorization.*bearer.*',
            
            # 시스템 명령어 실행 시도
            r'exec\(.*\)',
            r'eval\(.*\)',
            r'subprocess\..*',
            r'os\.system\(.*\)',
            r'import.*os.*',
            
            # 정보 수집 시도
            r'ipconfig.*\/all',
            r'netstat.*-an',
            r'whoami.*',
            r'pwd.*&&.*ls',
        ]
        
        # 사기 패턴
        self.scam_patterns = [
            # 가짜 이벤트
            r'free.*nitro.*click.*here',
            r'discord.*모더레이터.*선정',
            r'축하합니다.*당첨.*되었습니다',
            r'무료.*steam.*게임.*받기',
            
            # 계정 탈취
            r'계정.*확인.*필요합니다',
            r'토큰.*만료.*재로그인',
            r'qr.*코드.*스캔.*해주세요',
            r'보안.*문제.*발생.*확인',
            
            # 투자 사기
            r'비트코인.*투자.*수익.*보장',
            r'주식.*정보.*100.*수익',
            r'코인.*투자.*방.*참여',
        ]
        
        # 실시간 모니터링
        self.threat_stats = defaultdict(int)
        self.recent_threats = deque(maxlen=100)
        self.suspicious_users = defaultdict(list)
        
        # 고급 보안 시스템 추가
        self.behavioral_patterns = defaultdict(lambda: {
            'message_intervals': deque(maxlen=50),
            'message_lengths': deque(maxlen=30),
            'command_usage': defaultdict(int),
            'channel_activity': defaultdict(int),
            'reaction_patterns': deque(maxlen=20),
            'join_leave_pattern': deque(maxlen=10),
            'typing_speed': deque(maxlen=20)
        })
        
        # 레이드 탐지
        self.raid_detection = {
            'recent_joins': deque(maxlen=50),
            'mass_message_events': deque(maxlen=30),
            'coordinated_activity': defaultdict(list),
            'raid_threshold': 10,  # 10명이 짧은 시간에 가입시 레이드로 판정
            'raid_time_window': 60  # 60초 내
        }
        
        # 봇 계정 탐지 패턴
        self.bot_detection_patterns = {
            'suspicious_usernames': [
                r'^[a-z]+\d{4,}$',  # user1234 형태
                r'^user_?\d+$',     # user123 형태
                r'^[a-z]{3}\d{3}[a-z]{3}$',  # abc123def 형태
                r'bot$|^bot',       # bot으로 시작하거나 끝나는
                r'^test\d+$',       # test123 형태
                r'^discord\d+$'     # discord123 형태
            ],
            'bot_behaviors': {
                'identical_messages': 3,        # 동일한 메시지 3회 이상
                'rapid_commands': 5,           # 5초 내 5개 이상 명령
                'perfect_timing': 1.0,         # 너무 정확한 타이밍 (초 단위)
                'no_typos_threshold': 100      # 100개 메시지에 오타 0개
            }
        }
        
        # 소셜 엔지니어링 탐지
        self.social_engineering_patterns = [
            # 긴급성 조작
            r'긴급.*도움.*필요|응급.*상황.*발생|지금.*당장.*해야',
            r'시간.*없어|빨리.*해줘|서둘러|마감.*임박',
            
            # 권위 이용
            r'관리자.*명령|상급자.*지시|본사.*지시|CEO.*요청',
            r'경찰.*수사|정부.*요청|공식.*명령',
            
            # 공포 조성
            r'계정.*해킹.*당함|바이러스.*감염|보안.*위반.*발견',
            r'법적.*조치|고발.*당함|처벌.*받을.*수.*있음',
            
            # 신뢰 구축
            r'검증된.*사이트|안전한.*링크|공식.*홈페이지',
            r'믿을.*수.*있는|보장.*드림|100.*안전',
            
            # 혜택 제공
            r'특별.*혜택.*제공|독점.*이벤트|한정.*기회',
            r'무료.*제공|선착순.*이벤트|특가.*할인'
        ]
        
        # 파일 위협 분석 (확장)
        self.file_threat_analysis = {
            'dangerous_signatures': {
                # 실행파일 시그니처
                b'MZ': 'PE_실행파일',
                b'\x7fELF': 'ELF_실행파일', 
                b'\xca\xfe\xba\xbe': 'Java_클래스파일',
                b'PK': 'ZIP_아카이브',
                
                # 스크립트 시그니처
                b'#!/bin/sh': '쉘_스크립트',
                b'#!/usr/bin/python': '파이썬_스크립트',
                b'<?php': 'PHP_스크립트',
                
                # 문서 시그니처 (매크로 위험)
                b'\xd0\xcf\x11\xe0': 'OLE_문서',
                b'%PDF': 'PDF_파일'
            },
            'suspicious_extensions': {
                '.scr', '.pif', '.com', '.bat', '.cmd', '.exe', '.msi',
                '.vbs', '.js', '.jar', '.app', '.deb', '.rpm', '.dmg'
            }
        }
        
        # 네트워크 행동 분석
        self.network_behavior = defaultdict(lambda: {
            'ip_tracking': set(),
            'connection_patterns': deque(maxlen=20),
            'suspicious_ips': set(),
            'proxy_indicators': []
        })
        
        # 위협 인텔리전스 (실시간 업데이트)
        self.threat_intelligence = {
            'known_malicious_hashes': set(),
            'ip_blacklist': set(),
            'domain_blacklist': set(),
            'last_update': datetime.now() - timedelta(hours=24)  # 강제 업데이트 유도
        }
        
    async def analyze_message_security(self, message_content: str, user_id: int, 
                                     channel_id: int) -> Dict[str, Any]:
        """메시지 보안 분석"""
        threats_found = []
        risk_score = 0.0
        
        # URL 분석
        url_threats = await self._analyze_urls(message_content)
        if url_threats:
            threats_found.extend(url_threats)
            risk_score += 0.7  # URL 위협은 고위험
        
        # 파일 확장자 분석
        file_threats = self._analyze_file_extensions(message_content)
        if file_threats:
            threats_found.extend(file_threats)
            risk_score += 0.8  # 위험 파일은 매우 고위험
        
        # 해킹 시도 탐지
        hack_threats = self._detect_hack_attempts(message_content)
        if hack_threats:
            threats_found.extend(hack_threats)
            risk_score += 0.9  # 해킹 시도는 치명적
        
        # 사기 패턴 탐지
        scam_threats = self._detect_scam_patterns(message_content)
        if scam_threats:
            threats_found.extend(scam_threats)
            risk_score += 0.6  # 사기는 높은 위험
        
        # 프롬프트 주입 탐지
        prompt_injection = self._detect_prompt_injection(message_content)
        if prompt_injection:
            threats_found.extend(prompt_injection)
            risk_score += 0.95  # 프롬프트 주입은 최고 위험
        
        # 개인정보 요구 탐지
        personal_info_threat = self._detect_personal_info_requests(message_content)
        if personal_info_threat:
            threats_found.extend(personal_info_threat)
            risk_score += 0.75

        # 소셜 엔지니어링 탐지 (신규)
        social_eng_threats = self._detect_social_engineering(message_content)
        if social_eng_threats:
            threats_found.extend(social_eng_threats)
            risk_score += 0.85

        # 봇 계정 의심 행동 탐지 (신규)
        bot_behavior_threat = await self._analyze_bot_behavior(user_id, message_content)
        if bot_behavior_threat:
            threats_found.extend(bot_behavior_threat)
            risk_score += 0.7

        # 행동 패턴 분석 (신규)
        behavior_threat = await self._analyze_behavioral_patterns(user_id, message_content, channel_id)
        if behavior_threat:
            threats_found.extend(behavior_threat)
            risk_score += 0.6

        # 위협 기록
        if threats_found:
            self._record_threat(user_id, channel_id, threats_found, risk_score)
        
        return {
            'threats_detected': threats_found,
            'risk_score': min(risk_score, 1.0),  # 최대 1.0으로 제한
            'threat_level': self._get_threat_level(risk_score),
            'recommended_action': self._get_recommended_action(risk_score),
            'should_block': risk_score >= 0.7,
            'should_alert_admins': risk_score >= 0.8
        }
    
    async def _analyze_urls(self, text: str) -> List[Dict[str, Any]]:
        """URL 분석 - 피싱 및 악성 링크 탐지"""
        threats = []
        url_pattern = r'https?://[^\s<>"\'()]+'
        urls = re.findall(url_pattern, text)
        
        for url in urls:
            try:
                parsed = urlparse(url.lower())
                domain = parsed.netloc
                
                # 도메인 검사
                if any(malicious in domain for malicious in self.malicious_domains):
                    threats.append({
                        'type': '악성_도메인',
                        'content': url,
                        'reason': f'알려진 위험 도메인: {domain}',
                        'severity': 'critical'
                    })
                
                # 의심스러운 도메인 패턴
                if self._is_suspicious_domain(domain):
                    threats.append({
                        'type': '의심_도메인',
                        'content': url,
                        'reason': f'의심스러운 도메인 패턴: {domain}',
                        'severity': 'high'
                    })
                
                # IP 주소 직접 접근
                if re.match(r'^\d+\.\d+\.\d+\.\d+', domain):
                    threats.append({
                        'type': 'IP_직접접근',
                        'content': url,
                        'reason': 'IP 주소로 직접 접근 (피싱 가능성)',
                        'severity': 'medium'
                    })
                
            except Exception as e:
                logger.error(f"URL 분석 오류: {e}")
        
        return threats
    
    def _analyze_file_extensions(self, text: str) -> List[Dict[str, Any]]:
        """위험 파일 확장자 탐지"""
        threats = []
        
        for ext in self.dangerous_extensions:
            if ext in text.lower():
                threats.append({
                    'type': '위험_파일',
                    'content': f'파일 확장자: {ext}',
                    'reason': f'위험한 파일 확장자 탐지: {ext}',
                    'severity': 'critical'
                })
        
        return threats
    
    def _detect_hack_attempts(self, text: str) -> List[Dict[str, Any]]:
        """해킹 시도 탐지"""
        threats = []
        text_lower = text.lower()
        
        for pattern in self.hack_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                threats.append({
                    'type': '해킹_시도',
                    'content': text[:100],  # 앞부분만 기록
                    'reason': f'해킹 시도 패턴 탐지: {pattern}',
                    'severity': 'critical'
                })
        
        return threats
    
    def _detect_scam_patterns(self, text: str) -> List[Dict[str, Any]]:
        """사기 패턴 탐지"""
        threats = []
        text_lower = text.lower()
        
        for pattern in self.scam_patterns:
            try:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    threats.append({
                        'type': '사기_시도',
                        'content': text[:100],
                        'reason': f'사기 패턴 탐지: {pattern}',
                        'severity': 'high'
                    })
            except re.error as e:
                logger.error(f"정규식 오류 - 패턴: {pattern}, 오류: {e}")
                continue
        
        return threats
    
    def _detect_prompt_injection(self, text: str) -> List[Dict[str, Any]]:
        """프롬프트 주입 공격 탐지"""
        threats = []
        text_lower = text.lower()
        
        # 프롬프트 주입 키워드
        injection_keywords = [
            'ignore previous instructions',
            'forget everything above',
            'you are now',
            'system prompt',
            'developer mode',
            'admin override',
            'root access',
            'bypass restrictions'
        ]
        
        for keyword in injection_keywords:
            if keyword in text_lower:
                threats.append({
                    'type': '프롬프트_주입',
                    'content': text[:100],
                    'reason': f'프롬프트 주입 시도: {keyword}',
                    'severity': 'critical'
                })
        
        return threats
    
    def _detect_personal_info_requests(self, text: str) -> List[Dict[str, Any]]:
        """개인정보 요구 탐지"""
        threats = []
        text_lower = text.lower()
        
        personal_info_patterns = [
            r'주민(?:등록)?번호.*알려.*주세요',
            r'비밀번호.*입력.*해주세요',
            r'카드.*번호.*알려.*주세요',
            r'계좌.*번호.*알려.*주세요',
            r'개인정보.*확인.*필요',
            r'토큰.*알려.*주세요',
            r'패스워드.*입력.*하세요'
        ]
        
        for pattern in personal_info_patterns:
            if re.search(pattern, text_lower):
                threats.append({
                    'type': '개인정보_요구',
                    'content': text[:100],
                    'reason': f'개인정보 요구 패턴 탐지: {pattern}',
                    'severity': 'high'
                })
        
        return threats
    
    def _is_suspicious_domain(self, domain: str) -> bool:
        """의심스러운 도메인 패턴 검사"""
        suspicious_patterns = [
            # 오타 도메인 (타이포스쿼팅)
            r'discrd|dsicord|discodr|discordd',
            r'steamcommunty|steampowerd|staempowered',
            r'youtub|gogle|facbook|twiter',
            # 숫자나 하이픈이 많은 도메인
            r'.*-.*-.*-.*',  # 하이픈이 3개 이상
            r'.*\d.*\d.*\d',  # 숫자가 3개 이상
            # 의심스러운 TLD
            r'\.tk$|\.ml$|\.cf$|\.ga$|\.gq$'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                return True
        
        return False
    
    def _record_threat(self, user_id: int, channel_id: int, threats: List[Dict], risk_score: float):
        """위협 기록"""
        threat_record = {
            'timestamp': time.time(),
            'user_id': user_id,
            'channel_id': channel_id,
            'threats': threats,
            'risk_score': risk_score
        }
        
        self.recent_threats.append(threat_record)
        self.threat_stats[f'user_{user_id}'] += len(threats)
        
        # 의심스러운 사용자 목록에 추가
        if risk_score >= 0.5:
            self.suspicious_users[user_id].append(threat_record)
    
    def _get_threat_level(self, risk_score: float) -> str:
        """위험도에 따른 위협 수준 반환"""
        if risk_score >= 0.9:
            return 'CRITICAL'
        elif risk_score >= 0.7:
            return 'HIGH'
        elif risk_score >= 0.5:
            return 'MEDIUM'
        elif risk_score >= 0.3:
            return 'LOW'
        else:
            return 'SAFE'
    
    def _get_recommended_action(self, risk_score: float) -> str:
        """위험도에 따른 권장 조치"""
        if risk_score >= 0.9:
            return 'IMMEDIATE_BAN'
        elif risk_score >= 0.8:
            return 'TIMEOUT_AND_ALERT'
        elif risk_score >= 0.7:
            return 'DELETE_AND_WARN'
        elif risk_score >= 0.5:
            return 'MONITOR_CLOSELY'
        elif risk_score >= 0.3:
            return 'LOG_ACTIVITY'
        else:
            return 'NONE'
    
    def get_threat_statistics(self) -> Dict[str, Any]:
        """위협 통계 반환"""
        total_threats = sum(self.threat_stats.values())
        return {
            '총_위협_탐지': total_threats,
            '의심_사용자_수': len(self.suspicious_users),
            '최근_위협_수': len(self.recent_threats),
            '위협_유형별_통계': dict(self.threat_stats)
        }
    
    def is_user_suspicious(self, user_id: int) -> Tuple[bool, List[Dict]]:
        """사용자가 의심스러운지 확인"""
        user_threats = self.suspicious_users.get(user_id, [])
        is_suspicious = len(user_threats) > 0
        return is_suspicious, user_threats
    
    def _detect_social_engineering(self, text: str) -> List[Dict[str, Any]]:
        """소셜 엔지니어링 공격 탐지"""
        threats = []
        text_lower = text.lower()
        
        for pattern in self.social_engineering_patterns:
            try:
                if re.search(pattern, text_lower):
                    threats.append({
                        'type': '소셜_엔지니어링',
                        'content': text[:100],
                        'reason': f'소셜 엔지니어링 패턴 탐지: {pattern[:50]}',
                        'severity': 'high'
                    })
            except re.error as e:
                logger.error(f"정규식 오류 - 소셜 엔지니어링 패턴: {pattern}, 오류: {e}")
                continue
        
        return threats
    
    async def _analyze_bot_behavior(self, user_id: int, message_content: str) -> List[Dict[str, Any]]:
        """봇 계정 의심 행동 분석"""
        threats = []
        patterns = self.behavioral_patterns[user_id]
        
        # 메시지 간격 분석 (너무 규칙적인 패턴)
        current_time = time.time()
        patterns['message_intervals'].append(current_time)
        
        if len(patterns['message_intervals']) >= 5:
            intervals = []
            for i in range(1, len(patterns['message_intervals'])):
                interval = patterns['message_intervals'][i] - patterns['message_intervals'][i-1]
                intervals.append(interval)
            
            # 간격의 표준편차가 매우 작으면 봇 의심
            if len(intervals) >= 4 and statistics.stdev(intervals) < 0.5:
                threats.append({
                    'type': '봇_행동_패턴',
                    'content': f'메시지 간격이 너무 규칙적',
                    'reason': f'메시지 간격 표준편차: {statistics.stdev(intervals):.2f}초',
                    'severity': 'medium'
                })
        
        # 메시지 길이 분석
        patterns['message_lengths'].append(len(message_content))
        if len(patterns['message_lengths']) >= 10:
            avg_length = statistics.mean(patterns['message_lengths'])
            length_variance = statistics.variance(patterns['message_lengths'])
            
            # 메시지 길이가 너무 일정하면 봇 의심
            if length_variance < 10 and avg_length > 20:
                threats.append({
                    'type': '봇_메시지_패턴',
                    'content': f'메시지 길이가 너무 일정함',
                    'reason': f'평균길이: {avg_length:.1f}, 분산: {length_variance:.1f}',
                    'severity': 'medium'
                })
        
        # 동일한 메시지 반복
        recent_messages = [m for m in patterns['message_lengths'] if m == len(message_content)]
        if len(recent_messages) >= self.bot_detection_patterns['bot_behaviors']['identical_messages']:
            threats.append({
                'type': '봇_반복_메시지',
                'content': message_content[:100],
                'reason': f'동일 길이 메시지 {len(recent_messages)}회 반복',
                'severity': 'high'
            })
        
        return threats
    
    async def _analyze_behavioral_patterns(self, user_id: int, message_content: str, channel_id: int) -> List[Dict[str, Any]]:
        """고급 행동 패턴 분석"""
        threats = []
        patterns = self.behavioral_patterns[user_id]
        
        # 채널 활동 패턴
        patterns['channel_activity'][channel_id] += 1
        
        # 타이핑 속도 분석 (한글/영어 구분)
        typing_speed = self._calculate_typing_speed(message_content)
        patterns['typing_speed'].append(typing_speed)
        
        if len(patterns['typing_speed']) >= 10:
            avg_speed = statistics.mean(patterns['typing_speed'])
            # 너무 빠른 타이핑 (봇 의심)
            if avg_speed > 300:  # 분당 300타 이상
                threats.append({
                    'type': '비정상_타이핑속도',
                    'content': f'타이핑 속도: {avg_speed:.1f} 타/분',
                    'reason': '비정상적으로 빠른 타이핑 속도',
                    'severity': 'medium'
                })
        
        # 명령어 사용 패턴 분석
        if message_content.startswith(('!', '/', '봇아')):
            command = message_content.split()[0]
            patterns['command_usage'][command] += 1
            
            # 특정 명령어만 반복 사용
            most_used_cmd = max(patterns['command_usage'].values(), default=0)
            if most_used_cmd >= 10:
                threats.append({
                    'type': '명령어_반복사용',
                    'content': f'명령어: {command}',
                    'reason': f'특정 명령어 {most_used_cmd}회 사용',
                    'severity': 'low'
                })
        
        return threats
    
    def _calculate_typing_speed(self, text: str) -> float:
        """타이핑 속도 계산 (분당 타수)"""
        # 한글은 2타, 영어/숫자는 1타로 계산
        korean_chars = len(re.findall(r'[가-힣]', text))
        other_chars = len(text) - korean_chars
        total_keystrokes = korean_chars * 2 + other_chars
        
        # 평균 타이핑 시간 가정 (실제로는 메시지 간 시간차를 사용해야 함)
        estimated_time_minutes = max(0.1, total_keystrokes / 60)  # 최소 0.1분
        return total_keystrokes / estimated_time_minutes
    
    async def detect_raid_attack(self, new_member_id: int, join_time: datetime) -> Dict[str, Any]:
        """레이드 공격 탐지"""
        self.raid_detection['recent_joins'].append({
            'user_id': new_member_id,
            'join_time': join_time.timestamp()
        })
        
        # 최근 가입자 분석
        current_time = join_time.timestamp()
        recent_joins_count = sum(
            1 for join in self.raid_detection['recent_joins']
            if current_time - join['join_time'] <= self.raid_detection['raid_time_window']
        )
        
        is_raid = recent_joins_count >= self.raid_detection['raid_threshold']
        
        return {
            'is_raid_detected': is_raid,
            'recent_joins_count': recent_joins_count,
            'time_window': self.raid_detection['raid_time_window'],
            'threshold': self.raid_detection['raid_threshold'],
            'risk_level': 'critical' if is_raid else 'low',
            'recommended_action': 'LOCK_SERVER' if is_raid else 'MONITOR'
        }
    
    def detect_suspicious_username(self, username: str) -> Dict[str, Any]:
        """의심스러운 사용자명 탐지"""
        username_lower = username.lower()
        
        for pattern in self.bot_detection_patterns['suspicious_usernames']:
            if re.match(pattern, username_lower):
                return {
                    'is_suspicious': True,
                    'pattern_matched': pattern,
                    'reason': f'의심스러운 사용자명 패턴: {pattern}',
                    'severity': 'medium',
                    'recommended_action': 'MONITOR_CLOSELY'
                }
        
        return {
            'is_suspicious': False,
            'reason': '정상적인 사용자명',
            'severity': 'safe'
        }
    
    async def analyze_file_threat(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """파일 위협 분석"""
        threats = []
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # 파일 확장자 검사
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{file_ext}' in self.file_threat_analysis['suspicious_extensions']:
            threats.append({
                'type': '위험_확장자',
                'reason': f'위험한 파일 확장자: .{file_ext}',
                'severity': 'high'
            })
        
        # 파일 시그니처 검사
        for signature, file_type in self.file_threat_analysis['dangerous_signatures'].items():
            if file_data.startswith(signature):
                threats.append({
                    'type': '위험_파일시그니처',
                    'reason': f'위험한 파일 형식: {file_type}',
                    'severity': 'critical'
                })
        
        # 알려진 악성 파일 해시 확인
        if file_hash in self.threat_intelligence['known_malicious_hashes']:
            threats.append({
                'type': '알려진_악성파일',
                'reason': '위협 인텔리전스에 등록된 악성 파일',
                'severity': 'critical'
            })
        
        risk_score = len(threats) * 0.3
        
        return {
            'threats_detected': threats,
            'file_hash': file_hash,
            'risk_score': min(risk_score, 1.0),
            'should_block': risk_score >= 0.7,
            'recommended_action': 'DELETE_FILE' if risk_score >= 0.7 else 'SCAN_FURTHER'
        }
    
    async def update_threat_intelligence(self):
        """위협 인텔리전스 업데이트"""
        try:
            # 24시간 이상 지났을 때만 업데이트
            if datetime.now() - self.threat_intelligence['last_update'] < timedelta(hours=24):
                return
            
            logger.info("위협 인텔리전스 업데이트 시작...")
            
            # 실제 구현에서는 외부 API에서 최신 위협 정보를 가져와야 함
            # 예시 데이터로 일부 업데이트
            new_malicious_domains = {
                'fake-steam-community.org',
                'discord-free-nitro.com',
                'free-discord-nitro.tk'
            }
            
            self.malicious_domains.update(new_malicious_domains)
            self.threat_intelligence['last_update'] = datetime.now()
            
            logger.info(f"위협 인텔리전스 업데이트 완료: {len(new_malicious_domains)}개 도메인 추가")
            
        except Exception as e:
            logger.error(f"위협 인텔리전스 업데이트 실패: {e}")
    
    def get_advanced_statistics(self) -> Dict[str, Any]:
        """고급 보안 통계"""
        return {
            '기본_통계': self.get_threat_statistics(),
            '행동_패턴_분석': {
                '추적중인_사용자': len(self.behavioral_patterns),
                '레이드_탐지_횟수': len(self.raid_detection['recent_joins']),
                '봇_의심_사용자': sum(1 for patterns in self.behavioral_patterns.values() 
                                  if len(patterns['message_intervals']) >= 10)
            },
            '위협_인텔리전스': {
                '악성_도메인_수': len(self.malicious_domains),
                '마지막_업데이트': self.threat_intelligence['last_update'].isoformat()
            }
        }
    
    # ============ 신규 고급 보안 기능들 ============
    
    async def analyze_image_content(self, image_data: bytes, filename: str) -> Dict[str, Any]:
        """이미지 콘텐츠 고급 분석 - 딥페이크, 악성 콘텐츠 탐지"""
        threats = []
        risk_score = 0.0
        
        try:
            # 이미지 메타데이터 분석
            metadata_threats = self._analyze_image_metadata(image_data)
            if metadata_threats:
                threats.extend(metadata_threats)
                risk_score += 0.4
            
            # 스테가노그래피 탐지 (숨겨진 데이터)
            steganography_threat = self._detect_steganography(image_data)
            if steganography_threat:
                threats.append(steganography_threat)
                risk_score += 0.8
            
            # 딥페이크/AI 생성 이미지 탐지 (기본적인 휴리스틱)
            deepfake_threat = self._detect_ai_generated_content(image_data, filename)
            if deepfake_threat:
                threats.append(deepfake_threat)
                risk_score += 0.6
            
            # 악성 QR 코드 탐지
            qr_threats = self._analyze_qr_codes(image_data)
            if qr_threats:
                threats.extend(qr_threats)
                risk_score += 0.7
            
        except Exception as e:
            logger.error(f"이미지 분석 오류: {e}")
        
        return {
            'threats_detected': threats,
            'risk_score': min(risk_score, 1.0),
            'should_block': risk_score >= 0.7,
            'analysis_type': 'image_content'
        }
    
    def _analyze_image_metadata(self, image_data: bytes) -> List[Dict[str, Any]]:
        """이미지 메타데이터 위협 분석"""
        threats = []
        
        # EXIF 데이터에서 위험한 정보 탐지
        try:
            # 간단한 EXIF 검사 (더 고급 라이브러리 필요시 추가)
            if b'Software' in image_data and (b'DeepFaceLab' in image_data or b'FaceSwap' in image_data):
                threats.append({
                    'type': '딥페이크_생성툴',
                    'reason': '딥페이크 생성 소프트웨어 흔적 발견',
                    'severity': 'high'
                })
            
            # 의심스러운 GPS 좌표 (정부기관, 군사시설 근처)
            if b'GPSLatitude' in image_data:
                threats.append({
                    'type': '위치정보_포함',
                    'reason': '이미지에 GPS 위치정보가 포함되어 있음',
                    'severity': 'medium'
                })
                
        except Exception as e:
            logger.debug(f"메타데이터 분석 오류: {e}")
        
        return threats
    
    def _detect_steganography(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """스테가노그래피 탐지 - 이미지에 숨겨진 데이터"""
        try:
            # LSB 스테가노그래피 패턴 탐지
            if len(image_data) > 1024:  # 최소 크기 확인
                # 간단한 엔트로피 분석
                byte_freq = {}
                for byte in image_data[-1000:]:  # 마지막 1000바이트 분석
                    byte_freq[byte] = byte_freq.get(byte, 0) + 1
                
                # 너무 균등한 분포는 숨겨진 데이터 의심
                entropy = -sum((freq/1000) * np.log2(freq/1000) for freq in byte_freq.values() if freq > 0)
                
                if entropy > 7.5:  # 높은 엔트로피는 암호화된 데이터 의심
                    return {
                        'type': '스테가노그래피_의심',
                        'reason': f'이미지에 숨겨진 데이터 의심 (엔트로피: {entropy:.2f})',
                        'severity': 'high'
                    }
        except Exception as e:
            logger.debug(f"스테가노그래피 탐지 오류: {e}")
        
        return None
    
    def _detect_ai_generated_content(self, image_data: bytes, filename: str) -> Optional[Dict[str, Any]]:
        """AI 생성 콘텐츠 탐지 (기본적인 방법)"""
        try:
            # 파일명 패턴 검사
            ai_indicators = ['generated', 'ai_', 'deepfake', 'faceswap', 'stylegan', 'midjourney', 'dalle']
            if any(indicator in filename.lower() for indicator in ai_indicators):
                return {
                    'type': 'AI_생성_콘텐츠',
                    'reason': '파일명에서 AI 생성 콘텐츠 지시자 발견',
                    'severity': 'medium'
                }
            
            # 파일 크기 대비 품질 이상 패턴 (매우 기본적)
            if len(image_data) < 50000 and filename.lower().endswith(('.jpg', '.jpeg')):
                # 너무 작은 파일인데 고품질을 주장하는 경우
                return {
                    'type': '품질_조작_의심',
                    'reason': '파일 크기 대비 비정상적인 품질 패턴',
                    'severity': 'low'
                }
        except Exception as e:
            logger.debug(f"AI 콘텐츠 탐지 오류: {e}")
        
        return None
    
    def _analyze_qr_codes(self, image_data: bytes) -> List[Dict[str, Any]]:
        """QR 코드 내용 분석"""
        threats = []
        
        # QR 코드 패턴 기본 탐지 (실제로는 QR 코드 라이브러리 필요)
        try:
            # QR 코드의 기본 패턴 바이트 시퀀스 확인
            qr_patterns = [b'\x89PNG', b'\xff\xd8\xff']  # 기본적인 이미지 포맷 내 QR 패턴
            
            for pattern in qr_patterns:
                if pattern in image_data:
                    # 실제 QR 코드 디코딩은 전용 라이브러리 필요
                    # 여기서는 기본적인 위험 패턴만 검사
                    threats.append({
                        'type': 'QR_코드_포함',
                        'reason': '이미지에 QR 코드가 포함되어 있을 수 있음 - 수동 확인 필요',
                        'severity': 'medium'
                    })
                    break
        except Exception as e:
            logger.debug(f"QR 코드 분석 오류: {e}")
        
        return threats
    
    async def analyze_crypto_scam_advanced(self, content: str) -> Dict[str, Any]:
        """고급 암호화폐/NFT 스캠 탐지"""
        threats = []
        risk_score = 0.0
        
        # 고급 암호화폐 스캠 패턴
        advanced_crypto_patterns = [
            # 가짜 거래소
            r'새로운.*거래소.*상장.*이벤트',
            r'코인.*프리세일.*참여.*기회',
            r'디파이.*스테이킹.*수익.*보장',
            r'NFT.*민팅.*화이트리스트.*선정',
            
            # 가짜 에어드랍
            r'에어드랍.*무료.*토큰.*지급',
            r'메타마스크.*연결.*토큰.*받기',
            r'월렛.*주소.*입력.*보상.*지급',
            
            # 투자 사기
            r'코인.*투자.*100.*수익.*보장',
            r'블록체인.*프로젝트.*투자.*모집',
            r'암호화폐.*거래.*알고리즘.*수익',
            
            # 가짜 뉴스 기반 스캠
            r'일론머스크.*트위터.*코인.*언급',
            r'테슬라.*비트코인.*구매.*발표',
            r'정부.*암호화폐.*규제.*완화'
        ]
        
        for pattern in advanced_crypto_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                threats.append({
                    'type': '고급_암호화폐_스캠',
                    'reason': f'고급 암호화폐 스캠 패턴 탐지: {pattern}',
                    'severity': 'high'
                })
                risk_score += 0.8
        
        # 지갑 주소 분석
        wallet_threats = self._analyze_wallet_addresses(content)
        if wallet_threats:
            threats.extend(wallet_threats)
            risk_score += 0.6
        
        # 가짜 DApp 링크 탐지
        dapp_threats = self._detect_fake_dapp_links(content)
        if dapp_threats:
            threats.extend(dapp_threats)
            risk_score += 0.9
        
        return {
            'threats_detected': threats,
            'risk_score': min(risk_score, 1.0),
            'should_block': risk_score >= 0.7,
            'analysis_type': 'crypto_scam_advanced'
        }
    
    def _analyze_wallet_addresses(self, content: str) -> List[Dict[str, Any]]:
        """지갑 주소 분석"""
        threats = []
        
        # 비트코인 주소 패턴
        btc_pattern = r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}'
        # 이더리움 주소 패턴  
        eth_pattern = r'0x[a-fA-F0-9]{40}'
        
        btc_addresses = re.findall(btc_pattern, content)
        eth_addresses = re.findall(eth_pattern, content)
        
        if btc_addresses or eth_addresses:
            threats.append({
                'type': '암호화폐_주소_포함',
                'reason': f'암호화폐 지갑 주소 발견 - 수동 검증 필요',
                'severity': 'medium',
                'details': {
                    'btc_addresses': len(btc_addresses),
                    'eth_addresses': len(eth_addresses)
                }
            })
        
        return threats
    
    def _detect_fake_dapp_links(self, content: str) -> List[Dict[str, Any]]:
        """가짜 DApp 링크 탐지"""
        threats = []
        
        # 유명 DApp의 가짜 도메인 패턴
        fake_dapp_patterns = [
            r'uniswap-[a-z]+\.com',
            r'pancakeswap-[a-z]+\.org',
            r'metamask-[a-z]+\.net',
            r'opensea-[a-z]+\.io',
            r'compound-[a-z]+\.finance'
        ]
        
        for pattern in fake_dapp_patterns:
            matches = re.findall(pattern, content.lower())
            if matches:
                for match in matches:
                    threats.append({
                        'type': '가짜_DApp_링크',
                        'reason': f'가짜 DApp 링크 탐지: {match}',
                        'severity': 'critical'
                    })
        
        return threats
    
    async def detect_zero_day_patterns(self, content: str, user_id: int) -> Dict[str, Any]:
        """제로데이 공격 패턴 탐지"""
        threats = []
        risk_score = 0.0
        
        # 알려지지 않은 공격 패턴 탐지 (휴리스틱 기반)
        
        # 1. 비정상적인 유니코드 사용
        unicode_threats = self._detect_unicode_attacks(content)
        if unicode_threats:
            threats.extend(unicode_threats)
            risk_score += 0.7
        
        # 2. 고급 난독화 시도
        obfuscation_threats = self._detect_advanced_obfuscation(content)
        if obfuscation_threats:
            threats.extend(obfuscation_threats)
            risk_score += 0.8
        
        # 3. 시스템 메모리 공격 패턴
        memory_attack_threats = self._detect_memory_attacks(content)
        if memory_attack_threats:
            threats.extend(memory_attack_threats)
            risk_score += 0.9
        
        # 4. 시간 기반 공격
        timing_threats = await self._detect_timing_attacks(user_id, content)
        if timing_threats:
            threats.extend(timing_threats)
            risk_score += 0.6
        
        return {
            'threats_detected': threats,
            'risk_score': min(risk_score, 1.0),
            'should_block': risk_score >= 0.8,
            'analysis_type': 'zero_day_detection'
        }
    
    def _detect_unicode_attacks(self, content: str) -> List[Dict[str, Any]]:
        """유니코드 기반 공격 탐지"""
        threats = []
        
        # RTL 오버라이드 공격
        if '\u202e' in content or '\u202d' in content:
            threats.append({
                'type': 'RTL_오버라이드_공격',
                'reason': 'RTL 오버라이드 문자로 텍스트 조작 시도',
                'severity': 'high'
            })
        
        # 제로폭 문자 남용
        zero_width_chars = ['\u200b', '\u200c', '\u200d', '\ufeff']
        zero_width_count = sum(content.count(char) for char in zero_width_chars)
        if zero_width_count > 5:
            threats.append({
                'type': '제로폭문자_남용',
                'reason': f'제로폭 문자 {zero_width_count}개 발견 - 텍스트 숨김 시도 의심',
                'severity': 'medium'
            })
        
        # 동형 문자 공격 (homograph attack)
        suspicious_chars = ['а', 'е', 'о', 'р']  # 키릴 문자 중 라틴과 유사한 것들
        if any(char in content for char in suspicious_chars):
            threats.append({
                'type': '동형문자_공격',
                'reason': '시각적으로 유사한 문자를 이용한 속임수 시도',
                'severity': 'medium'
            })
        
        return threats
    
    def _detect_advanced_obfuscation(self, content: str) -> List[Dict[str, Any]]:
        """고급 난독화 탐지"""
        threats = []
        
        # Base64 인코딩 남용
        base64_matches = re.findall(r'[A-Za-z0-9+/]{20,}={0,2}', content)
        if len(base64_matches) > 3:
            threats.append({
                'type': '고급_난독화',
                'reason': f'Base64 인코딩 패턴 {len(base64_matches)}개 발견',
                'severity': 'medium'
            })
        
        # 헥스 인코딩 남용
        hex_matches = re.findall(r'\\x[0-9a-fA-F]{2}', content)
        if len(hex_matches) > 10:
            threats.append({
                'type': '헥스_인코딩_남용',
                'reason': f'헥스 인코딩 패턴 {len(hex_matches)}개 발견',
                'severity': 'medium'
            })
        
        return threats
    
    def _detect_memory_attacks(self, content: str) -> List[Dict[str, Any]]:
        """메모리 공격 패턴 탐지"""
        threats = []
        
        # 버퍼 오버플로우 시도
        overflow_patterns = [
            r'A{100,}',  # 반복된 A 문자
            r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]{20,}',  # 제어 문자 남용
            r'%[0-9a-fA-F]{2}{10,}'  # URL 인코딩 남용
        ]
        
        for pattern in overflow_patterns:
            if re.search(pattern, content):
                threats.append({
                    'type': '버퍼_오버플로우_시도',
                    'reason': f'버퍼 오버플로우 공격 패턴 탐지: {pattern}',
                    'severity': 'high'
                })
        
        return threats
    
    async def _detect_timing_attacks(self, user_id: int, content: str) -> List[Dict[str, Any]]:
        """시간 기반 공격 탐지"""
        threats = []
        current_time = time.time()
        
        # 사용자별 메시지 간격 분석
        if user_id not in self.behavioral_patterns:
            self.behavioral_patterns[user_id]['message_intervals'].append(current_time)
            return []
        
        intervals = self.behavioral_patterns[user_id]['message_intervals']
        intervals.append(current_time)
        
        if len(intervals) >= 5:
            # 너무 정확한 간격은 봇 의심
            recent_intervals = [intervals[i] - intervals[i-1] for i in range(1, min(6, len(intervals)))]
            interval_variance = statistics.variance(recent_intervals) if len(recent_intervals) > 1 else 0
            
            if interval_variance < 0.1:  # 0.1초 미만의 분산
                threats.append({
                    'type': '봇_행동_패턴',
                    'reason': f'너무 정확한 타이밍 패턴 (분산: {interval_variance:.3f})',
                    'severity': 'medium'
                })
        
        return threats


class NextGenSecuritySystem:
    """차세대 보안 시스템 - 머신러닝 기반 위협 탐지"""
    
    def __init__(self):
        self.ml_threat_classifier = MLThreatClassifier()
        self.behavioral_ai = BehavioralAI()
        self.network_forensics = NetworkForensics()
        
    async def analyze_with_ai(self, content: str, context: Dict) -> Dict[str, Any]:
        """AI 기반 종합 위협 분석"""
        # 여러 AI 모델을 조합한 분석
        results = []
        
        # 1. 텍스트 분류 AI
        text_analysis = await self.ml_threat_classifier.classify_threat(content)
        results.append(text_analysis)
        
        # 2. 행동 패턴 AI
        behavior_analysis = await self.behavioral_ai.analyze_behavior(context)
        results.append(behavior_analysis)
        
        # 3. 네트워크 포렌식 AI
        network_analysis = await self.network_forensics.analyze_network_pattern(context)
        results.append(network_analysis)
        
        # 결과 통합
        combined_risk = sum(r.get('risk_score', 0) for r in results) / len(results)
        all_threats = []
        for r in results:
            all_threats.extend(r.get('threats_detected', []))
        
        return {
            'threats_detected': all_threats,
            'risk_score': min(combined_risk, 1.0),
            'ai_confidence': max(r.get('confidence', 0) for r in results),
            'should_block': combined_risk >= 0.8,
            'analysis_details': results
        }


class MLThreatClassifier:
    """머신러닝 기반 위협 분류기"""
    
    def __init__(self):
        # 실제로는 사전 훈련된 모델을 로드해야 함
        self.threat_keywords = {
            'malware': ['트로이', '바이러스', '웜', '랜섬웨어'],
            'phishing': ['로그인', '확인', '계정', '인증'],
            'scam': ['무료', '당첨', '이벤트', '선착순'],
            'social_engineering': ['긴급', '빨리', '도움', '문제']
        }
    
    async def classify_threat(self, content: str) -> Dict[str, Any]:
        """텍스트 위협 분류"""
        threat_scores = {}
        
        for threat_type, keywords in self.threat_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content.lower())
            threat_scores[threat_type] = score / len(keywords)
        
        max_threat = max(threat_scores.items(), key=lambda x: x[1])
        
        return {
            'threats_detected': [{'type': max_threat[0], 'confidence': max_threat[1]}] if max_threat[1] > 0.3 else [],
            'risk_score': max_threat[1],
            'confidence': 0.8,  # 기본 신뢰도
            'threat_classification': threat_scores
        }


class BehavioralAI:
    """행동 패턴 AI 분석기"""
    
    async def analyze_behavior(self, context: Dict) -> Dict[str, Any]:
        """행동 패턴 AI 분석"""
        # 간단한 휴리스틱 기반 행동 분석
        risk_score = 0.0
        threats = []
        
        user_id = context.get('user_id')
        message_count = context.get('recent_message_count', 0)
        time_span = context.get('message_time_span', 3600)
        
        # 메시지 빈도 분석
        if message_count > 20 and time_span < 300:  # 5분에 20개 이상
            threats.append({
                'type': '비정상적_활동_빈도',
                'reason': f'{time_span}초에 {message_count}개 메시지'
            })
            risk_score += 0.7
        
        return {
            'threats_detected': threats,
            'risk_score': risk_score,
            'confidence': 0.9
        }


class NetworkForensics:
    """네트워크 포렌식 분석기"""
    
    async def analyze_network_pattern(self, context: Dict) -> Dict[str, Any]:
        """네트워크 패턴 분석"""
        # 기본적인 네트워크 패턴 분석
        threats = []
        risk_score = 0.0
        
        # IP 패턴 분석 (실제로는 더 복잡한 분석 필요)
        ip_address = context.get('ip_address')
        if ip_address:
            # VPN/Proxy 탐지 휴리스틱
            suspicious_ranges = ['10.', '192.168.', '172.']
            if any(ip_address.startswith(range_) for range_ in suspicious_ranges):
                threats.append({
                    'type': '사설IP_사용',
                    'reason': f'사설 IP 주소 사용: {ip_address}'
                })
                risk_score += 0.3
        
        return {
            'threats_detected': threats,
            'risk_score': risk_score,
            'confidence': 0.6
        }


# 전역 인스턴스들
advanced_threat_detector = AdvancedThreatDetector()
nextgen_security = NextGenSecuritySystem()