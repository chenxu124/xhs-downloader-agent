# 自动打包脚本
# 使用方式: python build_exe.py

import os
import sys
import subprocess
from pathlib import Path

def check_pyinstaller():
    """检查PyInstaller是否安装"""
    try:
        import PyInstaller
        print("✓ PyInstaller已安装")
        return True
    except ImportError:
        print("✗ PyInstaller未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def build_exe():
    """生成exe文件"""
    project_dir = Path(__file__).parent
    script_file = project_dir / "xhs_agent_batch_video.py"
    
    if not script_file.exists():
        print(f"✗ 找不到脚本: {script_file}")
        return False
    
    print(f"\n开始打包: {script_file.name}")
    print("-" * 50)
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        f"--name=xhs_agent",
        f"--distpath={project_dir}/dist",
        f"--buildpath={project_dir}/build",
        f"--specpath={project_dir}",
        str(script_file)
    ]
    
    try:
        result = subprocess.run(cmd, cwd=str(project_dir), check=True)
        exe_path = project_dir / "dist" / "xhs_agent.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n✓ 打包成功!")
            print(f"  输出文件: {exe_path}")
            print(f"  文件大小: {size_mb:.1f} MB")
            print(f"\n快速开始:")
            print(f"  {exe_path} --help")
            return True
        else:
            print(f"✗ 生成失败: {exe_path} 不存在")
            return False
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        return False

def cleanup_build():
    """清理构建文件"""
    project_dir = Path(__file__).parent
    for item in ["build", "xhs_agent.spec"]:
        path = project_dir / item
        if path.exists():
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
            else:
                path.unlink()
    print("✓ 已清理构建文件")

if __name__ == "__main__":
    print("XHS Downloader Agent - 自动打包工具")
    print("=" * 50)
    
    if not check_pyinstaller():
        sys.exit(1)
    
    if not build_exe():
        sys.exit(1)
    
    cleanup_build()
    print("\n完成! 可执行文件已生成在dist/目录")
