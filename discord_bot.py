import discord
from discord.ext import commands, tasks
import asyncio
import logging
import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sys
import os
from collections import defaultdict, deque

# 커스텀 모듈 임포트
from core_ai_system import initialize_ai_judge, get_ai_judge
from advanced_user_system import advanced_user_manager, UserTier, RiskLevel
from natural_language_command_system import initialize_natural_language_system, get_natural_language_system
from advanced_security_system import advanced_threat_detector

# 설정 - 환경변수에서 로드
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경변수에서 토큰 가져오기
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not DISCORD_TOKEN:
    print("❌ DISCORD_TOKEN 환경변수가 설정되지 않았습니다!")
    print("💡 .env 파일에 DISCORD_TOKEN=your_token_here 를 추가하세요")
    exit(1)

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY 환경변수가 설정되지 않았습니다!")
    print("💡 .env 파일에 GEMINI_API_KEY=your_api_key_here 를 추가하세요")
    exit(1)

# 로깅 설정 (서버 환경 최적화)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AdvancedSecurityBot:
    """AI 기반 Discord 보안봇 (서버 환경 최적화)"""
    
    def __init__(self):
        # 봇 설정
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        intents.voice_states = True
        
        self.bot = commands.Bot(
            command_prefix=['!', '봇아 ', '보안봇 '],
            intents=intents,
            help_command=None
        )
        
        # 시스템 컴포넌트
        self.ai_judge = None
        self.user_manager = advanced_user_manager
        self.natural_language_system = None
        
        # 메시지 분석을 위한 버퍼
        self.message_buffer = deque(maxlen=1000)
        
        # 성능 통계
        self.performance_stats = {
            'messages_processed': 0,
            'threats_detected': 0,
            'users_banned': 0,
            'timeouts_applied': 0,
            'warnings_issued': 0
        }
        
        # 레이드 탐지 시스템
        self.raid_detection = {
            'recent_joins': deque(maxlen=50),
            'join_threshold': 5,  # 1분 내 5명 이상
            'time_window': 60  # 1분
        }
        
        # 스팸 탐지 기록
        self.spam_tracking = defaultdict(lambda: {
            'message_times': deque(maxlen=20),
            'message_contents': deque(maxlen=10),
            'warnings': 0
        })
        
        # 자동 역할 관리
        self.auto_roles = {}
        
        # 이벤트 및 명령어 설정
        self.setup_bot_events()
        self.setup_bot_commands()
        
    async def initialize_systems(self):
        """시스템 컴포넌트 초기화"""
        try:
            logger.info("🚀 보안봇 시스템 초기화 중...")
            
            # AI 판사 시스템 초기화
            await initialize_ai_judge(GEMINI_API_KEY)
            self.ai_judge = get_ai_judge()
            logger.info("✅ AI 판사 시스템 초기화 완료")
            
            # 자연어 처리 시스템 초기화
            await initialize_natural_language_system(GEMINI_API_KEY)
            self.natural_language_system = get_natural_language_system()
            logger.info("✅ 자연어 처리 시스템 초기화 완료")
            
            # 정기 작업 시작
            self.start_background_tasks()
            
            logger.info("✅ 모든 시스템 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ 시스템 초기화 실패: {e}")
            raise
    
    def log_message(self, level: str, message: str):
        """로그 출력 (서버 환경 최적화)"""
        level_map = {
            "INFO": logger.info,
            "SUCCESS": logger.info,
            "WARNING": logger.warning,
            "ERROR": logger.error,
            "VIOLATION": logger.warning,
            "ACTION": logger.info,
            "COMMAND": logger.info
        }
        
        log_func = level_map.get(level, logger.info)
        log_func(f"{level}: {message}")
    
    async def safe_delete_message(self, message):
        """안전하게 메시지 삭제"""
        try:
            await message.delete()
            return True
        except discord.NotFound:
            return False
        except discord.Forbidden:
            logger.warning(f"메시지 삭제 권한 없음: {message.id}")
            return False
        except discord.HTTPException:
            logger.warning(f"메시지 삭제 API 오류: {message.id}")
            return False
        except Exception as e:
            logger.error(f"메시지 삭제 중 알 수 없는 오류: {e}")
            return False

    def setup_bot_events(self):
        """봇 이벤트 설정"""
        
        @self.bot.event
        async def on_ready():
            await self.initialize_systems()
            
            logger.info(f'🤖 {self.bot.user}가 {len(self.bot.guilds)}개 서버에서 준비되었습니다!')
            
            # 봇 상태 설정
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="서버 보안 모니터링 중 🛡️"
            )
            await self.bot.change_presence(activity=activity, status=discord.Status.online)
            
            # 시스템 준비 완료
            self.log_message("SUCCESS", f"봇이 {len(self.bot.guilds)}개 서버에서 활성화되었습니다!")
        
        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user or message.author.bot:
                return
            
            try:
                # 성능 통계 업데이트
                self.performance_stats['messages_processed'] += 1
                
                # 메시지 버퍼에 추가 (DM 안전 처리)
                self.message_buffer.append({
                    'content': message.content[:500],  # 메모리 절약
                    'author': message.author.id,
                    'channel': message.channel.id,
                    'guild': message.guild.id if message.guild else 0,  # DM은 0으로 처리
                    'timestamp': message.created_at,
                    'is_dm': message.guild is None
                })
                
                # DM 메시지 처리 (안전)
                if message.guild is None:
                    await self.handle_dm_message(message)
                    return
                
                # 파일 첨부 보안 검사
                if message.attachments:
                    for attachment in message.attachments:
                        try:
                            # 파일 크기 제한 (10MB)
                            if attachment.size > 10 * 1024 * 1024:
                                await self.safe_delete_message(message)
                                await message.channel.send(f"❌ {message.author.mention} 파일이 너무 큽니다. (최대 10MB)")
                                continue
                            
                            # 파일 분석 수행
                            file_analysis = await advanced_threat_detector.analyze_file_security(
                                attachment.filename, attachment.url
                            )
                            
                            if file_analysis.get('is_suspicious', False):
                                if file_analysis.get('image_threats', []):
                                    image_analysis = file_analysis['image_threats'][0]  # 첫 번째 이미지 분석 결과
                                    if image_analysis['threats_detected']:
                                        file_analysis['threats_detected'].extend(image_analysis['threats_detected'])
                                elif image_analysis['threats_detected']:
                                    file_analysis['threats_detected'].extend(image_analysis['threats_detected'])
                            
                            if file_analysis['should_block']:
                                await self.safe_delete_message(message)
                                embed = discord.Embed(
                                    title="🚫 위험한 파일 차단",
                                    description=f"업로드된 파일 `{attachment.filename}`이 보안 위협으로 판정되어 차단되었습니다.",
                                    color=0xFF0000
                                )
                                embed.add_field(
                                    name="탐지된 위협",
                                    value="\n".join([threat['reason'] for threat in file_analysis['threats_detected']])[:1000],
                                    inline=False
                                )
                                await message.channel.send(embed=embed, delete_after=10)
                                self.log_message("WARNING", f"위험한 파일 차단: {attachment.filename} by {message.author.name}")
                        except Exception as file_error:
                            logger.error(f"파일 보안 검사 오류: {file_error}")
                
                # 스팸 탐지
                if await self.detect_spam(message):
                    return
                
                # 인텔리전트 위협 분석 및 처벌
                asyncio.create_task(self.intelligent_threat_analysis_and_punishment(message))
                
            except Exception as e:
                logger.error(f"메시지 처리 오류: {e}")
        
        @self.bot.event
        async def on_member_join(member):
            """새 멤버 합류 시"""
            try:
                # 레이드 탐지
                current_time = time.time()
                self.raid_detection['recent_joins'].append(current_time)
                
                # 1분 내 가입자 수 체크
                recent_count = sum(1 for join_time in self.raid_detection['recent_joins'] 
                                 if current_time - join_time <= self.raid_detection['time_window'])
                
                if recent_count >= self.raid_detection['join_threshold']:
                    raid_result = await advanced_threat_detector.analyze_raid_pattern(
                        list(self.raid_detection['recent_joins'])
                    )
                    if raid_result['is_raid']:
                        self.log_message("WARNING", f"레이드 공격 탐지: {raid_result['recent_joins_count']}명 빠른 가입")
                    
                    # 레이드 감지 시 엄격한 모드 활성화
                    # TODO: 임시 승인 시스템 또는 슬로우 모드 활성화
                
                # 새 멤버 계정 분석
                account_age = (datetime.now() - member.created_at).days
                if account_age < 7:  # 7일 미만 계정
                    suspicious_factors = []
                    
                    if account_age < 1:
                        suspicious_factors.append("매우 새로운 계정")
                    if not member.avatar:
                        suspicious_factors.append("기본 아바타")
                    if len(member.name) < 3:
                        suspicious_factors.append("짧은 사용자명")
                        
                    if len(suspicious_factors) >= 2:
                        self.log_message("WARNING", f"의심스러운 신규 멤버: {member.name}")
                
                self.log_message("INFO", f"새 멤버 가입: {member.name} ({member.id})")
                
            except Exception as e:
                logger.error(f"멤버 가입 처리 오류: {e}")
        
        @self.bot.event
        async def on_member_remove(member):
            """멤버 퇴장 시"""
            self.log_message("INFO", f"멤버 퇴장: {member.name} ({member.id})")
    
    def setup_bot_commands(self):
        """봇 명령어 설정"""
        
        @self.bot.command(name='상태', aliases=['status'])
        async def status_command(ctx):
            """봇 상태 확인"""
            try:
                uptime = time.time() - getattr(self, '_start_time', time.time())
                uptime_str = str(timedelta(seconds=int(uptime)))
                
                embed = discord.Embed(
                    title="🤖 보안봇 상태",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📊 기본 정보",
                    value=f"🔹 가동시간: {uptime_str}\n🔹 서버 수: {len(self.bot.guilds)}\n🔹 지연시간: {round(self.bot.latency * 1000)}ms",
                    inline=False
                )
                
                embed.add_field(
                    name="📈 처리 통계",
                    value=f"🔹 처리한 메시지: {self.performance_stats['messages_processed']:,}\n🔹 탐지한 위협: {self.performance_stats['threats_detected']:,}\n🔹 적용한 제재: {self.performance_stats['users_banned'] + self.performance_stats['timeouts_applied']:,}",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 상태 확인 중 오류가 발생했습니다: {str(e)}")

    async def detect_spam(self, message):
        """스팸 메시지 탐지"""
        try:
            user_id = message.author.id
            current_time = time.time()
            
            # 사용자별 메시지 기록 업데이트
            user_tracking = self.spam_tracking[user_id]
            user_tracking['message_times'].append(current_time)
            user_tracking['message_contents'].append(message.content[:100])
            
            # 스팸 탐지 로직
            recent_messages = [t for t in user_tracking['message_times'] if current_time - t <= 30]
            
            if len(recent_messages) >= 8:  # 30초에 8개 이상 메시지
                await self.safe_delete_message(message)
                await message.channel.send(f"⚠️ {message.author.mention} 스팸으로 판정되었습니다. 잠시 후 다시 시도하세요.", delete_after=5)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"스팸 탐지 오류: {e}")
            return False

    async def intelligent_threat_analysis_and_punishment(self, message):
        """지능형 위협 분석 및 처벌 시스템"""
        try:
            if message.guild is None:
                return  # DM은 처리하지 않음
            
            user = message.author
            content = message.content
            
            # 1단계: 고급 보안 스캔
            security_result = await advanced_threat_detector.analyze_message_security(
                content, user.id, message.channel.id
            )
            
            # 2단계: AI 판사 분석 (필요시)
            ai_judgment = None
            if self.ai_judge and (security_result['threats_detected'] or self._should_analyze_message(message)):
                user_context = await self.user_manager.get_user_context(user.id)
                guild_context = {
                    'strictness': '높음',
                    'recent_violations': '보통',
                    'server_type': '보안중시',
                    'special_notes': '자동처벌활성화'
                }
                ai_judgment = await self.ai_judge.comprehensive_judgment(content, user_context, guild_context)
            
            # 3단계: 통합 판단 및 처벌 결정
            final_decision = await self._make_final_punishment_decision(
                message, security_result, ai_judgment
            )
            
            # 4단계: 정확한 처벌 실행
            if final_decision['should_punish']:
                await self._execute_smart_punishment(message, final_decision)
                
        except Exception as e:
            logger.error(f"통합 위협 분석 오류: {e}")

    def _should_analyze_message(self, message):
        """메시지가 AI 분석이 필요한지 판단"""
        content = message.content.lower()
        
        # AI 분석이 필요한 패턴들
        ai_analysis_triggers = [
            '명령', '지시', '시스템', '관리자', '권한',
            '토큰', '비밀번호', '로그인', '계정',
            '돈', '투자', '수익', '무료', '이벤트'
        ]
        
        return any(trigger in content for trigger in ai_analysis_triggers)

    async def _make_final_punishment_decision(self, message, security_result, ai_judgment):
        """보안 스캔과 AI 판단을 종합해서 최종 처벌 결정"""
        user = message.author
        
        # 사용자 이력 확인
        user_profile = await self.user_manager.get_or_create_user_profile(
            user.id, user.name, message.guild.id if message.guild else 0
        )
        user_violations = user_profile.total_violations
        
        # 기본 결정 구조
        decision = {
            'should_punish': False,
            'punishment_type': 'none',
            'duration': 0,
            'reason': '',
            'confidence': 0.0,
            'delete_message': False,
            'notify_admins': False
        }
        
        # 보안 위험도가 높은 경우
        if security_result['should_block']:
            decision.update({
                'should_punish': True,
                'punishment_type': 'timeout',
                'duration': 60,  # 1시간
                'reason': f'보안 위협 탐지: {security_result["threats_detected"][0]["type"]}',
                'confidence': 0.9,
                'delete_message': True
            })
        
        # AI 판단 반영
        if ai_judgment and ai_judgment.get('action_required'):
            if ai_judgment['recommended_action'] == 'ban':
                decision.update({
                    'should_punish': True,
                    'punishment_type': 'ban',
                    'reason': f'AI 판단: {ai_judgment["reason"]}',
                    'confidence': ai_judgment['confidence'],
                    'delete_message': True,
                    'notify_admins': True
                })
        
        # 누적 위반 고려
        if user_violations >= 3 and decision['punishment_type'] in ['warning', 'timeout']:
            decision['punishment_type'] = 'ban'
            decision['reason'] += f' (누적 위반: {user_violations + 1}회)'
            decision['notify_admins'] = True
        
        return decision

    async def _execute_smart_punishment(self, message, decision):
        """정확한 처벌 실행"""
        user = message.author
        punishment_type = decision['punishment_type']
        guild = message.guild
        
        try:
            # 메시지 삭제
            if decision['delete_message']:
                await self.safe_delete_message(message)
            
            # 처벌 실행
            if punishment_type == 'ban':
                await guild.ban(
                    user,
                    reason=decision['reason'],
                    delete_message_days=1
                )
                self.performance_stats['users_banned'] += 1
                self.log_message("ACTION", f"사용자 차단: {user} - {decision['reason']}")
                
            elif punishment_type == 'timeout':
                timeout_duration = timedelta(minutes=decision['duration'])
                await user.timeout(
                    timeout_duration,
                    reason=decision['reason']
                )
                self.performance_stats['timeouts_applied'] += 1
                self.log_message("ACTION", f"타임아웃 적용: {user} - {decision['duration']}분 - {decision['reason']}")
            
            # 사용자 기록 업데이트
            user_profile = await self.user_manager.get_or_create_user_profile(
                user.id, user.name, guild.id
            )
            user_profile.total_violations += 1
            if punishment_type == 'ban':
                user_profile.ban_count += 1
            elif punishment_type == 'timeout':
                user_profile.timeout_count += 1
            else:
                user_profile.total_warnings += 1
            
            await self.user_manager.save_user_profile(user_profile)
            
        except Exception as e:
            logger.error(f"처벌 실행 오류: {e}")

    async def handle_dm_message(self, message):
        """DM 메시지 안전 처리"""
        try:
            # DM에서는 보안 분석만 수행하고 응답하지 않음
            await asyncio.sleep(0.1)  # 비동기 처리 시뮬레이션
            
        except Exception as e:
            logger.error(f"DM 처리 오류: {e}")

    def start_background_tasks(self):
        """백그라운드 작업 시작"""
        try:
            # 주기적 작업들 시작
            self.periodic_cleanup.start()
            self.threat_intelligence_update.start()
            self.performance_monitor.start()
            
        except Exception as e:
            logger.error(f"백그라운드 작업 시작 오류: {e}")

    @tasks.loop(hours=1)
    async def periodic_cleanup(self):
        """주기적 정리 작업"""
        try:
            # 오래된 메시지 버퍼 정리
            current_time = datetime.now()
            self.message_buffer = deque([
                msg for msg in self.message_buffer
                if (current_time - msg['timestamp']).total_seconds() < 3600  # 1시간
            ], maxlen=1000)
            
            # 스팸 추적 정리
            for user_id in list(self.spam_tracking.keys()):
                user_data = self.spam_tracking[user_id]
                user_data['message_times'] = deque([
                    t for t in user_data['message_times']
                    if time.time() - t < 300  # 5분
                ], maxlen=20)
                
                if not user_data['message_times']:
                    del self.spam_tracking[user_id]
                    
        except Exception as e:
            logger.error(f"정리 작업 오류: {e}")

    @tasks.loop(hours=6)
    async def threat_intelligence_update(self):
        """위협 인텔리전스 업데이트"""
        try:
            logger.info("위협 인텔리전스 업데이트 시작...")
            
            # 고급 보안 시스템 업데이트
            await advanced_threat_detector.update_threat_intelligence()
            
            # 보안 통계 로깅
            stats = advanced_threat_detector.get_threat_statistics()
            logger.info(f"보안 통계: {stats}")
            
        except Exception as e:
            logger.error(f"위협 인텔리전스 업데이트 오류: {e}")

    @tasks.loop(minutes=30)
    async def performance_monitor(self):
        """성능 모니터링"""
        try:
            # 메모리 사용량 체크
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > 500:  # 500MB 초과시 경고
                logger.warning(f"높은 메모리 사용량: {memory_mb:.1f}MB")
            
            # 통계 출력
            logger.info(f"성능 통계 - 메시지: {self.performance_stats['messages_processed']}, "
                       f"위협: {self.performance_stats['threats_detected']}, "
                       f"메모리: {memory_mb:.1f}MB")
                       
        except Exception as e:
            logger.error(f"성능 모니터링 오류: {e}")

    async def start_bot(self):
        """봇 시작"""
        self._start_time = time.time()
        
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            retry_count += 1
            try:
                await self.bot.start(DISCORD_TOKEN)
                break
            except Exception as e:
                logger.error(f"봇 시작 오류 (시도 {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    await asyncio.sleep(5 * retry_count)  # 점진적 대기
                    logger.info(f"{5 * retry_count}초 후 재시도...")
                else:
                    logger.error("모든 재시도 실패 - 봇 시작 중단")
                    raise

async def main():
    """서버용 메인 함수"""
    try:
        print("🚀 Discord 보안봇 시작 중...")
        
        bot = AdvancedSecurityBot()
        await bot.start_bot()
        
    except KeyboardInterrupt:
        print("\n⏹️ 봇이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 봇 실행 오류: {e}")
        logger.error(f"봇 실행 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())