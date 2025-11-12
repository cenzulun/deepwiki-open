#!/bin/bash

# DeepWiki-Open 快速启动脚本 - 修复版本
# 优化处理缺失API密钥的情况

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "   ____             _            _____ _               "
echo "  / ___|  ___ _ __ | | ___ _ _  |_   _(_) __ _  ___ _ __ "
echo "  \___ \ / _ \ '_ \| |/ _ \ '_ \   | | | | '_ \` |/ _ \ '__|"
echo "   ___) |  __/ | | | |  __/ | | |  | | | | | | |  __/ |   "
echo "  |____/ \___|_| |_|_|\___|_| |_|  |_|_|_| |_|\___|_|   "
echo -e "${NC}"
echo -e "${CYAN}DeepWiki-Open 智能文档生成工具 (修复版)${NC}"
echo -e "${YELLOW}=====================================${NC}"

# 切换到项目目录
cd /Users/mac/github-local/deepwiki-open-main

# 检查函数
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 已安装"
        return 0
    else
        echo -e "${RED}✗${NC} $1 未安装"
        return 1
    fi
}

# 停止现有服务
stop_existing_services() {
    echo -e "${YELLOW}正在停止现有服务...${NC}"

    # 强制停止端口进程
    pkill -f "api.main" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true

    sleep 2
    echo -e "${GREEN}✓ 现有服务已停止${NC}"
}

# 检查依赖
check_dependencies() {
    echo -e "${YELLOW}检查系统依赖...${NC}"

    if ! check_command python3; then
        echo -e "${RED}错误: Python3 未安装${NC}"
        exit 1
    fi

    if ! check_command node; then
        echo -e "${RED}错误: Node.js 未安装${NC}"
        exit 1
    fi

    if ! check_command npm; then
        echo -e "${RED}错误: npm 未安装${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ 系统依赖检查通过${NC}"
}

# 设置环境
setup_environment() {
    echo -e "${YELLOW}检查环境配置...${NC}"

    # 确保日志目录存在
    mkdir -p api/logs

    # 检查.env文件
    if [ -f ".env" ]; then
        echo -e "${GREEN}✓ .env 文件存在${NC}"

        # 读取关键配置
        source .env

        # 检查关键配置项
        if [ "$SKIP_EMBEDDING" = "true" ] && [ "$DEEPWIKI_EMBEDDER_TYPE" = "mock" ]; then
            echo -e "${GREEN}✓ 已启用模拟嵌入模式${NC}"
        else
            echo -e "${YELLOW}注意: 未启用模拟模式，可能需要API密钥${NC}"
        fi

        if [ "$DEEPSEEK_API_KEY" ] && [ "$DEEPSEEK_API_KEY" != "" ]; then
            echo -e "${GREEN}✓ 找到DeepSeek API密钥${NC}"
        fi
    else
        echo -e "${RED}警告: .env 文件不存在${NC}"
        echo -e "${YELLOW}从示例文件复制...${NC}"
        cp .env.example .env 2>/dev/null || echo "警告: .env.example 不存在"
    fi
}

# 安装依赖
install_dependencies() {
    echo -e "${YELLOW}检查并安装依赖...${NC}"

    # 前端依赖
    if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
        echo -e "${BLUE}安装前端依赖...${NC}"
        npm install
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 前端依赖安装完成${NC}"
        else
            echo -e "${RED}前端依赖安装失败${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ 前端依赖已存在${NC}"
    fi

    # 后端依赖
    if [ -f "api/pyproject.toml" ] && command -v poetry &> /dev/null; then
        echo -e "${BLUE}使用Poetry安装后端依赖...${NC}"
        poetry install -C api --no-dev
    else
        echo -e "${BLUE}使用pip安装后端依赖...${NC}"
        pip3 install -r api/requirements.txt 2>/dev/null || pip3 install -e api/
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 后端依赖安装完成${NC}"
    else
        echo -e "${YELLOW}警告: 后端依赖安装可能有问题，但继续尝试启动${NC}"
    fi
}

