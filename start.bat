@echo off
chcp 65001 >nul
title DeepWiki-Open 智能文档生成工具

:: DeepWiki-Open 一键启动脚本 (Windows版本)
:: 支持本地路径解析和国产AI模型的智能文档生成工具

echo.
echo    ____             _            _____ _
echo   / ___\  ___ _ __ ^| ^| ___ _ _  ^|_   _(_) __ _  ___ _ __
echo   \___ \ / _ \ '_ \^| ^|/ _ \ '_ \   ^| ^| ^| ^| '_ \` ^|^/ _ \ '__^|
echo    ___) ^|  __/ ^| ^| ^| ^|  __/ ^| ^| ^|  ^| ^| ^| ^| ^| ^|^|  __/ ^|
echo   ^|____/ \___^|_^|_^|_^_^|\___^|_^|_^|_^|^|_^|_^|_^|_^|\___^|_^|
echo.
echo DeepWiki-Open 智能文档生成工具
echo 支持本地路径解析 + 国产AI模型
echo =====================================

:: 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python 未安装，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: 检查Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Node.js 未安装，请先安装 Node.js
    pause
    exit /b 1
)

echo [信息] 基础环境检查通过

:: 检查并设置环境变量
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [成功] 已创建 .env 文件
        echo [提示] 请编辑 .env 文件，添加您的API密钥：
        echo        - ZHIPUAI_API_KEY=your_zhipuai_api_key (智谱AI)
        echo        - DEEPSEEK_API_KEY=your_deepseek_api_key (DeepSeek)
        echo        - ENABLE_CHINESE_MODELS=true
        echo.
        pause
    ) else (
        echo [警告] .env.example 文件不存在
    )
) else (
    echo [成功] .env 文件已存在
)

:: 创建日志目录
if not exist "api\logs" mkdir "api\logs"

:: 安装前端依赖
if not exist "node_modules" (
    echo [信息] 正在安装前端依赖...
    npm install
    if %errorlevel% neq 0 (
        echo [错误] 前端依赖安装失败
        pause
        exit /b 1
    )
    echo [成功] 前端依赖安装完成
) else (
    echo [成功] 前端依赖已存在
)

:: 检查并终止占用的端口
echo [信息] 检查端口占用...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: 启动后端服务
echo [信息] 启动后端服务 (端口: 8001)...
start /B python -m api.main > api\logs\backend.log 2>&1
set BACKEND_PID=%errorlevel%

:: 等待后端启动
timeout /t 5 /nobreak >nul

:: 检查后端是否启动成功
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8001/health' -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel% equ 0 (
    echo [成功] 后端服务启动成功
) else (
    echo [错误] 后端服务启动失败，请检查日志: api\logs\backend.log
    pause
    exit /b 1
)

:: 启动前端服务
echo [信息] 启动前端服务 (端口: 3000)...
start /B npm run dev >nul 2>&1
set FRONTEND_PID=%errorlevel%

:: 等待前端启动
timeout /t 8 /nobreak >nul

:: 检查前端是否启动成功
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:3000' -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel% equ 0 (
    echo [成功] 前端服务启动成功
) else (
    echo [错误] 前端服务启动失败
    pause
    exit /b 1
)

:: 显示启动成功信息
echo.
echo 🎉 DeepWiki-Open 启动成功！
echo =====================================
echo 📱 前端应用: http://localhost:3000
echo 🔧 后端API:  http://localhost:8001
echo 📊 健康检查: http://localhost:8001/health
echo.
echo 📖 新功能使用指南:
echo • 本地路径格式: C:\path\to\project 或 .\api
echo • 您的特殊格式: mac/github-local/project-name
echo • 国产模型: 需要在.env中配置相应API密钥
echo.
echo 🛑 停止服务:
echo • 关闭此窗口或按 Ctrl+C
echo.
echo 📚 查看日志:
echo • 后端日志: type api\logs\backend.log
echo.

:: 打开浏览器
start http://localhost:3000

echo [信息] 按任意键停止服务...
pause >nul

:: 停止服务
echo [信息] 正在停止服务...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq api.main*" >nul 2>&1
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *npm*dev*" >nul 2>&1
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *next*" >nul 2>&1

echo [成功] 所有服务已停止
pause