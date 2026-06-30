@echo off
chcp 65001 >nul
title Facebook Lead Radar

echo ============================================================
echo    Facebook Lead Radar - 本地运行启动器
echo ============================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 没有找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

if not exist venv (
    echo [1/3] 首次运行，正在创建虚拟环境...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [2/3] 正在安装依赖...
    pip install -e ..\Agent-Reach
) else (
    call venv\Scripts\activate.bat
)

echo [3/3] 启动 Lead Radar...
echo.

:menu
cls
echo ============================================================
echo    Facebook Lead Radar - 主菜单
echo ============================================================
echo.
echo   [1] 检查环境状态 (doctor)
echo   [2] 手动导入帖子评分
echo   [3] 快速评分单条帖子
echo   [4] 自动搜索 Facebook (需 OpenCLI)
echo   [5] 打开报告目录
echo   [0] 退出
echo.
set /p choice=请选择操作 [0-5]: 

if "%choice%"=="1" goto doctor
if "%choice%"=="2" goto manual
if "%choice%"=="3" goto scoreone
if "%choice%"=="4" goto search
if "%choice%"=="5" goto reports
if "%choice%"=="0" goto end

echo 无效选择，请重试
pause
goto menu

:doctor
cls
python lead_radar.py doctor
echo.
pause
goto menu

:manual
cls
echo ============================================================
echo   手动导入模式
echo ============================================================
echo.
echo 请把帖子内容保存到 input_posts.txt 文件中，
echo 然后按任意键继续...
echo.
echo 格式示例：
echo   name: 发帖人
echo   url: https://...
echo   group: 群组名
echo   comments: 5
echo   （空行）
echo   帖子内容...
echo   ---
echo   （下一条）
echo.
if exist input_posts.txt (
    echo 检测到 input_posts.txt，按任意键开始评分...
    pause >nul
    python lead_radar.py manual --file input_posts.txt --show
) else (
    echo 没有找到 input_posts.txt
    echo 正在用示例数据演示...
    pause >nul
    python lead_radar.py manual --file sample_posts.txt --show
)
echo.
pause
goto menu

:scoreone
cls
echo ============================================================
echo   快速评分单条帖子
echo ============================================================
echo.
set /p text=请粘贴帖子内容: 
echo.
python lead_radar.py score-one --text "%text%"
echo.
pause
goto menu

:search
cls
python lead_radar.py search --top 10
echo.
pause
goto menu

:reports
if not exist reports mkdir reports
start reports
goto menu

:end
echo.
echo 再见！
deactivate
timeout /t 1 >nul
