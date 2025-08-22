"""
Agent基础框架
定义所有Agent的通用接口和行为
"""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime

from loguru import logger

from ..api.claude_client import ClaudeClient, ClaudeRequest, ClaudeResponse
from ..config.settings import AgentConfig


class AgentStatus(str, Enum):
    """Agent状态"""
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    ERROR = "error"
    PAUSED = "paused"


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentTask:
    """Agent任务数据结构"""
    task_id: str
    task_type: str
    description: str
    input_data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class AgentResult:
    """Agent结果数据结构"""
    task_id: str
    agent_id: str
    result_type: str
    output_data: Dict[str, Any]
    success: bool = True
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    quality_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class BaseAgent(ABC):
    """Agent基础类"""
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        claude_client: Optional[ClaudeClient] = None
    ):
        self.agent_id = agent_id or f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
        self.agent_type = agent_type or self.__class__.__name__.lower().replace("agent", "")
        self.claude_client = claude_client or ClaudeClient()
        
        # Agent状态
        self.status = AgentStatus.IDLE
        self.current_task: Optional[AgentTask] = None
        self.task_queue: List[AgentTask] = []
        self.results_history: List[AgentResult] = []
        
        # 性能统计
        self.total_tasks_completed = 0
        self.total_processing_time = 0.0
        self.success_rate = 1.0
        self.average_quality_score = 0.0
        
        # 配置
        self.system_prompt = self._get_system_prompt()
        self.capabilities = self._get_capabilities()
        
        logger.info(f"Agent {self.agent_id} ({self.agent_type}) initialized")
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """获取Agent的系统提示"""
        pass
    
    @abstractmethod
    def _get_capabilities(self) -> List[str]:
        """获取Agent的能力列表"""
        pass
    
    @abstractmethod
    async def _process_task(self, task: AgentTask) -> AgentResult:
        """处理具体任务（子类实现）"""
        pass
    
    async def add_task(self, task: AgentTask) -> bool:
        """添加任务到队列"""
        try:
            # 检查依赖是否满足
            if not await self._check_dependencies(task):
                logger.warning(f"Task {task.task_id} dependencies not satisfied")
                return False
            
            # 按优先级插入队列
            self._insert_task_by_priority(task)
            
            logger.info(
                f"Task {task.task_id} added to agent {self.agent_id} queue "
                f"(priority: {task.priority}, queue size: {len(self.task_queue)})"
            )
            
            # 如果Agent空闲，立即开始处理
            if self.status == AgentStatus.IDLE and not self.current_task:
                asyncio.create_task(self._process_next_task())
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to add task {task.task_id}: {str(e)}")
            return False
    
    def _insert_task_by_priority(self, task: AgentTask):
        """按优先级插入任务"""
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        
        task_priority = priority_order[task.priority]
        
        # 找到合适的插入位置
        insert_index = len(self.task_queue)
        for i, queued_task in enumerate(self.task_queue):
            if priority_order[queued_task.priority] > task_priority:
                insert_index = i
                break
        
        self.task_queue.insert(insert_index, task)
    
    async def _check_dependencies(self, task: AgentTask) -> bool:
        """检查任务依赖"""
        if not task.dependencies:
            return True
        
        # 检查依赖的任务是否已完成
        completed_tasks = {result.task_id for result in self.results_history if result.success}
        
        for dependency in task.dependencies:
            if dependency not in completed_tasks:
                return False
        
        return True
    
    async def _process_next_task(self):
        """处理下一个任务"""
        if not self.task_queue or self.status != AgentStatus.IDLE:
            return
        
        # 获取下一个任务
        task = self.task_queue.pop(0)
        self.current_task = task
        self.status = AgentStatus.WORKING
        
        logger.info(f"Agent {self.agent_id} started processing task {task.task_id}")
        
        try:
            # 处理任务
            start_time = asyncio.get_event_loop().time()
            result = await self._process_task(task)
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # 更新结果
            result.processing_time = processing_time
            result.agent_id = self.agent_id
            
            # 保存结果
            self.results_history.append(result)
            
            # 更新统计
            self._update_statistics(result)
            
            logger.info(
                f"Agent {self.agent_id} completed task {task.task_id} "
                f"in {processing_time:.2f}s (success: {result.success})"
            )
        
        except Exception as e:
            # 创建错误结果
            error_result = AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                result_type="error",
                output_data={},
                success=False,
                error_message=str(e)
            )
            
            self.results_history.append(error_result)
            logger.error(f"Agent {self.agent_id} failed to process task {task.task_id}: {str(e)}")
        
        finally:
            # 重置状态
            self.current_task = None
            self.status = AgentStatus.IDLE
            
            # 处理下一个任务
            if self.task_queue:
                asyncio.create_task(self._process_next_task())
    
    def _update_statistics(self, result: AgentResult):
        """更新统计信息"""
        self.total_tasks_completed += 1
        
        if result.processing_time:
            self.total_processing_time += result.processing_time
        
        # 更新成功率
        successful_tasks = sum(1 for r in self.results_history if r.success)
        self.success_rate = successful_tasks / len(self.results_history)
        
        # 更新平均质量分数
        quality_scores = [r.quality_score for r in self.results_history if r.quality_score is not None]
        if quality_scores:
            self.average_quality_score = sum(quality_scores) / len(quality_scores)
    
    async def send_claude_request(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> ClaudeResponse:
        """发送Claude请求"""
        request = ClaudeRequest(
            messages=messages,
            system=system or self.system_prompt,
            **kwargs
        )
        
        return await self.claude_client.send_message(request, self.agent_type)
    
    async def analyze_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析输入数据"""
        messages = [
            {
                "role": "user",
                "content": f"Please analyze the following input data for {self.agent_type} processing:\n\n{json.dumps(input_data, indent=2)}"
            }
        ]
        
        response = await self.send_claude_request(messages)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"analysis": response.content, "structured": False}
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "current_task": self.current_task.task_id if self.current_task else None,
            "queue_size": len(self.task_queue),
            "capabilities": self.capabilities,
            "statistics": {
                "total_tasks_completed": self.total_tasks_completed,
                "success_rate": self.success_rate,
                "average_processing_time": (
                    self.total_processing_time / max(self.total_tasks_completed, 1)
                ),
                "average_quality_score": self.average_quality_score
            }
        }
    
    def get_result(self, task_id: str) -> Optional[AgentResult]:
        """获取指定任务的结果"""
        for result in self.results_history:
            if result.task_id == task_id:
                return result
        return None
    
    def get_recent_results(self, limit: int = 10) -> List[AgentResult]:
        """获取最近的结果"""
        return self.results_history[-limit:]
    
    async def pause(self):
        """暂停Agent"""
        if self.status == AgentStatus.WORKING:
            self.status = AgentStatus.PAUSED
            logger.info(f"Agent {self.agent_id} paused")
    
    async def resume(self):
        """恢复Agent"""
        if self.status == AgentStatus.PAUSED:
            self.status = AgentStatus.IDLE
            logger.info(f"Agent {self.agent_id} resumed")
            
            # 继续处理任务
            if self.task_queue and not self.current_task:
                asyncio.create_task(self._process_next_task())
    
    async def clear_queue(self):
        """清空任务队列"""
        cleared_count = len(self.task_queue)
        self.task_queue.clear()
        logger.info(f"Agent {self.agent_id} queue cleared ({cleared_count} tasks removed)")
    
    def can_handle_task(self, task_type: str) -> bool:
        """检查是否能处理指定类型的任务"""
        return task_type in self.capabilities
    
    def estimate_processing_time(self, task: AgentTask) -> float:
        """估算任务处理时间"""
        if self.total_tasks_completed == 0:
            return 60.0  # 默认1分钟
        
        base_time = self.total_processing_time / self.total_tasks_completed
        
        # 根据任务优先级调整
        priority_multipliers = {
            TaskPriority.LOW: 0.8,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.HIGH: 1.3,
            TaskPriority.CRITICAL: 1.5
        }
        
        return base_time * priority_multipliers.get(task.priority, 1.0)


class AgentPool:
    """Agent池管理器"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_types: Dict[str, List[BaseAgent]] = {}
        
    def register_agent(self, agent: BaseAgent):
        """注册Agent"""
        self.agents[agent.agent_id] = agent
        
        if agent.agent_type not in self.agent_types:
            self.agent_types[agent.agent_type] = []
        self.agent_types[agent.agent_type].append(agent)
        
        logger.info(f"Agent {agent.agent_id} registered in pool")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取指定Agent"""
        return self.agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: str) -> List[BaseAgent]:
        """获取指定类型的所有Agent"""
        return self.agent_types.get(agent_type, [])
    
    def get_available_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """获取指定类型的可用Agent"""
        agents = self.get_agents_by_type(agent_type)
        
        # 优先选择空闲的Agent
        for agent in agents:
            if agent.status == AgentStatus.IDLE and not agent.current_task:
                return agent
        
        # 如果没有空闲的，选择队列最短的
        if agents:
            return min(agents, key=lambda a: len(a.task_queue))
        
        return None
    
    def get_pool_status(self) -> Dict[str, Any]:
        """获取Agent池状态"""
        status = {
            "total_agents": len(self.agents),
            "agent_types": {},
            "overall_stats": {
                "idle": 0,
                "working": 0,
                "paused": 0,
                "error": 0
            }
        }
        
        for agent_type, agents in self.agent_types.items():
            type_status = {
                "count": len(agents),
                "idle": sum(1 for a in agents if a.status == AgentStatus.IDLE),
                "working": sum(1 for a in agents if a.status == AgentStatus.WORKING),
                "average_queue_size": sum(len(a.task_queue) for a in agents) / len(agents)
            }
            status["agent_types"][agent_type] = type_status
            
            # 更新总体统计
            for agent in agents:
                status["overall_stats"][agent.status.value] += 1
        
        return status


# 全局Agent池
agent_pool = AgentPool()