"""
ModelAI 主应用程序
智能3D建模工具的入口点
"""

import asyncio
import argparse
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ui.gradio_interface import GradioInterface


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ModelAI - 智能3D建模工具"
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="服务器主机地址 (默认: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="服务器端口 (默认: 7860)"
    )
    
    parser.add_argument(
        "--share",
        action="store_true",
        help="创建公共链接"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )
    
    args = parser.parse_args()
    
    print("🎨 ModelAI - 智能3D建模工具")
    print("=" * 50)
    print(f"🌐 启动服务器: {args.host}:{args.port}")
    
    if args.share:
        print("🔗 将创建公共分享链接")
    
    if args.debug:
        print("🐛 调试模式已启用")
    
    print("=" * 50)
    
    try:
        # 创建并启动Gradio界面
        interface = GradioInterface()
        interface.launch(
            share=args.share,
            server_name=args.host,
            server_port=args.port,
            debug=args.debug
        )
        
    except KeyboardInterrupt:
        print("\n👋 感谢使用ModelAI！")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()