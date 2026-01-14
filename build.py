#!/usr/bin/env python3
"""
PCPCS 跨平台打包腳本
自動檢測系統並打包成可執行檔

使用方式:
    python build.py           # 自動打包
    python build.py --clean   # 清理之前的建置
"""
import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.absolute()


def print_header():
    print("=" * 50)
    print("  PCPCS Cross-Platform Build Tool")
    print("=" * 50)
    print(f"  Platform: {platform.system()} {platform.machine()}")
    print(f"  Python: {sys.version.split()[0]}")
    print("=" * 50)
    print()


def check_dependencies():
    """檢查並安裝必要的依賴"""
    print("[INFO] Checking dependencies...")

    # 檢查 pip
    try:
        import pip
    except ImportError:
        print("[ERROR] pip not found!")
        return False

    # 安裝 PyInstaller
    try:
        import PyInstaller
        print(f"  - PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        print("  - PyInstaller: Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"],
                      check=True, capture_output=True)
        print("  - PyInstaller: Installed")

    # 安裝 Pillow (可選)
    try:
        import PIL
        print(f"  - Pillow: {PIL.__version__}")
    except ImportError:
        print("  - Pillow: Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pillow"],
                          check=True, capture_output=True)
            print("  - Pillow: Installed")
        except:
            print("  - Pillow: Failed (optional, continuing...)")

    # 檢查 tkinter
    try:
        import tkinter
        print("  - tkinter: OK")
    except ImportError:
        print("[ERROR] tkinter not found!")
        if platform.system() == "Linux":
            print("  Install with: sudo apt install python3-tk")
        return False

    print()
    return True


def clean_build():
    """清理之前的建置"""
    print("[INFO] Cleaning previous builds...")

    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']

    for dir_name in dirs_to_clean:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_name}/")

    for pattern in files_to_clean:
        for file_path in PROJECT_ROOT.glob(pattern):
            file_path.unlink()
            print(f"  Removed: {file_path.name}")

    print()


def build():
    """執行打包"""
    system = platform.system()

    # 基本參數
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--name", "PCPCS",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageTk",
    ]

    # 添加資源檔案
    assets_dir = PROJECT_ROOT / "assets"
    if assets_dir.exists():
        separator = ";" if system == "Windows" else ":"
        args.extend(["--add-data", f"assets{separator}assets"])

    # 平台特定參數
    if system == "Windows":
        args.append("--windowed")  # 無控制台視窗
        icon_path = PROJECT_ROOT / "assets" / "icon.ico"
        if icon_path.exists():
            args.extend(["--icon", str(icon_path)])
    elif system == "Darwin":  # macOS
        args.append("--windowed")
        args.extend(["--osx-bundle-identifier", "com.perspic.pcpcs"])
    # Linux 不需要 --windowed

    # 主程式
    args.append(str(PROJECT_ROOT / "main.py"))

    print(f"[INFO] Building for {system}...")
    print(f"  Command: {' '.join(args[-5:])}")
    print()

    # 執行打包
    result = subprocess.run(args, cwd=PROJECT_ROOT)

    return result.returncode == 0


def post_build():
    """打包後處理"""
    system = platform.system()
    dist_dir = PROJECT_ROOT / "dist"

    if system == "Windows":
        output_file = dist_dir / "PCPCS.exe"
    elif system == "Darwin":
        output_file = dist_dir / "PCPCS.app"
        if not output_file.exists():
            output_file = dist_dir / "PCPCS"
    else:
        output_file = dist_dir / "PCPCS"
        # 確保 Linux 可執行
        if output_file.exists():
            output_file.chmod(0o755)

    if output_file.exists():
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print()
        print("=" * 50)
        print("  BUILD SUCCESS!")
        print("=" * 50)
        print(f"  Output: {output_file}")
        print(f"  Size: {size_mb:.1f} MB")
        print()
        print("  This file can run on any computer without")
        print("  installing Python or any dependencies!")
        print("=" * 50)
        return True
    else:
        print()
        print("[ERROR] Build failed - output file not found")
        return False


def main():
    print_header()

    # 處理命令列參數
    if "--clean" in sys.argv:
        clean_build()
        if len(sys.argv) == 2:  # 只有 --clean
            return

    # 總是先清理
    clean_build()

    # 檢查依賴
    if not check_dependencies():
        print("[ERROR] Dependency check failed!")
        sys.exit(1)

    # 執行打包
    if build():
        post_build()
    else:
        print("[ERROR] Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
