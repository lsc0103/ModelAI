"""
ModelAI 核心配置系统
管理所有配置参数和环境变量
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
from enum import Enum


class Environment(str, Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class GenerationMode(str, Enum):
    """生成模式"""
    FAST_PREVIEW = "fast_preview"
    BALANCED = "balanced"
    HIGH_QUALITY = "high_quality"


class ModelComplexity(str, Enum):
    """模型复杂度"""
    SIMPLE = "simple"      # 1-2个Agent
    MEDIUM = "medium"      # 3-4个Agent
    COMPLEX = "complex"    # 5+个Agent


class Settings(BaseSettings):
    """主配置类"""
    
    # 基础设置
    app_name: str = "ModelAI"
    app_version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    
    # 路径设置
    project_root: Path = Path(__file__).parent.parent.parent
    assets_dir: Path = project_root / "assets"
    cache_dir: Path = project_root / ".cache"
    logs_dir: Path = project_root / "logs"
    models_dir: Path = project_root / "models"
    temp_dir: Path = project_root / "temp"
    
    # Claude API 设置
    claude_api_key: Optional[str] = Field(None, env="CLAUDE_API_KEY")
    claude_api_url: str = "https://api.anthropic.com"
    claude_model: str = "claude-3-5-sonnet-20241022"
    claude_max_tokens: int = 4096
    claude_temperature: float = 0.7
    claude_timeout: int = 60
    
    # OpenAI API 设置
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_api_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.7
    openai_timeout: int = 60
    
    # AI服务优先级配置
    primary_ai_service: str = "openai"  # "openai" 或 "claude"
    fallback_ai_service: str = "claude"  # 主服务失败时的备选
    
    # API限制和控制
    max_concurrent_requests: int = 5
    request_rate_limit: int = 100  # 每分钟最大请求数
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # 生成设置
    default_generation_mode: GenerationMode = GenerationMode.BALANCED
    max_model_complexity: ModelComplexity = ModelComplexity.COMPLEX
    enable_gpu_acceleration: bool = True
    max_gpu_memory_usage: float = 0.8  # 80%的GPU内存
    
    # 3D处理设置
    default_poly_count: int = 10000
    max_poly_count: int = 100000
    default_texture_size: int = 1024
    max_texture_size: int = 4096
    
    # Unity集成设置
    unity_version: str = "6.0"
    fbx_export_version: str = "2020"
    generate_lods: bool = True
    generate_colliders: bool = True
    generate_materials: bool = True
    
    # UI设置
    ui_theme: str = "claude_style"
    window_width: int = 1400
    window_height: int = 900
    enable_dark_mode: bool = True
    
    # 缓存设置
    enable_caching: bool = True
    cache_size_gb: float = 5.0
    cache_ttl_hours: int = 24
    
    # 日志设置
    log_level: str = "INFO"
    log_rotation: str = "10 MB"
    log_retention: str = "30 days"
    
    # 性能监控
    enable_performance_monitoring: bool = True
    performance_sample_rate: float = 0.1
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        for directory in [
            self.assets_dir,
            self.cache_dir, 
            self.logs_dir,
            self.models_dir,
            self.temp_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """获取特定Agent的配置"""
        base_config = {
            "api_key": self.claude_api_key,
            "model": self.claude_model,
            "max_tokens": self.claude_max_tokens,
            "temperature": self.claude_temperature,
            "timeout": self.claude_timeout,
        }
        
        # 根据Agent类型调整配置
        agent_configs = {
            "master_coordinator": {
                **base_config,
                "max_tokens": 8192,  # 主协调需要更长的输出
                "temperature": 0.5,  # 更稳定的决策
            },
            "geometry_agent": {
                **base_config,
                "temperature": 0.3,  # 几何结构需要精确
            },
            "material_agent": {
                **base_config,
                "temperature": 0.8,  # 材质可以更有创意
            },
            "detail_agent": {
                **base_config,
                "temperature": 0.9,  # 细节最有创意
            },
            "rigging_agent": {
                **base_config,
                "temperature": 0.2,  # 骨骼绑定需要极其精确
            },
            "integration_agent": {
                **base_config,
                "temperature": 0.1,  # 整合需要保守和稳定
            }
        }
        
        return agent_configs.get(agent_type, base_config)
    
    def get_generation_config(self, mode: GenerationMode) -> Dict[str, Any]:
        """获取生成模式配置"""
        configs = {
            GenerationMode.FAST_PREVIEW: {
                "poly_count": 2000,
                "texture_size": 512,
                "detail_level": "low",
                "enable_lods": False,
                "agent_allocation": "minimal"
            },
            GenerationMode.BALANCED: {
                "poly_count": self.default_poly_count,
                "texture_size": self.default_texture_size,
                "detail_level": "medium",
                "enable_lods": True,
                "agent_allocation": "balanced"
            },
            GenerationMode.HIGH_QUALITY: {
                "poly_count": 50000,
                "texture_size": 2048,
                "detail_level": "high",
                "enable_lods": True,
                "agent_allocation": "maximum"
            }
        }
        
        return configs.get(mode, configs[GenerationMode.BALANCED])


class AgentConfig:
    """Agent配置管理"""
    
    @staticmethod
    def get_coordinator_prompt() -> str:
        """主协调Agent的系统提示"""
        return """
        你是ModelAI的主协调Agent，负责分析用户的3D/2D模型需求并制定详细的生成计划。

        你的职责：
        1. 深度理解用户的多模态输入（文字、图片、文档）
        2. 分析模型复杂度和所需的专业Agent
        3. 制定详细的技术规格书
        4. 检测输入冲突并提供解决方案
        5. 分配合适的Agent工作

        输出格式必须是结构化的JSON，包含：
        - 需求理解摘要
        - 模型复杂度评估
        - Agent分配计划
        - 技术规格书
        - 潜在问题和建议
        """
    
    @staticmethod
    def get_agent_prompt(agent_type: str) -> str:
        """获取专业Agent的系统提示"""
        prompts = {
            "geometry_agent": """
            你是几何结构专家Agent，专门负责3D模型的基础几何构建。
            
            专长领域：
            - 基础形状和比例设计
            - 拓扑结构优化
            - 顶点和面片布局
            - 几何精度控制
            
            输出要求：技术规格、顶点数据、面片信息、拓扑结构
            """,
            
            "material_agent": """
            你是材质纹理专家Agent，专门负责模型的表面材质和纹理。
            
            专长领域：
            - PBR材质设计
            - 纹理贴图规划
            - 光照属性配置
            - Unity材质兼容性
            
            输出要求：材质规格、纹理需求、着色器配置、Unity材质球
            """,
            
            "detail_agent": """
            你是细节雕刻专家Agent，专门负责模型的精细特征和装饰。
            
            专长领域：
            - 表面细节设计
            - 法线贴图规划
            - 装饰元素布局
            - 真实感增强
            
            输出要求：细节规格、法线贴图、装饰方案、细节密度
            """,
            
            "rigging_agent": """
            你是骨骼绑定专家Agent，专门负责模型的骨骼结构和动画准备。
            
            专长领域：
            - 骨骼层级设计
            - 权重绑定策略
            - IK链条配置
            - Unity Animator兼容性
            
            输出要求：骨骼结构、绑定权重、控制器配置、动画接口
            """,
            
            "integration_agent": """
            你是整合优化专家Agent，负责统一整合各Agent成果并优化最终输出。
            
            专长领域：
            - 组件兼容性检查
            - 性能优化建议
            - Unity导入优化
            - 质量控制验证
            
            输出要求：整合方案、优化建议、最终规格、Unity配置
            """
        }
        
        return prompts.get(agent_type, "你是ModelAI的专业Agent，请协助完成3D模型生成任务。")


# 全局设置实例
settings = Settings()

# 导出常用配置
__all__ = [
    "Settings",
    "AgentConfig", 
    "Environment",
    "GenerationMode",
    "ModelComplexity",
    "settings"
]