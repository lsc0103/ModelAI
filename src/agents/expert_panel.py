"""
ModelAI 需求分析专家组系统
负责智能分析用户需求并制定Agent调用策略
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..api.multi_ai_client import get_multi_ai_client, AIRequest
from .base_agent import BaseAgent, AgentTask, AgentResult


class ComplexityLevel(str, Enum):
    """复杂度级别"""
    SIMPLE = "simple"        # 1-3分
    MEDIUM = "medium"        # 4-6分  
    COMPLEX = "complex"      # 7-9分
    ULTRA = "ultra"          # 10分


@dataclass
class RequirementAnalysis:
    """需求分析结果"""
    # 基础信息
    model_type: str              # 模型类型 (character, building, prop, etc.)
    description_summary: str     # 需求理解摘要
    
    # 复杂度评估
    complexity_score: int        # 复杂度评分 (1-10)
    complexity_level: ComplexityLevel
    complexity_factors: List[str]  # 复杂度因素
    
    # 技术需求
    technical_requirements: List[str]  # 技术需求列表
    special_features: List[str]        # 特殊功能需求
    
    # Agent调度
    required_agents: List[str]     # 需要的Agent列表
    agent_priorities: Dict[str, int]  # Agent优先级
    estimated_tokens: int         # 预计Token消耗
    estimated_cost: float         # 预计成本(USD)
    
    # 风险评估
    potential_challenges: List[str]  # 潜在挑战
    success_probability: float       # 成功概率(0-1)


class RequirementAnalysisExpert(BaseAgent):
    """需求理解专家 - 深度解析用户输入"""
    
    def __init__(self):
        super().__init__("requirement_analysis_expert")
    
    def _get_capabilities(self) -> List[str]:
        """获取Agent能力列表"""
        return [
            "multimodal_input_analysis",
            "model_type_identification", 
            "technical_constraint_extraction",
            "user_expectation_understanding",
            "requirement_clarity_assessment"
        ]
        
    def _get_system_prompt(self) -> str:
        return """你是ModelAI的需求理解专家，擅长深度解析用户的3D建模需求。
        
        你的专长：
        - 理解多模态输入（文字、图片、文档描述）
        - 识别模型类型和关键特征
        - 提取技术要求和约束条件
        - 发现隐含需求和用户期望
        
        分析时请关注：
        1. 模型类型识别 (角色/建筑/道具/载具/自然物等)
        2. 关键特征提取 (尺寸、风格、功能、材质等)  
        3. 技术约束识别 (性能要求、平台限制、格式需求等)
        4. 用户期望理解 (质量期待、用途说明、预算考虑等)
        
        输出JSON格式：
        {
            "model_type": "建议的模型类型",
            "key_features": ["关键特征1", "特征2"],
            "technical_constraints": ["约束1", "约束2"],
            "user_expectations": "用户期望描述",
            "clarity_score": "需求清晰度(1-10分)",
            "additional_questions": ["需要澄清的问题"]
        }
        """
        
    async def _process_task(self, task: AgentTask) -> AgentResult:
        """处理需求理解任务"""
        request = AIRequest(
            messages=[{
                "role": "user", 
                "content": f"请分析以下3D建模需求：\n{task.input_data.get('user_prompt', '')}"
            }],
            system=self._get_system_prompt(),
            max_tokens=1000,
            temperature=0.3
        )
        
        client = get_multi_ai_client()
        response = await client.send_message(request, self.agent_id)
        
        try:
            analysis = json.loads(response.content)
        except:
            # 如果JSON解析失败，构建基础分析
            analysis = {
                "model_type": "unknown",
                "key_features": [response.content[:100]],
                "technical_constraints": [],
                "user_expectations": response.content,
                "clarity_score": 5,
                "additional_questions": []
            }
        
        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            result_type="requirement_analysis",
            output_data=analysis,
            success=True,
            metadata={"tokens_used": response.usage.get("total_tokens", 0)}
        )


class ComplexityAssessmentExpert(BaseAgent):
    """复杂度评估专家 - 评估建模难度和资源需求"""
    
    def __init__(self):
        super().__init__("complexity_assessment_expert")
    
    def _get_capabilities(self) -> List[str]:
        """获取Agent能力列表"""
        return [
            "complexity_scoring",
            "geometry_difficulty_assessment",
            "material_complexity_analysis",
            "feature_difficulty_evaluation",
            "risk_factor_identification",
            "resource_estimation"
        ]
        
    def _get_system_prompt(self) -> str:
        return """你是ModelAI的复杂度评估专家，专门评估3D建模任务的难度和资源需求。
        
        复杂度评估标准：
        
        简单模型 (1-3分):
        - 基础几何形状 (立方体、球体变形)
        - 单一材质，简单纹理
        - 无动画需求，静态模型
        - 例：简单道具、基础建筑块
        
        中等模型 (4-6分):
        - 中等几何复杂度 (组合形状)
        - 多材质混合，PBR纹理  
        - 基础动画需求或模块化
        - 例：家具、载具、简单建筑
        
        复杂模型 (7-9分):
        - 高几何复杂度 (细节丰富)
        - 复杂材质系统，多层纹理
        - 高级功能 (骨骼、物理、特效)
        - 例：精细角色、复杂机械、大型建筑
        
        超复杂模型 (10分):
        - 极致细节和精度
        - 多系统集成 (角色+服装+武器)
        - 高级动画和交互系统
        - 例：游戏主角、电影级资产
        
        输出JSON格式：
        {
            "complexity_score": "复杂度评分(1-10)",
            "complexity_factors": ["影响复杂度的因素"],
            "geometry_complexity": "几何复杂度(1-10)",
            "material_complexity": "材质复杂度(1-10)", 
            "feature_complexity": "功能复杂度(1-10)",
            "estimated_work_hours": "预计工作小时数",
            "risk_factors": ["风险因素"]
        }
        """
        
    async def _process_task(self, task: AgentTask) -> AgentResult:
        """处理复杂度评估任务"""
        requirement_analysis = task.input_data.get('requirement_analysis', {})
        
        request = AIRequest(
            messages=[{
                "role": "user",
                "content": f"""
                请评估以下建模需求的复杂度：
                
                模型类型: {requirement_analysis.get('model_type', 'unknown')}
                关键特征: {requirement_analysis.get('key_features', [])}
                技术约束: {requirement_analysis.get('technical_constraints', [])}
                用户期望: {requirement_analysis.get('user_expectations', '')}
                
                原始需求: {task.input_data.get('user_prompt', '')}
                """
            }],
            system=self._get_system_prompt(),
            max_tokens=800,
            temperature=0.2
        )
        
        client = get_multi_ai_client()
        response = await client.send_message(request, self.agent_id)
        
        try:
            assessment = json.loads(response.content)
        except:
            # 默认中等复杂度
            assessment = {
                "complexity_score": 5,
                "complexity_factors": ["分析失败，使用默认值"],
                "geometry_complexity": 5,
                "material_complexity": 5,
                "feature_complexity": 5,
                "estimated_work_hours": 2,
                "risk_factors": ["解析失败"]
            }
        
        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            result_type="complexity_assessment",
            output_data=assessment,
            success=True,
            metadata={"tokens_used": response.usage.get("total_tokens", 0)}
        )


class ResourceSchedulingExpert(BaseAgent):
    """资源调度专家 - 制定Agent调用策略和成本估算"""
    
    def __init__(self):
        super().__init__("resource_scheduling_expert")
    
    def _get_capabilities(self) -> List[str]:
        """获取Agent能力列表"""
        return [
            "agent_selection_strategy",
            "resource_allocation_optimization",
            "cost_estimation",
            "performance_prediction",
            "parallel_execution_planning",
            "success_probability_assessment"
        ]
        
    def _get_system_prompt(self) -> str:
        return """你是ModelAI的资源调度专家，负责制定最优的Agent调用策略。
        
        可用的核心Agent类型：
        1. geometry_construction_agent - 几何构建 (必需)
        2. surface_detail_agent - 表面细节雕刻
        3. material_texture_agent - 材质纹理设计 (必需)
        4. functional_integration_agent - 功能集成 (骨骼/模块化/物理)
        5. performance_optimization_agent - 性能优化
        6. quality_control_agent - 质量控制 (必需)
        
        调度策略：
        
        简单模型 (1-3分):
        - 必需Agent: geometry, material, quality (3个)
        - 预计成本: $0.08-0.12
        
        中等模型 (4-6分):
        - 标准Agent: geometry, surface_detail, material, quality (4-5个)
        - 预计成本: $0.18-0.25
        
        复杂模型 (7-9分):
        - 完整Agent: geometry, surface_detail, material, functional, optimization, quality (6-7个)
        - 预计成本: $0.35-0.50
        
        超复杂模型 (10分):
        - 全部Agent + 多轮迭代 (8-12个调用)
        - 预计成本: $0.70-1.20
        
        输出JSON格式：
        {
            "required_agents": ["agent1", "agent2"],
            "agent_sequence": ["执行顺序"],
            "parallel_groups": [["可并行执行的Agent组"]],
            "estimated_tokens": "预计Token消耗",
            "estimated_cost": "预计成本(USD)",
            "estimated_duration": "预计时间(分钟)",
            "success_probability": "成功概率(0-1)",
            "optimization_suggestions": ["优化建议"]
        }
        """
        
    async def _process_task(self, task: AgentTask) -> AgentResult:
        """处理资源调度任务"""
        requirement_analysis = task.input_data.get('requirement_analysis', {})
        complexity_assessment = task.input_data.get('complexity_assessment', {})
        
        request = AIRequest(
            messages=[{
                "role": "user",
                "content": f"""
                请为以下建模任务制定Agent调用策略：
                
                需求分析结果:
                - 模型类型: {requirement_analysis.get('model_type', 'unknown')}
                - 关键特征: {requirement_analysis.get('key_features', [])}
                - 需求清晰度: {requirement_analysis.get('clarity_score', 5)}/10
                
                复杂度评估结果:
                - 总复杂度: {complexity_assessment.get('complexity_score', 5)}/10  
                - 几何复杂度: {complexity_assessment.get('geometry_complexity', 5)}/10
                - 材质复杂度: {complexity_assessment.get('material_complexity', 5)}/10
                - 功能复杂度: {complexity_assessment.get('feature_complexity', 5)}/10
                - 风险因素: {complexity_assessment.get('risk_factors', [])}
                
                请制定最优的Agent调用计划。
                """
            }],
            system=self._get_system_prompt(),
            max_tokens=800,
            temperature=0.1  # 需要稳定的调度决策
        )
        
        client = get_multi_ai_client()
        response = await client.send_message(request, self.agent_id)
        
        try:
            schedule = json.loads(response.content)
        except:
            # 默认调度方案
            try:
                complexity = int(complexity_assessment.get('complexity_score', 5))
            except (ValueError, TypeError):
                complexity = 5  # 默认中等复杂度
            if complexity <= 3:
                agents = ["geometry_construction_agent", "material_texture_agent", "quality_control_agent"]
                cost = 0.10
            elif complexity <= 6:
                agents = ["geometry_construction_agent", "surface_detail_agent", 
                         "material_texture_agent", "quality_control_agent"]
                cost = 0.22
            else:
                agents = ["geometry_construction_agent", "surface_detail_agent",
                         "material_texture_agent", "functional_integration_agent", 
                         "performance_optimization_agent", "quality_control_agent"]
                cost = 0.45
                
            schedule = {
                "required_agents": agents,
                "agent_sequence": agents,
                "parallel_groups": [agents[:-1], [agents[-1]]],  # 最后一个质量控制单独执行
                "estimated_tokens": len(agents) * 1500,
                "estimated_cost": cost,
                "estimated_duration": len(agents) * 0.5,
                "success_probability": 0.85,
                "optimization_suggestions": ["使用默认调度方案"]
            }
        
        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            result_type="resource_scheduling",
            output_data=schedule,
            success=True,
            metadata={"tokens_used": response.usage.get("total_tokens", 0)}
        )


class ExpertPanel:
    """需求分析专家组 - 协调三个专家进行需求分析"""
    
    def __init__(self):
        self.requirement_expert = RequirementAnalysisExpert()
        self.complexity_expert = ComplexityAssessmentExpert()
        self.scheduling_expert = ResourceSchedulingExpert()
    
    def _safe_float_convert(self, value, default=0.0):
        """安全地将值转换为浮点数"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # 移除货币符号和空格
            cleaned = value.replace('$', '').replace('¥', '').replace('€', '').strip()
            try:
                return float(cleaned)
            except (ValueError, TypeError):
                return default
        
        return default
        
    async def analyze_requirement(self, user_prompt: str, additional_data: Dict[str, Any] = None) -> RequirementAnalysis:
        """
        完整的需求分析流程
        
        Args:
            user_prompt: 用户输入的建模需求
            additional_data: 额外数据 (图片、文档等)
            
        Returns:
            RequirementAnalysis: 完整的分析结果
        """
        
        # 第一步：需求理解
        req_task = AgentTask(
            task_id=f"req_analysis_{hash(user_prompt)}",
            task_type="requirement_analysis",
            description="分析用户3D建模需求",
            input_data={"user_prompt": user_prompt, **(additional_data or {})}
        )
        
        requirement_result = await self.requirement_expert.process_task(req_task)
        
        # 第二步：复杂度评估
        complexity_task = AgentTask(
            task_id=f"complexity_analysis_{hash(user_prompt)}",
            task_type="complexity_assessment",
            description="评估建模复杂度和资源需求", 
            input_data={
                "user_prompt": user_prompt,
                "requirement_analysis": requirement_result.output_data
            }
        )
        
        complexity_result = await self.complexity_expert.process_task(complexity_task)
        
        # 第三步：资源调度
        scheduling_task = AgentTask(
            task_id=f"scheduling_{hash(user_prompt)}",
            task_type="resource_scheduling",
            description="制定Agent调用策略和成本估算",
            input_data={
                "user_prompt": user_prompt,
                "requirement_analysis": requirement_result.output_data,
                "complexity_assessment": complexity_result.output_data
            }
        )
        
        scheduling_result = await self.scheduling_expert.process_task(scheduling_task)
        
        # 整合结果
        req_data = requirement_result.output_data
        comp_data = complexity_result.output_data  
        sched_data = scheduling_result.output_data
        
        # 确定复杂度级别
        complexity_score = int(comp_data.get('complexity_score', 5))
        if complexity_score <= 3:
            complexity_level = ComplexityLevel.SIMPLE
        elif complexity_score <= 6:
            complexity_level = ComplexityLevel.MEDIUM
        elif complexity_score <= 9:
            complexity_level = ComplexityLevel.COMPLEX
        else:
            complexity_level = ComplexityLevel.ULTRA
        
        return RequirementAnalysis(
            # 基础信息
            model_type=req_data.get('model_type', 'unknown'),
            description_summary=req_data.get('user_expectations', user_prompt[:100]),
            
            # 复杂度评估
            complexity_score=complexity_score,
            complexity_level=complexity_level,
            complexity_factors=comp_data.get('complexity_factors', []),
            
            # 技术需求
            technical_requirements=req_data.get('technical_constraints', []),
            special_features=req_data.get('key_features', []),
            
            # Agent调度  
            required_agents=sched_data.get('required_agents', []),
            agent_priorities={agent: i for i, agent in enumerate(sched_data.get('agent_sequence', []))},
            estimated_tokens=int(sched_data.get('estimated_tokens', 5000)),
            estimated_cost=self._safe_float_convert(sched_data.get('estimated_cost', 0.25)),
            
            # 风险评估
            potential_challenges=comp_data.get('risk_factors', []),
            success_probability=self._safe_float_convert(sched_data.get('success_probability', 0.8), 0.8)
        )
    
    async def get_analysis_summary(self, analysis: RequirementAnalysis) -> str:
        """获取分析结果的用户友好摘要"""
        return f"""
🎯 需求分析完成！

📋 模型类型: {analysis.model_type}
📊 复杂度: {analysis.complexity_level.value.upper()} ({analysis.complexity_score}/10分)
🤖 需要Agent: {len(analysis.required_agents)}个
💰 预计成本: ${analysis.estimated_cost:.2f}
⏱️ 预计时间: {len(analysis.required_agents) * 0.5:.1f}分钟
📈 成功概率: {analysis.success_probability:.0%}

🔍 主要特征: {', '.join(analysis.special_features[:3])}
⚠️ 注意事项: {', '.join(analysis.potential_challenges[:2]) if analysis.potential_challenges else '无特殊风险'}
        """.strip()


# 全局专家组实例
_expert_panel: Optional[ExpertPanel] = None


def get_expert_panel() -> ExpertPanel:
    """获取专家组单例"""
    global _expert_panel
    if _expert_panel is None:
        _expert_panel = ExpertPanel()
    return _expert_panel