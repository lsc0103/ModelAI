"""
Claude API客户端
处理与Claude API的所有交互，包括限流、重试、错误处理
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from loguru import logger
from anthropic import AsyncAnthropic
from anthropic.types import Message

from ..config.settings import settings


@dataclass
class ClaudeRequest:
    """Claude请求数据结构"""
    messages: List[Dict[str, str]]
    system: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    stream: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ClaudeResponse:
    """Claude响应数据结构"""
    content: str
    usage: Dict[str, int]
    model: str
    role: str = "assistant"
    metadata: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    processing_time: Optional[float] = None


class RateLimiter:
    """API调用频率限制器"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """获取调用许可"""
        async with self._lock:
            now = time.time()
            
            # 清理过期的请求记录
            self.requests = [
                req_time for req_time in self.requests 
                if now - req_time < self.window_seconds
            ]
            
            # 检查是否超过限制
            if len(self.requests) >= self.max_requests:
                wait_time = self.window_seconds - (now - self.requests[0])
                if wait_time > 0:
                    logger.warning(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    return await self.acquire()
            
            # 记录当前请求
            self.requests.append(now)


class RequestQueue:
    """请求队列管理器"""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_requests = 0
        self._lock = asyncio.Lock()
    
    @asynccontextmanager
    async def acquire_slot(self):
        """获取并发槽位"""
        async with self.semaphore:
            async with self._lock:
                self.active_requests += 1
            
            try:
                yield
            finally:
                async with self._lock:
                    self.active_requests -= 1
    
    def get_queue_status(self) -> Dict[str, int]:
        """获取队列状态"""
        return {
            "active_requests": self.active_requests,
            "max_concurrent": self.max_concurrent,
            "available_slots": self.max_concurrent - self.active_requests
        }


class ClaudeClient:
    """Claude API客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.claude_api_key
        if not self.api_key:
            raise ValueError("Claude API key is required")
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.rate_limiter = RateLimiter(
            max_requests=settings.request_rate_limit,
            window_seconds=60
        )
        self.request_queue = RequestQueue(
            max_concurrent=settings.max_concurrent_requests
        )
        
        # 统计信息
        self.total_requests = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.error_count = 0
        
        logger.info("Claude API client initialized")
    
    async def send_message(
        self,
        request: ClaudeRequest,
        agent_type: str = "default"
    ) -> ClaudeResponse:
        """发送消息到Claude"""
        
        start_time = time.time()
        request_id = f"{agent_type}_{int(start_time * 1000)}"
        
        logger.info(f"Sending request {request_id} for agent {agent_type}")
        
        try:
            # 应用频率限制
            await self.rate_limiter.acquire()
            
            # 获取并发槽位
            async with self.request_queue.acquire_slot():
                response = await self._make_request(request, agent_type)
                
                # 计算处理时间
                processing_time = time.time() - start_time
                response.processing_time = processing_time
                response.request_id = request_id
                
                # 更新统计
                self.total_requests += 1
                self.total_tokens_used += response.usage.get("total_tokens", 0)
                
                logger.info(
                    f"Request {request_id} completed in {processing_time:.2f}s, "
                    f"tokens: {response.usage.get('total_tokens', 0)}"
                )
                
                return response
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Request {request_id} failed: {str(e)}")
            raise
    
    async def _make_request(
        self,
        request: ClaudeRequest,
        agent_type: str
    ) -> ClaudeResponse:
        """执行实际的API请求"""
        
        # 获取Agent特定配置
        agent_config = settings.get_agent_config(agent_type)
        
        # 构建请求参数
        params = {
            "model": agent_config["model"],
            "max_tokens": request.max_tokens or agent_config["max_tokens"],
            "temperature": request.temperature or agent_config["temperature"],
            "messages": request.messages
        }
        
        if request.system:
            params["system"] = request.system
        
        # 带重试的请求执行
        for attempt in range(settings.retry_attempts):
            try:
                if request.stream:
                    return await self._stream_request(params, agent_type)
                else:
                    return await self._sync_request(params, agent_type)
            
            except Exception as e:
                if attempt == settings.retry_attempts - 1:
                    raise
                
                wait_time = settings.retry_delay * (2 ** attempt)
                logger.warning(
                    f"Request attempt {attempt + 1} failed: {str(e)}, "
                    f"retrying in {wait_time}s"
                )
                await asyncio.sleep(wait_time)
    
    async def _sync_request(
        self,
        params: Dict[str, Any],
        agent_type: str
    ) -> ClaudeResponse:
        """同步请求"""
        
        message = await self.client.messages.create(**params)
        
        return ClaudeResponse(
            content=message.content[0].text,
            usage={
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "total_tokens": message.usage.input_tokens + message.usage.output_tokens
            },
            model=message.model,
            role=message.role,
            metadata={"agent_type": agent_type}
        )
    
    async def _stream_request(
        self,
        params: Dict[str, Any],
        agent_type: str
    ) -> ClaudeResponse:
        """流式请求"""
        
        content_parts = []
        input_tokens = 0
        output_tokens = 0
        
        async with self.client.messages.stream(**params) as stream:
            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    content_parts.append(chunk.delta.text)
                elif chunk.type == "message_start":
                    input_tokens = chunk.message.usage.input_tokens
                elif chunk.type == "message_delta":
                    output_tokens = chunk.delta.usage.output_tokens
        
        return ClaudeResponse(
            content="".join(content_parts),
            usage={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            },
            model=params["model"],
            role="assistant",
            metadata={"agent_type": agent_type, "streamed": True}
        )
    
    async def send_multimodal_message(
        self,
        text: str,
        images: Optional[List[Path]] = None,
        documents: Optional[List[Path]] = None,
        agent_type: str = "master_coordinator"
    ) -> ClaudeResponse:
        """发送多模态消息"""
        
        # 构建消息内容
        message_content = []
        
        # 添加文本
        if text:
            message_content.append({
                "type": "text",
                "text": text
            })
        
        # 添加图片
        if images:
            for image_path in images:
                if image_path.exists():
                    with open(image_path, "rb") as f:
                        image_data = f.read()
                    
                    # 检测图片格式
                    import base64
                    image_b64 = base64.b64encode(image_data).decode()
                    
                    if image_path.suffix.lower() in ['.jpg', '.jpeg']:
                        media_type = "image/jpeg"
                    elif image_path.suffix.lower() == '.png':
                        media_type = "image/png"
                    elif image_path.suffix.lower() == '.webp':
                        media_type = "image/webp"
                    else:
                        logger.warning(f"Unsupported image format: {image_path}")
                        continue
                    
                    message_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64
                        }
                    })
        
        # 处理文档（转换为文本）
        if documents:
            for doc_path in documents:
                doc_text = await self._extract_document_text(doc_path)
                if doc_text:
                    message_content.append({
                        "type": "text",
                        "text": f"Document content from {doc_path.name}:\n\n{doc_text}"
                    })
        
        # 创建请求
        request = ClaudeRequest(
            messages=[{
                "role": "user",
                "content": message_content
            }],
            system=self._get_multimodal_system_prompt(),
            max_tokens=8192,
            temperature=0.5
        )
        
        return await self.send_message(request, agent_type)
    
    async def _extract_document_text(self, doc_path: Path) -> Optional[str]:
        """提取文档文本"""
        try:
            if doc_path.suffix.lower() == '.pdf':
                # PDF处理
                import PyPDF2
                with open(doc_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text.strip()
            
            elif doc_path.suffix.lower() in ['.docx', '.doc']:
                # Word文档处理
                from docx import Document
                doc = Document(doc_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text.strip()
            
            elif doc_path.suffix.lower() == '.txt':
                # 纯文本
                with open(doc_path, 'r', encoding='utf-8') as file:
                    return file.read().strip()
            
            else:
                logger.warning(f"Unsupported document format: {doc_path}")
                return None
        
        except Exception as e:
            logger.error(f"Failed to extract text from {doc_path}: {str(e)}")
            return None
    
    def _get_multimodal_system_prompt(self) -> str:
        """获取多模态系统提示"""
        return """
        你是ModelAI的主协调Agent，专门处理多模态输入的3D/2D模型生成需求。

        你需要分析用户提供的：
        1. 文本描述 - 详细的需求说明
        2. 参考图片 - 视觉风格和结构参考
        3. 文档内容 - 技术规格和详细要求

        处理优先级：图片 > 文档 > 文字

        如果发现输入之间有冲突，请：
        1. 明确指出冲突点
        2. 提供解决建议
        3. 请求用户确认最终方案

        输出必须是结构化的JSON格式，包含需求分析、Agent分配、技术规格等。
        """
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "error_count": self.error_count,
            "success_rate": (self.total_requests - self.error_count) / max(self.total_requests, 1),
            "queue_status": self.request_queue.get_queue_status(),
            "estimated_cost": self.total_tokens_used * 0.000003  # 粗略估算
        }
    
    async def test_connection(self) -> bool:
        """测试API连接"""
        try:
            request = ClaudeRequest(
                messages=[{
                    "role": "user", 
                    "content": "Hello, please respond with 'OK' to confirm the connection."
                }],
                max_tokens=10,
                temperature=0
            )
            
            response = await self.send_message(request, "test")
            return "OK" in response.content.upper()
        
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False


# 单例客户端实例
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """获取Claude客户端单例"""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client


# 便捷函数
async def send_claude_message(
    messages: List[Dict[str, str]],
    agent_type: str = "default",
    system: Optional[str] = None,
    **kwargs
) -> ClaudeResponse:
    """便捷的消息发送函数"""
    client = get_claude_client()
    request = ClaudeRequest(
        messages=messages,
        system=system,
        **kwargs
    )
    return await client.send_message(request, agent_type)


async def send_multimodal_request(
    text: str,
    images: Optional[List[Path]] = None,
    documents: Optional[List[Path]] = None,
    agent_type: str = "master_coordinator"
) -> ClaudeResponse:
    """便捷的多模态请求函数"""
    client = get_claude_client()
    return await client.send_multimodal_message(text, images, documents, agent_type)