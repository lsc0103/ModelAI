"""
ModelAI 游戏开发预设系统
面向小白用户的场景化配置
"""

from typing import Dict, Any, List
from enum import Enum
from dataclasses import dataclass


class Platform(str, Enum):
    """目标平台"""
    MOBILE_ANDROID = "mobile_android"
    MOBILE_IOS = "mobile_ios"
    PC_LOW = "pc_low"
    PC_MID = "pc_mid"
    PC_HIGH = "pc_high"
    CONSOLE_SWITCH = "console_switch"
    CONSOLE_PS5 = "console_ps5"
    CONSOLE_XBOX = "console_xbox"
    VR_QUEST = "vr_quest"
    VR_PCVR = "vr_pcvr"
    WEB_BROWSER = "web_browser"
    CROSS_PLATFORM = "cross_platform"


class GameType(str, Enum):
    """游戏类型"""
    MOBILE = "mobile"
    INDIE_PC = "indie_pc" 
    AAA_PC = "aaa_pc"
    VR = "vr"
    RETRO = "retro"
    CONSOLE = "console"


class ModelPurpose(str, Enum):
    """模型用途"""
    MAIN_CHARACTER = "main_character"
    NPC = "npc"
    ARCHITECTURE = "architecture"
    PROPS = "props"
    WEAPONS = "weapons"
    VEHICLES = "vehicles"
    ENVIRONMENT = "environment"


class QualityTier(str, Enum):
    """质量档次"""
    PROTOTYPE = "prototype"
    PRODUCTION = "production"
    SHOWCASE = "showcase"


@dataclass
class GamePreset:
    """游戏预设配置"""
    name: str
    description: str
    poly_range: tuple  # (min, max)
    texture_size: int
    enable_lods: bool
    performance_target: str
    recommended_agents: List[str]
    unity_features: Dict[str, bool]


@dataclass
class PlatformPreset:
    """平台预设配置"""
    name: str
    description: str
    hardware_level: str  # low, mid, high, ultra
    poly_multiplier: float  # 多边形数量系数
    texture_multiplier: float  # 纹理分辨率系数
    memory_limit: int  # MB
    performance_target: str
    optimization_features: Dict[str, Any]
    multi_quality_support: bool  # 是否支持多质量版本


