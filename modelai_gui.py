#!/usr/bin/env python3
"""
ModelAI GUI启动脚本
启动PyQt6桌面应用
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.ui.main_window import main
    
    if __name__ == "__main__":
        print("ModelAI 启动中...")
        print("正在初始化PyQt6界面...")
        sys.exit(main())
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装PyQt6: pip install PyQt6")
    sys.exit(1)
except Exception as e:
    print(f"启动失败: {e}")
    sys.exit(1)