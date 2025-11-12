@echo off
chcp 65001 >nul
title DeepWiki-Open 停止服务

:: DeepWiki-Open 停止服务脚本 (Windows版本)

echo DeepWiki-Open 停止服务
echo =======================

:: 停止后端服务
echo [信息] 正在停止后端服务 (端口: 8001)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    echo [信息] 终止进程 PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

:: 停止前端服务
echo [信息] 正在停止前端服务 (端口: 3000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    echo [信息] 终止进程 PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

:: 额外清理相关进程
echo [信息] 清理残留进程...

:: 查找并终止Python相关进程
for /f "tokens=2" %%a in ('tasklist ^| findstr "python.exe" ^| findstr "api.main"') do (
    echo [信息] 终止Python进程: %%a
    taskkill /F /PID %%a >nul 2>&1
)

:: 查找并终止Node.js相关进程
for /f "tokens=2" %%a in ('tasklist ^| findstr "node.exe"') do (
    echo [信息] 检查Node.js进程: %%a
    :: 可以选择性终止，避免误关闭其他Node应用
)

:: 清理PID文件
if exist "api\.backend.pid" del "api\.backend.pid" >nul 2>&1
if exist ".frontend.pid" del ".frontend.pid" >nul 2>&1

echo.
echo 🎉 所有服务已停止！
echo.
echo 重新启动请运行: start.bat
echo.

pause