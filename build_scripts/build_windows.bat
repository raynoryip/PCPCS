@echo off
REM PCPCS Windows Build Script
REM 此腳本會將 PCPCS 打包成單一 .exe 檔案

echo ============================================
echo   PCPCS Windows Build Script
echo ============================================
echo.

REM 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.7+
    pause
    exit /b 1
)

REM 進入專案目錄
cd /d "%~dp0.."

REM 建立虛擬環境（如果不存在）
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM 啟動虛擬環境
call venv\Scripts\activate.bat

REM 安裝依賴
echo [INFO] Installing dependencies...
pip install --upgrade pip
pip install pyinstaller pillow

REM 打包
echo [INFO] Building PCPCS...
pyinstaller --noconfirm --onefile --windowed ^
    --name "PCPCS" ^
    --icon "assets\icon.ico" ^
    --add-data "assets;assets" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL.Image" ^
    --hidden-import "PIL.ImageTk" ^
    main.py

REM 檢查結果
if exist "dist\PCPCS.exe" (
    echo.
    echo ============================================
    echo   Build Success!
    echo   Output: dist\PCPCS.exe
    echo ============================================
) else (
    echo.
    echo [ERROR] Build failed!
)

pause
