"""
ModelAI 使用示例
展示如何使用智能3D建模工具的各项功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.generator import ModelGenerator, GenerationConfig
from models.classifier import ModelClassifier, ModelType
from unity_export.exporter import UnityExporter, ExportSettings
from unity_export.formats import ExportFormat
from utils.quality_control import QualityController
from utils.validator import ModelValidator
from utils.performance import PerformanceOptimizer


async def basic_generation_example():
    """基础生成示例"""
    print("🎨 基础生成示例")
    print("-" * 40)
    
    # 1. 创建生成器
    generator = ModelGenerator()
    await generator.initialize()
    
    # 2. 配置生成参数
    config = GenerationConfig(
        quality_level="high",
        target_poly_count=5000,
        seed=42
    )
    
    # 3. 生成模型
    prompt = "一座中世纪城堡，有高塔和厚重的石墙"
    result = await generator.generate_model(
        prompt, 
        ModelType.BUILDING, 
        config
    )
    
    print(f"✅ 生成完成!")
    print(f"   顶点数: {result['metadata']['vertex_count']}")
    print(f"   面数: {result['metadata']['face_count']}")
    
    return result


def classification_example():
    """分类示例"""
    print("\n🔍 智能分类示例")
    print("-" * 40)
    
    classifier = ModelClassifier()
    
    test_prompts = [
        "一棵巨大的橡树",
        "勇敢的骑士战士",
        "现代跑车",
        "简单的木桌",
        "锋利的宝剑"
    ]
    
    for prompt in test_prompts:
        result = classifier.classify(prompt)
        print(f"'{prompt}'")
        print(f"  -> {result.model_type.value} (置信度: {result.confidence:.2f})")
        if result.alternative_types:
            alt = result.alternative_types[0]
            print(f"  备选: {alt[0].value} ({alt[1]:.2f})")
        print()


def quality_control_example(model_data):
    """质量控制示例"""
    if not model_data:
        return
        
    print("🎯 质量控制示例")
    print("-" * 40)
    
    # 质量评估
    quality_controller = QualityController()
    metrics = quality_controller.evaluate_model(
        model_data["mesh"],
        model_data["model_type"],
        "high"
    )
    
    print(f"总体评分: {metrics.overall_score:.1f}")
    print(f"质量等级: {metrics.get_quality_level().value}")
    print(f"几何质量: {metrics.geometry_score:.1f}")
    print(f"拓扑质量: {metrics.topology_score:.1f}")
    print(f"Unity就绪度: {metrics.unity_readiness:.1f}")
    
    if metrics.issues:
        print("\n⚠️ 发现的问题:")
        for issue in metrics.issues[:3]:  # 显示前3个问题
            print(f"  - {issue}")
    
    if metrics.suggestions:
        print("\n💡 改进建议:")
        for suggestion in metrics.suggestions[:3]:  # 显示前3个建议
            print(f"  - {suggestion}")


def validation_example(model_data):
    """验证示例"""
    if not model_data:
        return
        
    print("\n🔬 模型验证示例")
    print("-" * 40)
    
    validator = ModelValidator()
    validation_result = validator.validate_model(
        model_data["mesh"],
        model_data["model_type"],
        strict_mode=False
    )
    
    print(f"验证结果: {'✅ 通过' if validation_result.is_valid else '❌ 未通过'}")
    print(f"警告: {validation_result.warnings_count}")
    print(f"错误: {validation_result.errors_count}")
    print(f"严重问题: {validation_result.critical_count}")
    
    if validation_result.can_auto_fix():
        print("🔧 可以自动修复部分问题")
    
    # 显示部分问题
    critical_issues = validation_result.get_issues_by_severity(
        validation_result.get_issues_by_severity
    )
    
    if validation_result.issues:
        print("\n主要问题:")
        for issue in validation_result.issues[:3]:
            emoji = {"warning": "⚠️", "error": "❌", "critical": "🔥", "info": "ℹ️"}
            print(f"  {emoji.get(issue.severity.value, '•')} {issue.message}")


def export_example(model_data):
    """导出示例"""
    if not model_data:
        return
        
    print("\n📦 Unity导出示例")
    print("-" * 40)
    
    # 创建导出器
    exporter = UnityExporter()
    
    # 配置导出设置
    export_settings = ExportSettings(
        format=ExportFormat.OBJ,
        generate_lods=True,
        generate_colliders=True,
        generate_prefab=True,
        optimize_for_unity=True
    )
    
    # 导出模型
    output_dir = Path("./example_output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        unity_asset = exporter.export_model(
            model_data["mesh"],
            output_dir,
            "example_castle",
            model_data["model_type"],
            export_settings
        )
        
        print(f"✅ 导出完成!")
        print(f"   输出目录: {unity_asset.asset_directory}")
        print(f"   文件数: {unity_asset.get_file_count()}")
        print(f"   总大小: {unity_asset.get_total_size() / 1024:.1f} KB")
        
        # 显示生成的文件
        print("\n生成的文件:")
        print(f"  📄 主模型: {unity_asset.main_model_path.name}")
        
        if unity_asset.lod_paths:
            print(f"  📊 LOD文件: {len(unity_asset.lod_paths)} 个")
        
        if unity_asset.collider_path:
            print(f"  🔲 碰撞器: {unity_asset.collider_path.name}")
        
        if unity_asset.material_paths:
            print(f"  🎨 材质: {len(unity_asset.material_paths)} 个")
        
        if unity_asset.prefab_path:
            print(f"  🧩 预制件: {unity_asset.prefab_path.name}")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")


async def performance_optimization_example():
    """性能优化示例"""
    print("\n⚡ 性能优化示例")
    print("-" * 40)
    
    # 创建性能优化器
    optimizer = PerformanceOptimizer()
    
    # 示例prompts和类型
    test_prompts = [
        "一座现代办公楼",
        "一棵樱花树",
        "一个机器人角色"
    ]
    
    test_types = [
        ModelType.BUILDING,
        ModelType.TREE,
        ModelType.CHARACTER
    ]
    
    # 创建生成器
    generator = ModelGenerator()
    await generator.initialize()
    
    print("🔍 分析生成管道性能...")
    
    # 性能分析
    profiling_results = optimizer.profile_generation_pipeline(
        generator, test_prompts, test_types
    )
    
    if "bottlenecks" in profiling_results and profiling_results["bottlenecks"]:
        print("发现的性能瓶颈:")
        for bottleneck in profiling_results["bottlenecks"][:3]:
            print(f"  - {bottleneck['function']}: {bottleneck['cumulative_time']:.2f}s")
    
    # 获取优化建议
    from utils.performance import PerformanceMetrics
    
    # 模拟一些性能指标
    mock_metrics = PerformanceMetrics(
        generation_time=45.0,
        memory_usage=6000.0,
        gpu_memory_usage=2000.0,
        cpu_usage=75.0,
        throughput=0.15,
        quality_score=85.0,
        efficiency_score=1.2
    )
    
    recommendations = optimizer.get_optimization_recommendations(mock_metrics)
    
    if recommendations:
        print("\n💡 优化建议:")
        for rec in recommendations:
            print(f"  - {rec}")


def batch_generation_example():
    """批量生成示例"""
    print("\n🔄 批量生成示例")
    print("-" * 40)
    
    # 批量提示
    batch_prompts = [
        ("一个简单的小屋", ModelType.BUILDING),
        ("一棵柳树", ModelType.TREE),
        ("一把长剑", ModelType.WEAPON),
        ("一辆自行车", ModelType.VEHICLE),
        ("一个花瓶", ModelType.DECORATION)
    ]
    
    print(f"准备生成 {len(batch_prompts)} 个模型...")
    
    # 这里只是演示，实际中会调用批量生成功能
    for i, (prompt, model_type) in enumerate(batch_prompts, 1):
        print(f"  {i}. {prompt} ({model_type.value})")
    
    print("💡 提示: 使用 generator.batch_generate() 进行实际批量生成")


async def complete_workflow_example():
    """完整工作流示例"""
    print("\n🚀 完整工作流示例")
    print("=" * 50)
    
    # 1. 生成模型
    model_data = await basic_generation_example()
    
    # 2. 分类演示
    classification_example()
    
    # 3. 质量控制
    quality_control_example(model_data)
    
    # 4. 模型验证
    validation_example(model_data)
    
    # 5. 导出Unity资产
    export_example(model_data)
    
    # 6. 性能优化
    await performance_optimization_example()
    
    # 7. 批量生成演示
    batch_generation_example()
    
    print("\n🎉 完整工作流演示完成!")
    print("\n要运行实际的ModelAI应用，请使用:")
    print("python app.py")


async def main():
    """主函数"""
    print("🎨 ModelAI 使用示例")
    print("=" * 50)
    print("这个示例展示了ModelAI的各项功能")
    print("包括模型生成、分类、质量控制、验证和导出等\n")
    
    try:
        await complete_workflow_example()
    except KeyboardInterrupt:
        print("\n👋 示例演示已停止")
    except Exception as e:
        print(f"\n❌ 运行示例时出错: {e}")
        print("请确保已正确安装所有依赖")


if __name__ == "__main__":
    asyncio.run(main())