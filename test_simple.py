"""
简化版多AI服务测试脚本
验证OpenAI和Claude API的混合使用
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.api.multi_ai_client import get_multi_ai_client, AIRequest, AIService
    from src.config.settings import settings
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所需依赖: pip install openai anthropic loguru pydantic-settings")
    sys.exit(1)


async def test_basic_functionality():
    """测试基础功能"""
    print("ModelAI 多AI服务测试")
    print("=" * 40)
    
    # 检查配置
    print(f"OpenAI API Key: {'已配置' if settings.openai_api_key else '未配置'}")
    print(f"Claude API Key: {'已配置' if settings.claude_api_key else '未配置'}")
    print(f"主要服务: {settings.primary_ai_service}")
    
    try:
        # 初始化客户端
        print("\n初始化多AI客户端...")
        client = get_multi_ai_client()
        
        # 检查可用服务
        available_services = client.get_available_services()
        print(f"可用服务: {[s.value for s in available_services]}")
        
        if not available_services:
            print("错误: 没有可用的AI服务")
            return False
        
        # 测试连接
        print("\n测试连接...")
        connections = await client.test_all_connections()
        for service, success in connections.items():
            status = "成功" if success else "失败"
            print(f"  {service}: {status}")
        
        # 发送测试消息
        print("\n发送测试消息...")
        request = AIRequest(
            messages=[{
                "role": "user",
                "content": "你好！请用中文简短回复，说明你是哪个AI模型。"
            }],
            max_tokens=100,
            temperature=0.3
        )
        
        response = await client.send_message(request, "test")
        
        print(f"成功! 使用服务: {response.service.value}")
        print(f"模型: {response.model}")
        print(f"回复: {response.content}")
        print(f"Token使用: {response.usage}")
        print(f"处理时间: {response.processing_time:.2f}s")
        
        # 模拟3D建模对话
        print("\n模拟3D建模对话...")
        modeling_request = AIRequest(
            messages=[{
                "role": "user",
                "content": "我想生成一个简单的房子3D模型。请作为主协调Agent分析这个需求。"
            }],
            system="你是ModelAI的主协调Agent，负责分析3D建模需求并制定制作计划。",
            max_tokens=500,
            temperature=0.5
        )
        
        modeling_response = await client.send_message(
            modeling_request, 
            "master_coordinator"
        )
        
        print(f"主协调Agent响应 (使用: {modeling_response.service.value}):")
        print(modeling_response.content)
        
        # 显示统计
        print("\n统计信息:")
        stats = client.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n测试成功! 多AI系统工作正常")
        print("\n下一步可以开始:")
        print("- 实现专业化Agent")
        print("- 开发PyQt6界面")
        print("- 集成3D生成工具")
        
        return True
        
    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_basic_functionality())
        if success:
            print("\n[SUCCESS] 所有功能正常!")
        else:
            print("\n[FAILED] 存在问题，请检查配置")
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n出现错误: {str(e)}")
        print("请检查依赖安装和网络连接")