# 启动后端服务
start_backend() {
    echo -e "${BLUE}启动后端服务...${NC}"

    # 确保Python路径正确
    export PYTHONPATH="/Users/mac/github-local/deepwiki-open-main:$PYTHONPATH"

    # 启动后端
    python3 -m api.main > api/logs/backend.log 2>&1 &
    BACKEND_PID=$!

    # 等待启动
    sleep 8

    # 检查启动状态
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${GREEN}✓ 后端服务启动 (PID: $BACKEND_PID)${NC}"
        echo $BACKEND_PID > api/.backend.pid

        # 尝试健康检查
        for i in {1..10}; do
            if curl -s http://localhost:8001/health > /dev/null 2>&1; then
                echo -e "${GREEN}✓ 后端健康检查通过${NC}"
                break
            fi
            if [ $i -eq 10 ]; then
                echo -e "${YELLOW}警告: 后端健康检查失败，但服务可能仍在启动${NC}"
            fi
            sleep 1
        done
    else
        echo -e "${RED}✗ 后端服务启动失败${NC}"
        echo -e "${RED}查看日志: tail -f api/logs/backend.log${NC}"
        exit 1
    fi
}

# 启动前端服务
start_frontend() {
    echo -e "${BLUE}启动前端服务...${NC}"

    # 启动前端
    npm run dev > /dev/null 2>&1 &
    FRONTEND_PID=$!

    # 等待启动
    sleep 10

    # 检查启动状态
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${GREEN}✓ 前端服务启动 (PID: $FRONTEND_PID)${NC}"
        echo $FRONTEND_PID > .frontend.pid

        # 尝试连接检查
        for i in {1..15}; do
            if curl -s http://localhost:3000 > /dev/null 2>&1; then
                echo -e "${GREEN}✓ 前端连接检查通过${NC}"
                break
            fi
            if [ $i -eq 15 ]; then
                echo -e "${YELLOW}警告: 前端连接检查失败，但服务可能仍在启动${NC}"
            fi
            sleep 1
        done
    else
        echo -e "${RED}✗ 前端服务启动失败${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
}

# 显示启动信息
show_startup_info() {
    echo ""
    echo -e "${GREEN}🎉 DeepWiki-Open 启动成功！${NC}"
    echo -e "${YELLOW}=====================================${NC}"
    echo -e "${CYAN}📱 前端应用: http://localhost:3000${NC}"
    echo -e "${CYAN}🔧 后端API:  http://localhost:8001${NC}"
    echo -e "${CYAN}📊 健康检查: http://localhost:8001/health${NC}"
    echo ""
    echo -e "${YELLOW}📖 功能说明:${NC}"
    echo -e "${BLUE}• 支持本地路径: /path/to/project${NC}"
    echo -e "${BLUE}• 支持GitHub仓库: owner/repo${NC}"
    if [ "$SKIP_EMBEDDING" = "true" ]; then
        echo -e "${GREEN}• 当前运行模式: 模拟嵌入 (无需API密钥)${NC}"
    else
        echo -e "${YELLOW}• 当前运行模式: 标准嵌入 (需要API密钥)${NC}"
    fi
    echo ""
    echo -e "${YELLOW}🛑 停止服务:${NC}"
    echo -e "${BLUE}• 按 Ctrl+C 停止所有服务${NC}"
    echo -e "${BLUE}• 或运行: ./stop.sh${NC}"
    echo ""
    echo -e "${GREEN}📚 查看日志:${NC}"
    echo -e "${BLUE}• 后端: tail -f api/logs/backend.log${NC}"
    echo ""
}

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}正在停止服务...${NC}"

    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    # 清理PID文件
    rm -f api/.backend.pid .frontend.pid

    # 强制清理端口
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true

    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}

# 设置信号处理
trap cleanup INT TERM

# 主执行流程
main() {
    echo -e "${BLUE}开始启动 DeepWiki-Open...${NC}"
    echo ""

    stop_existing_services
    echo ""

    check_dependencies
    echo ""

    setup_environment
    echo ""

    install_dependencies
    echo ""

    start_backend
    echo ""

    start_frontend
    echo ""

    show_startup_info

    # 等待用户中断
    echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
    while true; do
        sleep 1
    done
}

# 执行主函数
main