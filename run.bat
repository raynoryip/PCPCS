@echo off
REM PCPCS 啟動腳本 (Windows)

cd /d "%~dp0"

REM 嘗試找到 Python
where python >nul 2>nul
if %errorlevel% equ 0 (
    echo 使用 python 啟動 PCPCS...
    python main.py
    goto :end
)

where python3 >nul 2>nul
if %errorlevel% equ 0 (
    echo 使用 python3 啟動 PCPCS...
    python3 main.py
    goto :end
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    echo 使用 py 啟動 PCPCS...
    py main.py
    goto :end
)

echo 錯誤: 找不到 Python
echo 請安裝 Python 3.7 或更高版本
echo 下載: https://www.python.org/downloads/
pause
exit /b 1

:end
pause
