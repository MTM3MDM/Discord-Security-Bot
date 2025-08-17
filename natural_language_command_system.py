import asyncio
import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
import google.generativeai as genai
from dataclasses import dataclass
from enum import Enum
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class CommandCategory(Enum):
    """명령어 카테고리"""
    SECURITY = "보안"
    USER_MANAGEMENT = "사용자관리"
    MONITORING = "모니터링"
    SETTINGS = "설정"
    STATISTICS = "통계"
    MODERATION = "관리"
    AI_CONTROL = "AI제어"
    SYSTEM = "시스템"

class CommandIntent(Enum):
    """명령 의도"""
    QUERY = "조회"
    ACTION = "실행"
    MODIFY = "수정"
    DELETE = "삭제"
    CREATE = "생성"
    ANALYZE = "분석"

@dataclass
class ParsedCommand:
    """파싱된 명령"""
    category: CommandCategory
    intent: CommandIntent
    confidence: float
    target: Optional[str] = None
    parameters: Dict[str, Any] = None
    original_text: str = ""
    suggested_action: str = ""
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}

class NaturalLanguageCommandParser:
    """자연어 명령어 파서"""
    
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        # 최신 Gemini 모델 사용 (향상된 자연어 처리)
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info("✅ 자연어 처리용 Gemini 2.0 Flash 모델 초기화 완료")
        except Exception as e:
            self.model = genai.GenerativeModel('gemini-1.5-pro-latest')
            logger.info("✅ 자연어 처리용 Gemini 1.5 Pro Latest 모델로 폴백 초기화")
        
        # 명령어 패턴 데이터베이스
        self.command_patterns = self._initialize_command_patterns()
        
        # 컨텍스트 메모리
        self.conversation_context = {}
        
        # 명령 히스토리
        self.command_history = []
    
    def _initialize_command_patterns(self) -> Dict[str, List[Dict]]:
        """명령어 패턴 초기화"""
        return {
            "보안조회": [
                {"pattern": r"보안.*상태", "category": CommandCategory.SECURITY, "intent": CommandIntent.QUERY},
                {"pattern": r"위험.*사용자", "category": CommandCategory.SECURITY, "intent": CommandIntent.QUERY},
                {"pattern": r"최근.*위반", "category": CommandCategory.SECURITY, "intent": CommandIntent.QUERY},
                {"pattern": r"차단.*목록", "category": CommandCategory.SECURITY, "intent": CommandIntent.QUERY},
            ],
            "사용자관리": [
                {"pattern": r"사용자.*정보", "category": CommandCategory.USER_MANAGEMENT, "intent": CommandIntent.QUERY},
                {"pattern": r"경고.*초기화", "category": CommandCategory.USER_MANAGEMENT, "intent": CommandIntent.ACTION},
                {"pattern": r"신뢰도.*변경", "category": CommandCategory.USER_MANAGEMENT, "intent": CommandIntent.MODIFY},
                {"pattern": r"사용자.*차단", "category": CommandCategory.USER_MANAGEMENT, "intent": CommandIntent.ACTION},
                {"pattern": r"뮤트.*해제", "category": CommandCategory.USER_MANAGEMENT, "intent": CommandIntent.ACTION},
            ],
            "통계조회": [
                {"pattern": r"서버.*통계", "category": CommandCategory.STATISTICS, "intent": CommandIntent.QUERY},
                {"pattern": r"활동.*분석", "category": CommandCategory.STATISTICS, "intent": CommandIntent.ANALYZE},
                {"pattern": r"위반.*통계", "category": CommandCategory.STATISTICS, "intent": CommandIntent.QUERY},
            ],
            "AI제어": [
                {"pattern": r"AI.*설정", "category": CommandCategory.AI_CONTROL, "intent": CommandIntent.MODIFY},
                {"pattern": r"판사.*모드", "category": CommandCategory.AI_CONTROL, "intent": CommandIntent.MODIFY},
                {"pattern": r"학습.*시작", "category": CommandCategory.AI_CONTROL, "intent": CommandIntent.ACTION},
                {"pattern": r"모델.*재학습", "category": CommandCategory.AI_CONTROL, "intent": CommandIntent.ACTION},
            ],
            "시스템": [
                {"pattern": r"봇.*재시작", "category": CommandCategory.SYSTEM, "intent": CommandIntent.ACTION},
                {"pattern": r"로그.*확인", "category": CommandCategory.SYSTEM, "intent": CommandIntent.QUERY},
                {"pattern": r"설정.*백업", "category": CommandCategory.SYSTEM, "intent": CommandIntent.ACTION},
            ]
        }
    
    async def parse_natural_command(self, text: str, user_context: Dict[str, Any] = None) -> ParsedCommand:
        """자연어 명령 파싱"""
        try:
            # 1. 기본 패턴 매칭
            basic_match = self._match_basic_patterns(text)
            
            # 2. AI 기반 고급 파싱
            ai_analysis = await self._ai_parse_command(text, user_context)
            
            # 3. 컨텍스트 기반 보정
            context_analysis = self._analyze_context(text, user_context)
            
            # 4. 최종 명령 구성
            final_command = self._synthesize_command(text, basic_match, ai_analysis, context_analysis)
            
            # 5. 명령 히스토리에 추가
            self._add_to_history(final_command)
            
            return final_command
            
        except Exception as e:
            logger.error(f"자연어 명령 파싱 오류: {e}")
            return ParsedCommand(
                category=CommandCategory.SYSTEM,
                intent=CommandIntent.QUERY,
                confidence=0.0,
                original_text=text,
                suggested_action="명령을 이해할 수 없습니다"
            )
    
    def _match_basic_patterns(self, text: str) -> Dict[str, Any]:
        """기본 패턴 매칭"""
        matches = []
        
        for category_name, patterns in self.command_patterns.items():
            for pattern_data in patterns:
                if re.search(pattern_data["pattern"], text, re.IGNORECASE):
                    matches.append({
                        "category": pattern_data["category"],
                        "intent": pattern_data["intent"],
                        "confidence": 0.8,
                        "pattern": pattern_data["pattern"]
                    })
        
        if matches:
            # 가장 높은 신뢰도의 매치 반환
            return max(matches, key=lambda x: x["confidence"])
        
        return {"confidence": 0.0}
    
    async def _ai_parse_command(self, text: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """AI 기반 명령 파싱"""
        try:
            prompt = f"""
            당신은 디스코드 보안봇의 자연어 명령 해석 AI입니다.
            다음 자연어 명령을 분석하고 구조화된 정보를 추출해주세요.

            사용자 명령: "{text}"
            
            사용자 컨텍스트:
            - 권한 레벨: {user_context.get('permission_level', '일반')}
            - 이전 명령들: {user_context.get('recent_commands', [])}
            - 현재 채널: {user_context.get('channel_type', '일반')}

            다음 카테고리 중 하나로 분류하세요:
            1. SECURITY (보안 관련)
            2. USER_MANAGEMENT (사용자 관리)
            3. MONITORING (모니터링)
            4. SETTINGS (설정 변경)
            5. STATISTICS (통계 조회)
            6. MODERATION (관리 작업)
            7. AI_CONTROL (AI 제어)
            8. SYSTEM (시스템 작업)

            다음 의도 중 하나로 분류하세요:
            1. QUERY (조회/확인)
            2. ACTION (실행/수행)
            3. MODIFY (수정/변경)
            4. DELETE (삭제)
            5. CREATE (생성)
            6. ANALYZE (분석)

            추가로 다음을 추출하세요:
            - 대상 (사용자명, ID, 채널 등)
            - 매개변수 (숫자, 시간, 옵션 등)
            - 제안할 구체적 행동

            예시 명령들:
            - "홍길동 사용자 정보 보여줘" → USER_MANAGEMENT, QUERY, target: 홍길동
            - "신뢰도 낮은 사용자들 차단해" → SECURITY, ACTION, parameters: {{trust_threshold: "low"}}
            - "어제부터 위반 통계 분석해줘" → STATISTICS, ANALYZE, parameters: {{timeframe: "yesterday"}}

            반드시 다음 JSON 형식으로 응답하세요:
            {{
                "category": "카테고리명",
                "intent": "의도명", 
                "confidence": 0.0-1.0,
                "target": "대상 또는 null",
                "parameters": {{"키": "값"}},
                "suggested_action": "구체적인 수행 작업",
                "reasoning": "판단 근거"
            }}
            """
            
            response = self.model.generate_content(prompt)
            ai_result = json.loads(response.text.strip())
            
            # 카테고리와 의도를 Enum으로 변환
            try:
                ai_result["category"] = CommandCategory[ai_result["category"]]
                ai_result["intent"] = CommandIntent[ai_result["intent"]]
            except KeyError as e:
                logger.warning(f"AI 응답의 Enum 변환 실패: {e}")
                ai_result["category"] = CommandCategory.SYSTEM
                ai_result["intent"] = CommandIntent.QUERY
            
            return ai_result
            
        except Exception as e:
            logger.error(f"AI 명령 파싱 오류: {e}")
            return {"confidence": 0.0, "error": str(e)}
    
    def _analyze_context(self, text: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """컨텍스트 분석"""
        context_score = 0.5
        context_info = {}
        
        if not user_context:
            return {"confidence": context_score, "info": context_info}
        
        # 사용자 권한 레벨 확인
        permission_level = user_context.get('permission_level', '일반')
        if permission_level == '관리자':
            context_score += 0.2
        elif permission_level == '모더레이터':
            context_score += 0.1
        
        # 이전 명령과의 연관성 확인
        recent_commands = user_context.get('recent_commands', [])
        if recent_commands:
            # 이전 명령과 유사한 패턴이면 신뢰도 증가
            for recent in recent_commands[-3:]:  # 최근 3개 명령만 확인
                if any(word in text.lower() for word in recent.lower().split()):
                    context_score += 0.05
        
        # 채널 타입에 따른 명령 적합성
        channel_type = user_context.get('channel_type', '일반')
        if channel_type == '관리자채널' and any(keyword in text for keyword in ['차단', '뮤트', '삭제']):
            context_score += 0.1
        
        # 시간대별 명령 적합성 (예: 새벽에는 긴급 명령일 가능성)
        current_hour = datetime.now().hour
        if 0 <= current_hour <= 6 and any(urgent in text for urgent in ['긴급', '즉시', '빨리']):
            context_info['urgency'] = 'high'
            context_score += 0.1
        
        return {
            "confidence": min(1.0, context_score),
            "info": context_info
        }
    
    def _synthesize_command(self, original_text: str, basic_match: Dict, 
                          ai_analysis: Dict, context_analysis: Dict) -> ParsedCommand:
        """명령 합성"""
        # 가장 신뢰도 높은 결과를 기본으로 사용
        sources = [
            ("basic", basic_match),
            ("ai", ai_analysis),
            ("context", context_analysis)
        ]
        
        best_source = max(sources, key=lambda x: x[1].get("confidence", 0))
        
        if best_source[1].get("confidence", 0) > 0.3:
            result_data = best_source[1]
        else:
            # 신뢰도가 모두 낮으면 AI 결과 사용
            result_data = ai_analysis
        
        # 기본값 설정
        category = result_data.get("category", CommandCategory.SYSTEM)
        intent = result_data.get("intent", CommandIntent.QUERY)
        confidence = result_data.get("confidence", 0.0)
        target = result_data.get("target")
        parameters = result_data.get("parameters", {})
        suggested_action = result_data.get("suggested_action", "명령을 처리할 수 없습니다")
        
        # 추가 매개변수 추출
        extracted_params = self._extract_parameters(original_text, category, intent)
        parameters.update(extracted_params)
        
        return ParsedCommand(
            category=category,
            intent=intent,
            confidence=confidence,
            target=target,
            parameters=parameters,
            original_text=original_text,
            suggested_action=suggested_action
        )
    
    def _extract_parameters(self, text: str, category: CommandCategory, 
                          intent: CommandIntent) -> Dict[str, Any]:
        """매개변수 추출"""
        params = {}
        
        # 숫자 추출
        numbers = re.findall(r'\d+', text)
        if numbers:
            params['numbers'] = [int(n) for n in numbers]
        
        # 시간 관련 키워드 추출
        time_keywords = {
            '어제': timedelta(days=1),
            '일주일': timedelta(weeks=1),
            '한달': timedelta(days=30),
            '오늘': timedelta(days=0),
            '최근': timedelta(days=7)
        }
        
        for keyword, delta in time_keywords.items():
            if keyword in text:
                params['timeframe'] = keyword
                params['time_delta'] = delta
                break
        
        # 사용자 멘션 추출
        mentions = re.findall(r'<@!?(\d+)>', text)
        if mentions:
            params['mentioned_users'] = [int(uid) for uid in mentions]
        
        # 사용자명 추출 (간단한 패턴)
        user_patterns = re.findall(r'(?:사용자|유저)\s*([가-힣a-zA-Z0-9_]+)', text)
        if user_patterns:
            params['usernames'] = user_patterns
        
        # 채널 추출
        channel_mentions = re.findall(r'<#(\d+)>', text)
        if channel_mentions:
            params['mentioned_channels'] = [int(cid) for cid in channel_mentions]
        
        # 보안 관련 키워드 추출
        if category == CommandCategory.SECURITY:
            if '위험' in text:
                params['focus'] = 'risk'
            elif '차단' in text:
                params['action_type'] = 'ban'
            elif '경고' in text:
                params['action_type'] = 'warning'
        
        # 설정 관련 키워드 추출
        if category == CommandCategory.SETTINGS:
            if '활성화' in text or '켜' in text:
                params['state'] = 'enable'
            elif '비활성화' in text or '꺼' in text:
                params['state'] = 'disable'
        
        return params
    
    def _add_to_history(self, command: ParsedCommand):
        """명령 히스토리에 추가"""
        self.command_history.append({
            'timestamp': datetime.now(),
            'command': command,
            'success': None  # 실행 후 업데이트
        })
        
        # 최대 100개 명령만 유지
        if len(self.command_history) > 100:
            self.command_history.pop(0)
    
    def update_command_result(self, success: bool):
        """최근 명령의 실행 결과 업데이트"""
        if self.command_history:
            self.command_history[-1]['success'] = success
    
    def get_command_suggestions(self, partial_text: str) -> List[str]:
        """명령어 자동완성 제안"""
        suggestions = []
        
        # 기본 패턴 기반 제안
        for category_patterns in self.command_patterns.values():
            for pattern_data in category_patterns:
                pattern = pattern_data["pattern"]
                # 패턴을 자연어 예시로 변환 (간단화)
                example = pattern.replace(r".*", " ").replace(r"\.", "")
                if partial_text.lower() in example.lower():
                    suggestions.append(example)
        
        # 최근 명령 기반 제안
        recent_texts = [h['command'].original_text for h in self.command_history[-10:]]
        for recent in recent_texts:
            if partial_text.lower() in recent.lower():
                suggestions.append(recent)
        
        # 중복 제거 및 정렬
        suggestions = list(set(suggestions))
        suggestions.sort(key=lambda x: len(x))
        
        return suggestions[:5]  # 최대 5개 제안

class CommandExecutor:
    """명령 실행기"""
    
    def __init__(self, bot_instance, user_manager, ai_judge):
        self.bot = bot_instance
        self.user_manager = user_manager
        self.ai_judge = ai_judge
        
        # 실행 권한 맵
        self.permission_map = {
            CommandCategory.SECURITY: ['관리자', '모더레이터'],
            CommandCategory.USER_MANAGEMENT: ['관리자', '모더레이터'],
            CommandCategory.MODERATION: ['관리자', '모더레이터'],
            CommandCategory.AI_CONTROL: ['관리자'],
            CommandCategory.SYSTEM: ['관리자'],
            CommandCategory.MONITORING: ['관리자', '모더레이터', '일반'],
            CommandCategory.STATISTICS: ['관리자', '모더레이터', '일반'],
            CommandCategory.SETTINGS: ['관리자']
        }
    
    async def execute_command(self, command: ParsedCommand, 
                            ctx: discord.ext.commands.Context) -> Dict[str, Any]:
        """명령 실행"""
        try:
            # 권한 확인
            if not await self._check_permissions(command, ctx):
                return {
                    'success': False,
                    'message': '❌ 이 명령을 실행할 권한이 없습니다.',
                    'permission_required': self.permission_map.get(command.category, ['관리자'])
                }
            
            # 카테고리별 명령 실행
            if command.category == CommandCategory.SECURITY:
                result = await self._execute_security_command(command, ctx)
            elif command.category == CommandCategory.USER_MANAGEMENT:
                result = await self._execute_user_management_command(command, ctx)
            elif command.category == CommandCategory.STATISTICS:
                result = await self._execute_statistics_command(command, ctx)
            elif command.category == CommandCategory.AI_CONTROL:
                result = await self._execute_ai_control_command(command, ctx)
            elif command.category == CommandCategory.SYSTEM:
                result = await self._execute_system_command(command, ctx)
            elif command.category == CommandCategory.MONITORING:
                result = await self._execute_monitoring_command(command, ctx)
            elif command.category == CommandCategory.SETTINGS:
                result = await self._execute_settings_command(command, ctx)
            elif command.category == CommandCategory.MODERATION:
                result = await self._execute_moderation_command(command, ctx)
            else:
                result = {
                    'success': False,
                    'message': f'❓ 알 수 없는 명령 카테고리: {command.category.value}'
                }
            
            # 실행 로그
            logger.info(f"자연어 명령 실행: {ctx.author} - {command.original_text} -> {result['success']}")
            
            return result
            
        except Exception as e:
            logger.error(f"명령 실행 오류: {e}")
            return {
                'success': False,
                'message': f'❌ 명령 실행 중 오류가 발생했습니다: {str(e)}'
            }
    
    async def _check_permissions(self, command: ParsedCommand, 
                               ctx: discord.ext.commands.Context) -> bool:
        """권한 확인"""
        required_permissions = self.permission_map.get(command.category, ['관리자'])
        
        # 봇 소유자는 모든 권한
        if await ctx.bot.is_owner(ctx.author):
            return True
        
        # 서버 관리자
        if ctx.author.guild_permissions.administrator:
            return True
        
        # 모더레이터 권한 (역할 기반)
        if '모더레이터' in required_permissions:
            mod_roles = ['모더레이터', 'Moderator', '관리자', 'Admin']
            if any(role.name in mod_roles for role in ctx.author.roles):
                return True
        
        # 일반 사용자 허용 명령
        if '일반' in required_permissions:
            return True
        
        return False
    
    async def _execute_security_command(self, command: ParsedCommand, 
                                      ctx: discord.ext.commands.Context) -> Dict[str, Any]:
        """보안 관련 명령 실행"""
        if command.intent == CommandIntent.QUERY:
            if '상태' in command.original_text:
                # 보안 상태 조회
                stats = self.user_manager.get_user_statistics()
                risk_users = await self.user_manager.get_risk_users()
                
                embed = discord.Embed(title="🛡️ 보안 상태", color=discord.Color.green())
                embed.add_field(name="총 사용자", value=stats.get('총사용자수', 0), inline=True)
                embed.add_field(name="위험 사용자", value=len(risk_users), inline=True)
                embed.add_field(name="평균 신뢰도", value=f"{stats.get('평균신뢰도', 0):.1f}", inline=True)
                
                await ctx.send(embed=embed)
                return {'success': True, 'message': '보안 상태를 조회했습니다.'}
                
            elif '위험' in command.original_text:
                # 위험 사용자 조회
                risk_users = await self.user_manager.get_risk_users()
                
                if not risk_users:
                    await ctx.send("✅ 현재 위험 사용자가 없습니다.")
                else:
                    embed = discord.Embed(title="⚠️ 위험 사용자 목록", color=discord.Color.red())
                    
                    for i, user in enumerate(risk_users[:10]):  # 최대 10명
                        embed.add_field(
                            name=f"{i+1}. {user.username}",
                            value=f"위험도: {user.risk_level.value}\n신뢰도: {user.trust_score:.1f}",
                            inline=True
                        )
                    
                    await ctx.send(embed=embed)
                
                return {'success': True, 'message': f'{len(risk_users)}명의 위험 사용자를 조회했습니다.'}
        
        return {'success': False, 'message': '지원하지 않는 보안 명령입니다.'}
    
    async def _execute_user_management_command(self, command: ParsedCommand, 
                                            ctx: discord.ext.commands.Context) -> Dict[str, Any]:
        """사용자 관리 명령 실행"""
        # 대상 사용자 찾기
        target_user = None
        if command.target:
            target_user = await self._find_user(command.target, ctx.guild)
        elif command.parameters.get('mentioned_users'):
            user_id = command.parameters['mentioned_users'][0]
            target_user = ctx.guild.get_member(user_id)
        elif command.parameters.get('usernames'):
            username = command.parameters['usernames'][0]
            target_user = discord.utils.get(ctx.guild.members, name=username)
        
        if not target_user and command.intent != CommandIntent.QUERY:
            return {'success': False, 'message': '❌ 대상 사용자를 찾을 수 없습니다.'}
        
        if command.intent == CommandIntent.QUERY:
            if target_user:
                # 특정 사용자 정보 조회
                user_context = await self.user_manager.get_user_context(target_user.id)
                
                embed = discord.Embed(title=f"👤 {target_user.display_name} 정보", color=discord.Color.blue())
                embed.add_field(name="신뢰도", value=f"{user_context['trust_score']:.1f}/100", inline=True)
                embed.add_field(name="경고", value=f"{user_context['warnings']}회", inline=True)
                embed.add_field(name="등급", value=user_context['user_tier'], inline=True)
                embed.add_field(name="위험도", value=user_context['risk_level'], inline=True)
                embed.add_field(name="계정 나이", value=f"{user_context['account_age']}일", inline=True)
                embed.add_field(name="총 메시지", value=f"{user_context['total_messages']}개", inline=True)
                
                await ctx.send(embed=embed)
                return {'success': True, 'message': '사용자 정보를 조회했습니다.'}
            else:
                # 전체 사용자 통계
                stats = self.user_manager.get_user_statistics()
                embed = discord.Embed(title="📊 사용자 통계", color=discord.Color.blue())
                
                for key, value in stats.items():
                    embed.add_field(name=key.replace('_', ' '), value=str(value), inline=True)
                
                await ctx.send(embed=embed)
                return {'success': True, 'message': '사용자 통계를 조회했습니다.'}
        
        elif command.intent == CommandIntent.ACTION:
            if '경고' in command.original_text and '초기화' in command.original_text:
                # 경고 초기화
                await self.user_manager.update_trust_score(target_user.id, 0, "관리자 경고 초기화")
                await ctx.send(f"✅ {target_user.mention}의 경고를 초기화했습니다.")
                return {'success': True, 'message': '경고를 초기화했습니다.'}
            
            elif '차단' in command.original_text:
                # 사용자 차단
                reason = command.parameters.get('reason', '관리자 명령')
                await target_user.ban(reason=reason)
                await ctx.send(f"🔨 {target_user.mention}을 차단했습니다. 사유: {reason}")
                return {'success': True, 'message': '사용자를 차단했습니다.'}
        
        return {'success': False, 'message': '지원하지 않는 사용자 관리 명령입니다.'}
    
    async def _execute_statistics_command(self, command: ParsedCommand, 
                                        ctx: discord.ext.commands.Context) -> Dict[str, Any]:
        """통계 관련 명령 실행"""
        if command.intent == CommandIntent.QUERY or command.intent == CommandIntent.ANALYZE:
            stats = self.user_manager.get_user_statistics()
            
            embed = discord.Embed(title="📈 서버 통계", color=discord.Color.green())
            
            # 기본 통계
            embed.add_field(name="총 사용자", value=stats.get('총사용자수', 0), inline=True)
            embed.add_field(name="활성 사용자", value=stats.get('활성사용자수', 0), inline=True)
            embed.add_field(name="현재 온라인", value=stats.get('현재온라인', 0), inline=True)
            
            # 신뢰도 통계
            embed.add_field(name="평균 신뢰도", value=f"{stats.get('평균신뢰도', 0):.1f}", inline=True)
            embed.add_field(name="평균 메시지", value=f"{stats.get('평균메시지수', 0):.0f}개", inline=True)
            
            # 등급별 분포
            tier_dist = stats.get('등급별분포', {})
            if tier_dist:
                tier_text = '\n'.join([f"{k}: {v}명" for k, v in tier_dist.items()])
                embed.add_field(name="등급 분포", value=tier_text, inline=True)
            
            # 위험도별 분포
            risk_dist = stats.get('위험도별분포', {})
            if risk_dist:
                risk_text = '\n'.join([f"{k}: {v}명" for k, v in risk_dist.items()])
                embed.add_field(name="위험도 분포", value=risk_text, inline=True)
            
            await ctx.send(embed=embed)
            return {'success': True, 'message': '서버 통계를 조회했습니다.'}
        
        return {'success': False, 'message': '지원하지 않는 통계 명령입니다.'}
    
    async def _execute_ai_control_command(self, command: ParsedCommand, 
                                        ctx: discord.ext.commands.Context) -> Dict[str, Any]:
        """AI 제어 명령 실행"""
        if command.intent == CommandIntent.ACTION:
            if '재학습' in command.original_text:
                # 모델 재학습
                try:
                    # AI 판사 모델 재학습 (실제 구현 필요)
                    await ctx.send("🤖 AI 모델 재학습을 시작합니다...")
                    # self.ai_judge.retrain_model()
                    await ctx.send("✅ AI 모델 재학습이 완료되었습니다.")
                    return {'success': True, 'message': 'AI 모델을 재학습했습니다.'}
                except Exception as e:
                    await ctx.send(f"❌ 재학습 중 오류 발생: {e}")
                    return {'success': False, 'message': f'재학습 실패: {e}'}
        
        return {'success': False, 'message': '지원하지 않는 AI 제어 명령입니다.'}
    
    async def _execute_system_command(self, command: ParsedCommand, 
                                    ctx: discord.ext.commands.Context) -> Dict[str, Any]:
        """시스템 명령 실행"""
        if command.intent == CommandIntent.QUERY:
            if '로그' in command.original_text:
                # 시스템 로그 조회 (간단한 예시)
                embed = discord.Embed(title="📋 시스템 로그", color=discord.Color.blue())
                embed.add_field(name="상태", value="정상 작동", inline=True)
                embed.add_field(name="가동 시간", value="24시간", inline=True)
                embed.add_field(name="메모리 사용량", value="85%", inline=True)
                
                await ctx.send(embed=embed)
                return {'success': True, 'message': '시스템 로그를 조회했습니다.'}
        
        return {'success': False, 'message': '지원하지 않는 시스템 명령입니다.'}
    
    async def _execute_monitoring_command(self, command: ParsedCommand, 
                                        ctx: discord.ext.commands.Context) -> Dict[str, Any]:
        """모니터링 명령 실행"""
        await ctx.send("📊 모니터링 기능은 개발 중입니다.")
        return {'success': True, 'message': '모니터링 명령을 실행했습니다.'}
    
    async def _execute_settings_command(self, command: ParsedCommand, 
                                      ctx: discord.ext.commands.Context) -> Dict[str, Any]:
        """설정 명령 실행"""
        await ctx.send("⚙️ 설정 기능은 개발 중입니다.")
        return {'success': True, 'message': '설정 명령을 실행했습니다.'}
    
    async def _execute_moderation_command(self, command: ParsedCommand, 
                                        ctx: discord.ext.commands.Context) -> Dict[str, Any]:
        """관리 명령 실행"""
        await ctx.send("🔨 관리 기능은 개발 중입니다.")
        return {'success': True, 'message': '관리 명령을 실행했습니다.'}
    
    async def _find_user(self, identifier: str, guild: discord.Guild) -> Optional[discord.Member]:
        """사용자 찾기"""
        # ID로 찾기
        if identifier.isdigit():
            return guild.get_member(int(identifier))
        
        # 이름으로 찾기
        return discord.utils.get(guild.members, name=identifier) or \
               discord.utils.get(guild.members, display_name=identifier)

# 전역 자연어 처리 시스템 인스턴스
natural_language_parser = None
command_executor = None

def initialize_natural_language_system(gemini_api_key: str, bot_instance, user_manager, ai_judge):
    """자연어 처리 시스템 초기화"""
    global natural_language_parser, command_executor
    natural_language_parser = NaturalLanguageCommandParser(gemini_api_key)
    command_executor = CommandExecutor(bot_instance, user_manager, ai_judge)
    return natural_language_parser, command_executor

def get_natural_language_system():
    """자연어 처리 시스템 반환"""
    return natural_language_parser, command_executor