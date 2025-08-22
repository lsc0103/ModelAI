"""
ModelAI 快速启动脚本
一键启动智能3D建模工具
"""

import sys
import subprocess
from pathlib import Path
import platform

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    
    print(f"✅ Python版本: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """检查依赖是否已安装"""
    print("🔍 检查依赖...")
    
    required_packages = [
        "torch", "trimesh", "numpy", "gradio", 
        "fastapi", "uvicorn", "open3d", "scipy"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ 缺少依赖: {', '.join(missing_packages)}")
        print("正在安装缺少的依赖...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✅ 依赖安装完成")
            return True
        except subprocess.CalledProcessError:
            print("❌ 依赖安装失败")
            print("请手动运行: pip install -r requirements.txt")
            return False
    
    print("✅ 所有依赖已满足")
    return True

def check_system_resources():
    """检查系统资源"""
    print("💻 检查系统资源...")
    
    try:
        import psutil
        
        # 检查内存
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        print(f"  💾 内存: {memory_gb:.1f} GB")
        
        if memory_gb < 4:
            print("  ⚠️ 建议至少4GB内存以获得最佳性能")
        
        # 检查磁盘空间
        disk = psutil.disk_usage('.')
        free_gb = disk.free / (1024**3)
        print(f"  💿 可用磁盘空间: {free_gb:.1f} GB")
        
        if free_gb < 2:
            print("  ⚠️ 建议至少2GB磁盘空间")
        
        # 检查GPU
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                print(f"  🎮 GPU: {gpu_name} ({gpu_memory:.1f} GB)")
            else:
                print("  ⚠️ 未检测到CUDA GPU，将使用CPU")
        except ImportError:
            print("  ⚠️ 无法检测GPU")
        
    except ImportError:
        print("  ⚠️ 无法检查系统资源 (缺少psutil)")

def run_basic_test():
    """运行基础测试"""
    print("🧪 运行基础测试...")
    
    try:
        result = subprocess.run([
            sys.executable, "test_basic.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ 基础测试通过")
            return True
        else:
            print("❌ 基础测试失败")
            print("错误输出:")
            print(result.stderr[:500])  # 显示前500个字符
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        return False

def show_usage_guide():
    """显示使用指南"""
    print("\n📚 使用指南")
    print("=" * 40)
    print("1. 启动Web界面:")
    print("   python app.py")
    print()
    print("2. 查看使用示例:")
    print("   python example_usage.py")
    print()
    print("3. 运行基础测试:")
    print("   python test_basic.py")
    print()
    print("4. 自定义配置:")
    print("   python app.py --host 0.0.0.0 --port 8080")
    print()
    print("🌐 默认访问地址: http://127.0.0.1:7860")

def main():
    """主函数"""
    print("🎨 ModelAI 快速启动")
    print("=" * 50)
    
    # 1. 检查Python版本
    if not check_python_version():
        return
    
    print()
    
    # 2. 检查依赖
    if not check_dependencies():
        return
    
    print()
    
    # 3. 检查系统资源
    check_system_resources()
    
    print()
    
    # 4. 询问是否运行测试
    run_test = input("🧪 是否运行基础测试? (y/N): ").lower().strip()
    if run_test in ['y', 'yes']:
        print()
        if not run_basic_test():
            print("⚠️ 测试失败，但仍可以尝试启动应用")
    
    print()
    
    # 5. 询问启动方式
    print("🚀 选择启动方式:")
    print("1. 启动Web界面 (推荐)")
    print("2. 查看使用示例")
    print("3. 显示使用指南")
    print("4. 退出")
    
    while True:
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == "1":
            print("\n🌐 启动Web界面...")
            try:
                subprocess.run([sys.executable, "app.py"])
            except KeyboardInterrupt:
                print("\n👋 应用已停止")
            break
        
        elif choice == "2":
            print("\n📖 运行使用示例...")
            try:
                subprocess.run([sys.executable, "example_usage.py"])
            except KeyboardInterrupt:
                print("\n👋 示例已停止")
            break
        
        elif choice == "3":
            show_usage_guide()
            break
        
        elif choice == "4":
            print("👋 再见!")
            break
        
        else:
            print("❌ 无效选择，请输入1-4")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 快速启动已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("请检查安装和配置是否正确")