class GamePresets:
    """游戏预设管理器"""
    
    # 游戏类型预设
    GAME_TYPE_PRESETS = {
        GameType.MOBILE: GamePreset(
            name="📱 手机游戏",
            description="适配iOS/Android，优化性能和包体大小",
            poly_range=(500, 3000),
            texture_size=512,
            enable_lods=True,
            performance_target="60fps on mobile",
            recommended_agents=["geometry_agent", "material_agent"],
            unity_features={
                "generate_lods": True,
                "generate_colliders": True,
                "generate_materials": True,
                "optimize_for_mobile": True
            }
        ),
        
        GameType.INDIE_PC: GamePreset(
            name="💻 PC独立游戏", 
            description="Steam发布标准，平衡质量与开发效率",
            poly_range=(2000, 12000),
            texture_size=1024,
            enable_lods=True,
            performance_target="60fps on mid-range PC",
            recommended_agents=["geometry_agent", "material_agent", "detail_agent"],
            unity_features={
                "generate_lods": True,
                "generate_colliders": True,
                "generate_materials": True,
                "pbr_materials": True
            }
        ),
        
        GameType.AAA_PC: GamePreset(
            name="🏆 PC大型游戏",
            description="主机级品质，追求最佳视觉效果",
            poly_range=(15000, 80000),
            texture_size=2048,
            enable_lods=True,
            performance_target="60fps on high-end PC",
            recommended_agents=["geometry_agent", "material_agent", "detail_agent", "rigging_agent"],
            unity_features={
                "generate_lods": True,
                "generate_colliders": True,
                "generate_materials": True,
                "pbr_materials": True,
                "hdrp_support": True
            }
        ),
        
        GameType.VR: GamePreset(
            name="🥽 VR游戏",
            description="90fps保证，优化渲染性能",
            poly_range=(800, 5000),
            texture_size=1024,
            enable_lods=True,
            performance_target="90fps VR",
            recommended_agents=["geometry_agent", "material_agent"],
            unity_features={
                "generate_lods": True,
                "generate_colliders": True,
                "generate_materials": True,
                "vr_optimized": True,
                "simplified_shaders": True
            }
        ),
        
        GameType.RETRO: GamePreset(
            name="🎮 复古像素",
            description="低多边形风格，怀旧美学",
            poly_range=(100, 1000),
            texture_size=256,
            enable_lods=False,
            performance_target="60fps on any device",
            recommended_agents=["geometry_agent"],
            unity_features={
                "generate_lods": False,
                "generate_colliders": True,
                "pixel_perfect": True,
                "unlit_materials": True
            }
        ),
        
        GameType.CONSOLE: GamePreset(
            name="🕹️ 主机游戏",
            description="PS5/Xbox Series级别品质",
            poly_range=(20000, 100000),
            texture_size=2048,
            enable_lods=True,
            performance_target="60fps on console",
            recommended_agents=["geometry_agent", "material_agent", "detail_agent", "rigging_agent"],
            unity_features={
                "generate_lods": True,
                "generate_colliders": True,
                "generate_materials": True,
                "pbr_materials": True,
                "hdrp_support": True,
                "console_optimized": True
            }
        )
    }
    
    # 平台预设配置
    PLATFORM_PRESETS = {
        Platform.MOBILE_ANDROID: PlatformPreset(
            name="📱 Android手机",
            description="兼容主流Android设备，优化性能和内存",
            hardware_level="low",
            poly_multiplier=0.3,
            texture_multiplier=0.5,
            memory_limit=512,  # MB
            performance_target="30-60fps",
            optimization_features={
                "texture_compression": "ETC2",
                "shader_variant_stripping": True,
                "draw_call_batching": True,
                "occlusion_culling": True,
                "frustum_culling": True,
                "lod_bias": 1.5
            },
            multi_quality_support=True
        ),
        
        Platform.MOBILE_IOS: PlatformPreset(
            name="📱 iOS手机",
            description="针对iPhone/iPad优化，更好的性能",
            hardware_level="mid",
            poly_multiplier=0.4,
            texture_multiplier=0.6,
            memory_limit=1024,  # MB
            performance_target="60fps",
            optimization_features={
                "texture_compression": "ASTC",
                "metal_rendering": True,
                "shader_variant_stripping": True,
                "draw_call_batching": True,
                "dynamic_batching": True
            },
            multi_quality_support=True
        ),
        
        Platform.PC_LOW: PlatformPreset(
            name="💻 低配PC",
            description="集成显卡，老旧硬件友好",
            hardware_level="low",
            poly_multiplier=0.6,
            texture_multiplier=0.7,
            memory_limit=2048,  # MB
            performance_target="30-45fps",
            optimization_features={
                "texture_compression": "DXT",
                "shader_quality": "low",
                "shadow_quality": "low",
                "reflection_probes": False,
                "realtime_lighting": False
            },
            multi_quality_support=True
        ),
        
        Platform.PC_MID: PlatformPreset(
            name="💻 中配PC",
            description="主流游戏PC，平衡画质与性能",
            hardware_level="mid",
            poly_multiplier=1.0,
            texture_multiplier=1.0,
            memory_limit=4096,  # MB
            performance_target="60fps",
            optimization_features={
                "texture_compression": "DXT",
                "shader_quality": "medium",
                "shadow_quality": "medium",
                "reflection_probes": True,
                "realtime_lighting": True,
                "post_processing": True
            },
            multi_quality_support=True
        ),
        
        Platform.PC_HIGH: PlatformPreset(
            name="💻 高配PC",
            description="高端显卡，追求最佳画质",
            hardware_level="high",
            poly_multiplier=1.5,
            texture_multiplier=1.5,
            memory_limit=8192,  # MB
            performance_target="60-120fps",
            optimization_features={
                "texture_compression": "BC7",
                "shader_quality": "high",
                "shadow_quality": "ultra",
                "reflection_probes": True,
                "realtime_lighting": True,
                "post_processing": True,
                "hdr_rendering": True
            },
            multi_quality_support=False  # 高配PC通常不需要多版本
        ),
        
        Platform.CONSOLE_SWITCH: PlatformPreset(
            name="🎮 Nintendo Switch",
            description="便携模式优化，电池续航考虑",
            hardware_level="low",
            poly_multiplier=0.4,
            texture_multiplier=0.5,
            memory_limit=1024,  # MB
            performance_target="30fps stable",
            optimization_features={
                "texture_compression": "ASTC",
                "shader_quality": "medium",
                "dynamic_resolution": True,
                "adaptive_quality": True,
                "power_saving_mode": True
            },
            multi_quality_support=True  # 掌机/底座模式
        ),
        
        Platform.CONSOLE_PS5: PlatformPreset(
            name="🎮 PlayStation 5",
            description="次世代主机，4K60fps目标",
            hardware_level="ultra",
            poly_multiplier=2.0,
            texture_multiplier=2.0,
            memory_limit=12288,  # MB
            performance_target="60fps 4K",
            optimization_features={
                "texture_compression": "BC7",
                "ray_tracing": True,
                "hdr_rendering": True,
                "variable_rate_shading": True,
                "mesh_shaders": True,
                "ssd_streaming": True
            },
            multi_quality_support=True  # 性能/画质模式
        ),
        
        Platform.CONSOLE_XBOX: PlatformPreset(
            name="🎮 Xbox Series X/S",
            description="Xbox生态，智能分发支持",
            hardware_level="ultra",
            poly_multiplier=2.0,
            texture_multiplier=2.0,
            memory_limit=10240,  # MB
            performance_target="60fps 4K",
            optimization_features={
                "texture_compression": "BC7",
                "ray_tracing": True,
                "hdr_rendering": True,
                "variable_rate_shading": True,
                "smart_delivery": True,
                "quick_resume": True
            },
            multi_quality_support=True  # Series X/S区别
        ),
        
        Platform.VR_QUEST: PlatformPreset(
            name="🥽 Meta Quest",
            description="移动VR，90Hz严格要求",
            hardware_level="mid",
            poly_multiplier=0.3,
            texture_multiplier=0.4,
            memory_limit=1024,  # MB
            performance_target="90fps stable",
            optimization_features={
                "foveated_rendering": True,
                "single_pass_stereo": True,
                "texture_compression": "ASTC",
                "shader_optimization": "mobile",
                "draw_call_optimization": True
            },
            multi_quality_support=False  # VR要求稳定
        ),
        
        Platform.VR_PCVR: PlatformPreset(
            name="🥽 PC VR",
            description="高端VR头显，极致沉浸感",
            hardware_level="ultra",
            poly_multiplier=1.2,
            texture_multiplier=1.5,
            memory_limit=6144,  # MB
            performance_target="90-120fps",
            optimization_features={
                "foveated_rendering": True,
                "single_pass_stereo": True,
                "msaa": True,
                "high_resolution": True,
                "ray_tracing": False  # VR性能优先
            },
            multi_quality_support=True  # 不同头显适配
        ),
        
        Platform.WEB_BROWSER: PlatformPreset(
            name="🌐 Web浏览器",
            description="WebGL/WebGPU，即开即玩",
            hardware_level="low",
            poly_multiplier=0.4,
            texture_multiplier=0.6,
            memory_limit=512,  # MB
            performance_target="30fps",
            optimization_features={
                "texture_compression": "WebGL",
                "shader_precision": "mediump",
                "draw_call_limit": 100,
                "memory_optimization": True,
                "loading_optimization": True
            },
            multi_quality_support=True  # 适应不同设备
        ),
        
        Platform.CROSS_PLATFORM: PlatformPreset(
            name="🌍 跨平台通用",
            description="一套资源适配多平台，智能降级",
            hardware_level="adaptive",
            poly_multiplier=1.0,
            texture_multiplier=1.0,
            memory_limit=2048,  # MB (基准)
            performance_target="adaptive",
            optimization_features={
                "auto_quality_scaling": True,
                "platform_detection": True,
                "adaptive_lod": True,
                "texture_streaming": True,
                "shader_variants": True,
                "multi_resolution_support": True
            },
            multi_quality_support=True  # 必须支持
        )
    }
    
    # 模型用途预设
    PURPOSE_PRESETS = {
        ModelPurpose.MAIN_CHARACTER: {
            "name": "👤 主角模型",
            "description": "最高细节，完整功能",
            "poly_multiplier": 2.0,
            "texture_multiplier": 1.5,
            "required_agents": ["geometry_agent", "material_agent", "detail_agent", "rigging_agent"],
            "features": {
                "detailed_textures": True,
                "bone_rigging": True,
                "facial_blend_shapes": True,
                "multiple_lods": True
            }
        },
        
        ModelPurpose.NPC: {
            "name": "🤖 NPC角色", 
            "description": "中等细节，基础功能",
            "poly_multiplier": 0.7,
            "texture_multiplier": 1.0,
            "required_agents": ["geometry_agent", "material_agent"],
            "features": {
                "basic_textures": True,
                "simple_rigging": True,
                "shared_materials": True
            }
        },
        
        ModelPurpose.ARCHITECTURE: {
            "name": "🏠 建筑场景",
            "description": "模块化，可重复使用",
            "poly_multiplier": 1.2,
            "texture_multiplier": 0.8,
            "required_agents": ["geometry_agent", "material_agent"],
            "features": {
                "modular_design": True,
                "tiling_textures": True,
                "lightmap_support": True,
                "occlusion_culling": True
            }
        },
        
        ModelPurpose.PROPS: {
            "name": "⚔️ 道具物品",
            "description": "适中细节，物理属性",
            "poly_multiplier": 0.8,
            "texture_multiplier": 1.2,
            "required_agents": ["geometry_agent", "material_agent"],
            "features": {
                "physics_colliders": True,
                "interaction_points": True,
                "pickup_animations": True
            }
        },
        
        ModelPurpose.WEAPONS: {
            "name": "⚔️ 武器装备",
            "description": "高细节武器，精确建模",
            "poly_multiplier": 1.2,
            "texture_multiplier": 1.5,
            "required_agents": ["geometry_agent", "material_agent", "detail_agent"],
            "features": {
                "high_detail_textures": True,
                "weapon_attachments": True,
                "animation_ready": True,
                "damage_states": True
            }
        },
        
        ModelPurpose.VEHICLES: {
            "name": "🚗 载具车辆",
            "description": "复杂结构，动态部件", 
            "poly_multiplier": 1.5,
            "texture_multiplier": 1.0,
            "required_agents": ["geometry_agent", "material_agent", "rigging_agent"],
            "features": {
                "wheel_rigging": True,
                "interior_detail": True,
                "damage_variants": True
            }
        },
        
        ModelPurpose.ENVIRONMENT: {
            "name": "🌲 环境装饰",
            "description": "大量实例，性能优化",
            "poly_multiplier": 0.5,
            "texture_multiplier": 0.7,
            "required_agents": ["geometry_agent"],
            "features": {
                "instancing_ready": True,
                "wind_animation": True,
                "seasonal_variants": True
            }
        }
    }
    
    # 质量档次预设
    QUALITY_PRESETS = {
        QualityTier.PROTOTYPE: {
            "name": "⚡ 快速原型",
            "description": "验证概念，快速迭代",
            "poly_multiplier": 0.3,
            "texture_multiplier": 0.5,
            "generation_speed": "fastest",
            "features": {
                "basic_geometry": True,
                "placeholder_textures": True,
                "no_optimization": True
            }
        },
        
        QualityTier.PRODUCTION: {
            "name": "✅ 发布标准", 
            "description": "平衡质量与性能，适合正式发布",
            "poly_multiplier": 1.0,
            "texture_multiplier": 1.0,
            "generation_speed": "balanced",
            "features": {
                "optimized_geometry": True,
                "production_textures": True,
                "performance_tested": True
            }
        },
        
        QualityTier.SHOWCASE: {
            "name": "💎 展示精品",
            "description": "最高质量，用于演示和营销",
            "poly_multiplier": 2.0,
            "texture_multiplier": 2.0,
            "generation_speed": "quality_first",
            "features": {
                "maximum_detail": True,
                "4k_textures": True,
                "artistic_polish": True
            }
        }
    }
    
    @classmethod
    def get_combined_config(
        cls, 
        game_type: GameType,
        model_purpose: ModelPurpose, 
        quality_tier: QualityTier,
        platform: Platform = None
    ) -> Dict[str, Any]:
        """获取组合配置"""
        
        # 获取基础预设
        game_preset = cls.GAME_TYPE_PRESETS[game_type]
        purpose_config = cls.PURPOSE_PRESETS[model_purpose]
        quality_config = cls.QUALITY_PRESETS[quality_tier]
        platform_config = cls.PLATFORM_PRESETS.get(platform) if platform else None
        
        # 计算最终参数，包含平台影响
        base_poly = sum(game_preset.poly_range) // 2
        
        # 应用所有系数
        poly_multiplier = (
            purpose_config["poly_multiplier"] * 
            quality_config["poly_multiplier"]
        )
        if platform_config:
            poly_multiplier *= platform_config.poly_multiplier
            
        final_poly = int(base_poly * poly_multiplier)
        
        # 计算纹理分辨率
        texture_multiplier = (
            purpose_config["texture_multiplier"] *
            quality_config["texture_multiplier"]
        )
        if platform_config:
            texture_multiplier *= platform_config.texture_multiplier
            
        final_texture = int(game_preset.texture_size * texture_multiplier)
        
        # 组合Agent需求
        required_agents = list(set(
            game_preset.recommended_agents + 
            purpose_config["required_agents"]
        ))
        
        # 合并Unity功能特性
        unity_features = {
            **game_preset.unity_features,
            **purpose_config["features"],
            **quality_config["features"]
        }
        
        # 添加平台特定功能
        if platform_config:
            unity_features.update(platform_config.optimization_features)
        
        # 构建配置信息
        config_info = {
            # 显示信息
            "preset_summary": {
                "game_type": game_preset.name,
                "model_purpose": purpose_config["name"], 
                "quality_tier": quality_config["name"],
                "platform": platform_config.name if platform_config else "通用",
                "description": f"{game_preset.description} | {purpose_config['description']}"
            },
            
            # 技术参数
            "poly_count": min(final_poly, 100000),  # 上限保护
            "texture_size": min(final_texture, 4096),  # 上限保护
            "enable_lods": game_preset.enable_lods,
            "performance_target": platform_config.performance_target if platform_config else game_preset.performance_target,
            "memory_limit": platform_config.memory_limit if platform_config else 2048,
            
            # Agent配置
            "required_agents": required_agents,
            "generation_priority": quality_config["generation_speed"],
            
            # Unity功能
            "unity_features": unity_features,
            
            # 平台特性
            "platform_features": {
                "hardware_level": platform_config.hardware_level if platform_config else "mid",
                "multi_quality_support": platform_config.multi_quality_support if platform_config else False,
                "optimization_features": platform_config.optimization_features if platform_config else {}
            },
            
            # 原始配置（供调试）
            "_raw_config": {
                "game_preset": game_preset,
                "purpose_config": purpose_config,
                "quality_config": quality_config,
                "platform_config": platform_config
            }
        }
        
        # 如果是跨平台，生成多版本配置
        if platform_config and platform_config.multi_quality_support:
            config_info["multi_platform_variants"] = cls._generate_platform_variants(config_info)
        
        return config_info
    
    @classmethod
    def _generate_platform_variants(cls, base_config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """生成多平台变体配置"""
        variants = {}
        
        base_poly = base_config["poly_count"]
        base_texture = base_config["texture_size"]
        
        # 生成不同质量级别的变体
        quality_levels = {
            "ultra": {"poly": 1.5, "texture": 2.0, "desc": "极致画质"},
            "high": {"poly": 1.2, "texture": 1.5, "desc": "高画质"},
            "medium": {"poly": 1.0, "texture": 1.0, "desc": "标准画质"},
            "low": {"poly": 0.6, "texture": 0.7, "desc": "性能优化"},
            "mobile": {"poly": 0.3, "texture": 0.5, "desc": "移动端优化"}
        }
        
        for level, multipliers in quality_levels.items():
            variants[level] = {
                "poly_count": int(base_poly * multipliers["poly"]),
                "texture_size": min(int(base_texture * multipliers["texture"]), 4096),
                "description": multipliers["desc"],
                "lod_count": 4 if level in ["ultra", "high"] else 3 if level == "medium" else 2
            }
        
        return variants
    
    @classmethod
    def get_recommended_presets(cls) -> List[Dict[str, Any]]:
        """获取推荐预设组合"""
        recommendations = [
            {
                "name": "🎮 新手推荐",
                "config": (GameType.INDIE_PC, ModelPurpose.PROPS, QualityTier.PRODUCTION),
                "description": "最适合初学者的配置"
            },
            {
                "name": "📱 手游爆款",
                "config": (GameType.MOBILE, ModelPurpose.MAIN_CHARACTER, QualityTier.PRODUCTION),
                "description": "手机游戏主角模型"
            },
            {
                "name": "🏆 3A品质",
                "config": (GameType.AAA_PC, ModelPurpose.MAIN_CHARACTER, QualityTier.SHOWCASE),
                "description": "最高品质展示模型"
            },
            {
                "name": "⚡ 快速原型",
                "config": (GameType.INDIE_PC, ModelPurpose.PROPS, QualityTier.PROTOTYPE),
                "description": "快速验证想法"
            }
        ]
        
        return recommendations


# 便捷函数
def get_preset_config(game_type: str, purpose: str, quality: str, platform: str = None) -> Dict[str, Any]:
    """获取预设配置的便捷函数"""
    platform_enum = Platform(platform) if platform else None
    return GamePresets.get_combined_config(
        GameType(game_type),
        ModelPurpose(purpose), 
        QualityTier(quality),
        platform_enum
    )