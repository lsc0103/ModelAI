"""
基础功能测试
用于验证ModelAI系统的核心功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.generator import ModelGenerator, GenerationConfig
from models.classifier import ModelClassifier, ModelType
from unity_export.exporter import UnityExporter, ExportSettings


async def test_classification():
    """测试模型分类功能"""
    print("🔍 测试模型分类...")
    
    classifier = ModelClassifier()
    
    test_prompts = [
        "一座中世纪城堡",
        "一棵大橡树",
        "一个勇敢的骑士",
        "一辆红色跑车",
        "一把锋利的剑"
    ]
    
    for prompt in test_prompts:
        result = classifier.classify(prompt)
        print(f"  '{prompt}' -> {result.model_type.value} (置信度: {result.confidence:.2f})")
    
    print("✅ 分类测试完成\n")


async def test_generation():
    """测试模型生成功能"""
    print("🎨 测试模型生成...")
    
    generator = ModelGenerator()
    await generator.initialize()
    
    # 简单的生成测试
    config = GenerationConfig(
        quality_level="medium",
        target_poly_count=1000
    )
    
    try:
        result = await generator.generate_model(
            "一个简单的立方体房子",
            ModelType.BUILDING,
            config
        )
        
        print(f"  生成成功!")
        print(f"  顶点数: {result['metadata']['vertex_count']}")
        print(f"  面数: {result['metadata']['face_count']}")
        print("✅ 生成测试完成\n")
        
        return result
        
    except Exception as e:
        print(f"❌ 生成测试失败: {e}\n")
        return None


def test_export(model_data):
    """测试导出功能"""
    if model_data is None:
        print("❌ 跳过导出测试（生成失败）\n")
        return
    
    print("📦 测试Unity导出...")
    
    exporter = UnityExporter()
    
    try:
        # 创建临时输出目录
        output_dir = Path("./test_output")
        output_dir.mkdir(exist_ok=True)
        
        settings = ExportSettings(
            generate_lods=True,
            generate_colliders=True,
            generate_prefab=True
        )
        
        unity_asset = exporter.export_model(
            model_data["mesh"],
            output_dir,
            "test_model",
            ModelType.BUILDING,
            settings
        )
        
        print(f"  导出成功!")
        print(f"  文件数: {unity_asset.get_file_count()}")
        print(f"  总大小: {unity_asset.get_total_size()} 字节")
        print("✅ 导出测试完成\n")
        
    except Exception as e:
        print(f"❌ 导出测试失败: {e}\n")


async def main():
    """主测试函数"""
    print("🚀 ModelAI 基础功能测试")
    print("=" * 40)
    
    # 测试分类
    await test_classification()
    
    # 测试生成
    model_data = await test_generation()
    
    # 测试导出
    test_export(model_data)
    
    print("🎉 所有测试完成!")


if __name__ == "__main__":
    asyncio.run(main())