"""
混合AI客户端
支持OpenAI和Claude API的统一调用接口
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from openai import AsyncOpenAI
import httpx
from loguru import logger

from .claude_client import ClaudeClient, ClaudeRequest, ClaudeResponse
from ..config.settings import settings


class AIService(str, Enum):
    """AI服务类型"""
    OPENAI = "openai"
    CLAUDE = "claude"


@dataclass
class AIRequest:
    """统一的AI请求格式"""
    messages: List[Dict[str, str]]
    system: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    service: Optional[AIService] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AIResponse:
    """统一的AI响应格式"""
    content: str
    service: AIService
    model: str
    usage: Dict[str, int]
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None


class OpenAIClient:
    """OpenAI API客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.total_requests = 0
        self.total_tokens = 0
        
        logger.info("OpenAI client initialized")
    
    async def send_message(self, request: AIRequest) -> AIResponse:
        """发送消息到OpenAI（带重试机制）"""
        start_time = time.time()
        
        # 构建OpenAI格式的消息
        messages = []
        
        # 添加系统消息
        if request.system:
            messages.append({"role": "system", "content": request.system})
        
        # 添加用户消息
        messages.extend(request.messages)
        
        # 重试逻辑
        last_error = None
        for attempt in range(settings.retry_attempts):
            try:
                # 调用OpenAI API
                response = await self.client.chat.completions.create(
                    model=settings.openai_model,
                    messages=messages,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    timeout=settings.openai_timeout
                )
                
                processing_time = time.time() - start_time
                
                # 更新统计
                self.total_requests += 1
                self.total_tokens += response.usage.total_tokens
                
                if attempt > 0:
                    logger.info(f"OpenAI request succeeded on attempt {attempt + 1}")
                
                return AIResponse(
                    content=response.choices[0].message.content,
                    service=AIService.OPENAI,
                    model=response.model,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    processing_time=processing_time,
                    metadata=request.metadata
                )
            
            except Exception as e:
                last_error = e
                logger.warning(f"OpenAI request failed on attempt {attempt + 1}/{settings.retry_attempts}: {str(e)}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < settings.retry_attempts - 1:
                    await asyncio.sleep(settings.retry_delay * (attempt + 1))  # 递增延迟
                    logger.info(f"Retrying OpenAI request in {settings.retry_delay * (attempt + 1)} seconds...")
        
        # 所有重试都失败
        logger.error(f"OpenAI request failed after {settings.retry_attempts} attempts: {str(last_error)}")
        raise last_error
    
    async def test_connection(self) -> bool:
        """测试OpenAI连接"""
        try:
            request = AIRequest(
                messages=[{"role": "user", "content": "Hello, please respond with 'OK'"}],
                max_tokens=10,
                temperature=0
            )
            response = await self.send_message(request)
            return "OK" in response.content.upper()
        except Exception:
            return False


class MultiAIClient:
    """多AI服务统一客户端"""
    
    def __init__(self):
        # 初始化各个AI客户端
        self.openai_client = None
        self.claude_client = None
        
        # 尝试初始化OpenAI客户端
        try:
            if settings.openai_api_key:
                self.openai_client = OpenAIClient()
                logger.info("OpenAI client ready")
        except Exception as e:
            logger.warning(f"OpenAI client initialization failed: {e}")
        
        # 尝试初始化Claude客户端
        try:
            if settings.claude_api_key:
                self.claude_client = ClaudeClient()
                logger.info("Claude client ready")
        except Exception as e:
            logger.warning(f"Claude client initialization failed: {e}")
        
        # 检查是否至少有一个可用的客户端
        if not self.openai_client and not self.claude_client:
            raise ValueError("No AI service available. Please configure at least one API key.")
        
        self.service_priority = self._determine_service_priority()
        logger.info(f"AI service priority: {self.service_priority}")
    
    def _determine_service_priority(self) -> List[AIService]:
        """确定AI服务优先级"""
        priority = []
        
        # 添加主要服务
        if settings.primary_ai_service == "openai" and self.openai_client:
            priority.append(AIService.OPENAI)
        elif settings.primary_ai_service == "claude" and self.claude_client:
            priority.append(AIService.CLAUDE)
        
        # 添加备选服务
        if settings.fallback_ai_service == "claude" and self.claude_client and AIService.CLAUDE not in priority:
            priority.append(AIService.CLAUDE)
        elif settings.fallback_ai_service == "openai" and self.openai_client and AIService.OPENAI not in priority:
            priority.append(AIService.OPENAI)
        
        # 如果配置的服务不可用，使用任何可用的服务
        if not priority:
            if self.openai_client:
                priority.append(AIService.OPENAI)
            if self.claude_client:
                priority.append(AIService.CLAUDE)
        
        return priority
    
    async def send_message(
        self, 
        request: AIRequest,
        agent_type: str = "default",
        preferred_service: Optional[AIService] = None
    ) -> AIResponse:
        """发送消息，支持服务选择和故障转移"""
        
        # 确定服务优先级
        services_to_try = []
        
        if preferred_service and self._is_service_available(preferred_service):
            services_to_try.append(preferred_service)
        
        # 添加默认优先级
        for service in self.service_priority:
            if service not in services_to_try:
                services_to_try.append(service)
        
        # 尝试各个服务
        last_error = None
        for service in services_to_try:
            try:
                logger.info(f"Trying {service.value} for agent {agent_type}")
                
                if service == AIService.OPENAI and self.openai_client:
                    return await self.openai_client.send_message(request)
                elif service == AIService.CLAUDE and self.claude_client:
                    # 转换为Claude格式
                    claude_request = ClaudeRequest(
                        messages=request.messages,
                        system=request.system,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        metadata=request.metadata
                    )
                    claude_response = await self.claude_client.send_message(claude_request, agent_type)
                    
                    # 转换为统一格式
                    return AIResponse(
                        content=claude_response.content,
                        service=AIService.CLAUDE,
                        model=claude_response.model,
                        usage=claude_response.usage,
                        processing_time=claude_response.processing_time or 0,
                        metadata=claude_response.metadata
                    )
            
            except Exception as e:
                last_error = e
                logger.warning(f"{service.value} failed: {str(e)}")
                continue
        
        # 所有服务都失败
        raise Exception(f"All AI services failed. Last error: {last_error}")
    
    def _is_service_available(self, service: AIService) -> bool:
        """检查服务是否可用"""
        if service == AIService.OPENAI:
            return self.openai_client is not None
        elif service == AIService.CLAUDE:
            return self.claude_client is not None
        return False
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """测试所有AI服务连接"""
        results = {}
        
        if self.openai_client:
            results["openai"] = await self.openai_client.test_connection()
        
        if self.claude_client:
            results["claude"] = await self.claude_client.test_connection()
        
        return results
    
    def get_available_services(self) -> List[AIService]:
        """获取可用的AI服务列表"""
        services = []
        if self.openai_client:
            services.append(AIService.OPENAI)
        if self.claude_client:
            services.append(AIService.CLAUDE)
        return services
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取所有服务的统计信息"""
        stats = {
            "available_services": [s.value for s in self.get_available_services()],
            "service_priority": [s.value for s in self.service_priority]
        }
        
        if self.openai_client:
            stats["openai"] = {
                "total_requests": self.openai_client.total_requests,
                "total_tokens": self.openai_client.total_tokens,
                "estimated_cost": self.openai_client.total_tokens * 0.00001  # 粗略估算
            }
        
        if self.claude_client:
            stats["claude"] = self.claude_client.get_statistics()
        
        return stats
    
    def get_optimal_service_for_agent(self, agent_type: str) -> AIService:
        """根据Agent类型返回最优的AI服务"""
        
        # Agent特定的服务选择策略
        service_preferences = {
            "master_coordinator": AIService.OPENAI,  # GPT-4推理能力强
            "geometry_agent": AIService.OPENAI,      # 数学和几何计算
            "material_agent": AIService.CLAUDE,      # 创意和艺术感
            "detail_agent": AIService.CLAUDE,        # 细节描述能力
            "rigging_agent": AIService.OPENAI,       # 技术精确性
            "integration_agent": AIService.OPENAI    # 逻辑整合
        }
        
        preferred_service = service_preferences.get(agent_type)
        
        # 检查首选服务是否可用
        if preferred_service and self._is_service_available(preferred_service):
            return preferred_service
        
        # 返回默认优先级中的第一个
        return self.service_priority[0] if self.service_priority else AIService.OPENAI


# 全局多AI客户端实例
_multi_ai_client: Optional[MultiAIClient] = None


def get_multi_ai_client() -> MultiAIClient:
    """获取多AI客户端单例"""
    global _multi_ai_client
    if _multi_ai_client is None:
        _multi_ai_client = MultiAIClient()
    return _multi_ai_client