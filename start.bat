@echo off
chcp 65001 >nul
title 仓库热力图系统 - 启动管理

:: 获取本机局域网 IP 地址
set LOCAL_IP=未检测到
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do (
        echo %%b | findstr "^192\. ^10\. ^172\." >nul && set LOCAL_IP=%%b
    )
)

:menu
cls
echo ========================================
echo    仓库热力图系统 - 启动管理
echo ========================================
echo.
echo   本机 IP: %LOCAL_IP%
echo.
echo   [1] 一键启动前后端
echo   [2] 仅启动后端
echo   [3] 仅启动前端
echo   [4] 停止所有服务
echo   [5] 初始化环境（首次使用）
echo   [0] 退出
echo.
echo ========================================
echo.

set /p choice=请选择操作 [0-5]: 

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto start_backend
if "%choice%"=="3" goto start_frontend
if "%choice%"=="4" goto stop_all
if "%choice%"=="5" goto setup
if "%choice%"=="0" goto end
goto menu

:start_all
cls
echo ========================================
echo    启动前后端服务
echo ========================================
echo.

:: 启动后端
echo [INFO] 启动后端服务...
start "后端服务 - 仓库热力图" cmd /k "cd /d %~dp0backend && (if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat) && python main.py"

timeout /t 2 /nobreak >nul

:: 启动前端
echo [INFO] 启动前端服务...
start "前端服务 - 仓库热力图" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo [SUCCESS] 服务启动完成！
echo ========================================
echo.
echo   本机访问:
echo     前端页面: http://localhost:5173
echo     API 文档: http://localhost:8000/docs
echo.
echo   局域网访问 (告诉同事这个地址):
echo     前端页面: http://%LOCAL_IP%:5173
echo     后端 API: http://%LOCAL_IP%:8000
echo ========================================
echo.
pause
goto menu

:start_backend
cls
echo ========================================
echo    启动后端服务
echo ========================================
echo.

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    echo [INFO] 激活虚拟环境...
    call venv\Scripts\activate.bat
)

:: 检查依赖
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [INFO] 安装依赖...
    pip install -r requirements.txt
)

echo.
echo   本机访问: http://localhost:8000
echo   局域网:   http://%LOCAL_IP%:8000
echo   API文档:  http://localhost:8000/docs
echo.
echo [INFO] 按 Ctrl+C 停止服务
echo ========================================
echo.

python main.py
goto menu

:start_frontend
cls
echo ========================================
echo    启动前端服务
echo ========================================
echo.

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [INFO] 安装依赖...
    call npm install
)

echo.
echo   本机访问: http://localhost:5173
echo   局域网:   http://%LOCAL_IP%:5173
echo.
echo [INFO] 按 Ctrl+C 停止服务
echo ========================================
echo.

call npm run dev
goto menu

:stop_all
cls
echo ========================================
echo    停止所有服务
echo ========================================
echo.

echo [INFO] 停止后端服务 (端口 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a 2>nul && echo   已停止 PID: %%a
)

echo [INFO] 停止前端服务 (端口 5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a 2>nul && echo   已停止 PID: %%a
)

echo.
echo [SUCCESS] 服务已停止
echo.
pause
goto menu

:setup
cls
echo ========================================
echo    初始化开发环境
echo ========================================
echo.

:: 检查 Python
echo [检查] Python...
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python 未安装，请先安装 Python 3.8+
    pause
    goto menu
)

:: 检查 Node.js
echo [检查] Node.js...
node --version 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js 未安装，请先安装 Node.js 16+
    pause
    goto menu
)

echo.
echo [后端] 设置 Python 环境...
cd /d "%~dp0backend"

if not exist "venv" (
    echo [INFO] 创建虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo [INFO] 安装 Python 依赖...
pip install -r requirements.txt -q

if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] 创建 .env 配置文件...
        copy .env.example .env >nul
    )
)

echo.
echo [前端] 设置 Node.js 环境...
cd /d "%~dp0frontend"
echo [INFO] 安装 Node.js 依赖...
call npm install

echo.
echo ========================================
echo [SUCCESS] 环境初始化完成！
echo ========================================
echo.
pause
goto menu

:end
exit /b 4


4
4


