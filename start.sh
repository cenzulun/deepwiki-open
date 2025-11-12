#!/bin/bash

# DeepWiki-Open 一键启动脚本
# 支持本地路径解析和国产AI模型的智能文档生成工具

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logo和欢迎信息
echo -e "${BLUE}"
echo "   ____             _            _____ _               "
echo "  / ___|  ___ _ __ | | ___ _ _  |_   _(_) __ _  ___ _ __ "
echo "  \___ \ / _ \ '_ \| |/ _ \ '_ \   | | | | '_ \` |/ _ \ '__|"
echo "   ___) |  __/ | | | |  __/ | | |  | | | | | | |  __/ |   "
echo "  |____/ \___|_| |_|_|\___|_| |_|  |_|_|_| |_|\___|_|   "
echo -e "${NC}"
echo -e "${CYAN}DeepWiki-Open 智能文档生成工具${NC}"
echo -e "${CYAN}支持本地路径解析 + 国产AI模型${NC}"
echo -e "${YELLOW}=====================================${NC}"

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

# 安装依赖函数
install_dependencies() {
    echo -e "${YELLOW}正在检查和安装依赖...${NC}"

    # 检查Python
    if ! check_command python3; then
        echo -e "${RED}错误: Python3 未安装，请先安装Python3${NC}"
        exit 1
    fi

    # 检查Node.js
    if ! check_command node; then
        echo -e "${RED}错误: Node.js 未安装，请先安装Node.js${NC}"
        exit 1
    fi

    # 检查npm
    if ! check_command npm; then
        echo -e "${RED}错误: npm 未安装，请先安装npm${NC}"
        exit 1
    fi

    echo -e "${GREEN}基础环境检查通过！${NC}"
}

# 设置环境变量
setup_environment() {
    echo -e "${YELLOW}正在设置环境变量...${NC}"

    # 如果.env文件不存在，从示例复制
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${GREEN}✓ 已创建 .env 文件${NC}"
            echo -e "${YELLOW}请编辑 .env 文件，添加您的API密钥：${NC}"
            echo -e "${YELLOW}- ZHIPUAI_API_KEY=your_zhipuai_api_key (智谱AI)${NC}"
            echo -e "${YELLOW}- DEEPSEEK_API_KEY=your_deepseek_api_key (DeepSeek)${NC}"
            echo -e "${YELLOW}- ENABLE_CHINESE_MODELS=true${NC}"
            echo ""
            read -p "按回车键继续..." -r
        else
            echo -e "${YELLOW}警告: .env.example 文件不存在${NC}"
        fi
    else
        echo -e "${GREEN}✓ .env 文件已存在${NC}"
    fi
}

# 安装前端依赖
install_frontend_deps() {
    echo -e "${YELLOW}正在安装前端依赖...${NC}"

    if [ ! -d "node_modules" ]; then
        npm install
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 前端依赖安装完成${NC}"
        else
            echo -e "${RED}前端依赖安装失败${NC}"
            return 1
        fi
    else
        echo -e "${GREEN}✓ 前端依赖已存在${NC}"
    fi
}

# 安装后端依赖
install_backend_deps() {
    echo -e "${YELLOW}正在安装后端依赖...${NC}"

    # 优先使用poetry
    if check_command poetry; then
        echo -e "${BLUE}使用 Poetry 安装后端依赖...${NC}"
        poetry install -C api
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 后端依赖安装完成 (Poetry)${NC}"
            return 0
        fi
    fi

    # 备选方案：使用pip
    if check_command pip3; then
        echo -e "${BLUE}使用 pip 安装后端依赖...${NC}"
        pip3 install -r api/requirements.txt 2>/dev/null || pip3 install -e api/
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 后端依赖安装完成 (pip)${NC}"
            return 0
        fi
    fi

    echo -e "${YELLOW}⚠️ 无法自动安装后端依赖，请手动安装${NC}"
    return 1
}

# 启动服务
start_services() {
    echo -e "${YELLOW}正在启动服务...${NC}"

    # 创建日志目录
    mkdir -p api/logs

    # 检查端口占用
    FRONTEND_PORT=3000
    BACKEND_PORT=8001

    if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}前端端口 $FRONTEND_PORT 已被占用，尝试终止现有进程...${NC}"
        lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null
        sleep 2
    fi

    if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}后端端口 $BACKEND_PORT 已被占用，尝试终止现有进程...${NC}"
        lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null
        sleep 2
    fi

    echo -e "${GREEN}✓ 端口检查完成${NC}"

    # 启动后端服务
    echo -e "${BLUE}启动后端服务 (端口: $BACKEND_PORT)...${NC}"
    if check_command poetry && [ -f "api/pyproject.toml" ]; then
        # 使用poetry启动
        poetry run -C api python -m api.main > api/logs/backend.log 2>&1 &
        BACKEND_PID=$!
    else
        # 使用python直接启动
        python3 -m api.main > api/logs/backend.log 2>&1 &
        BACKEND_PID=$!
    fi

    # 等待后端启动
    sleep 5

    # 检查后端是否启动成功
    if curl -s http://localhost:$BACKEND_PORT/health > /dev/null; then
        echo -e "${GREEN}✓ 后端服务启动成功 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${RED}✗ 后端服务启动失败，请检查日志: api/logs/backend.log${NC}"
        kill $BACKEND_PID 2>/dev/null
        return 1
    fi

    # 启动前端服务
    echo -e "${BLUE}启动前端服务 (端口: $FRONTEND_PORT)...${NC}"
    npm run dev > /dev/null 2>&1 &
    FRONTEND_PID=$!

    # 等待前端启动
    sleep 8

    # 检查前端是否启动成功
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null; then
        echo -e "${GREEN}✓ 前端服务启动成功 (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${RED}✗ 前端服务启动失败${NC}"
        kill $FRONTEND_PID 2>/dev/null
        kill $BACKEND_PID 2>/dev/null
        return 1
    fi

    # 保存PID到文件
    echo "$BACKEND_PID" > api/.backend.pid
    echo "$FRONTEND_PID" > .frontend.pid

    return 0
}

# 显示状态信息
show_status() {
    echo ""
    echo -e "${GREEN}🎉 DeepWiki-Open 启动成功！${NC}"
    echo -e "${YELLOW}=====================================${NC}"
    echo -e "${CYAN}📱 前端应用: http://localhost:3000${NC}"
    echo -e "${CYAN}🔧 后端API:  http://localhost:8001${NC}"
    echo -e "${CYAN}📊 健康检查: http://localhost:8001/health${NC}"
    echo ""
    echo -e "${YELLOW}📖 新功能使用指南:${NC}"
    echo -e "${BLUE}• 本地路径格式: /path/to/project 或 ./api${NC}"
    echo -e "${BLUE}• 您的特殊格式: mac/github-local/project-name${NC}"
    echo -e "${BLUE}• 国产模型: 需要在.env中配置相应API密钥${NC}"
    echo ""
    echo -e "${YELLOW}🛑 停止服务:${NC}"
    echo -e "${BLUE}• 前端: Ctrl+C 或 ./stop.sh${NC}"
    echo -e "${BLUE}• 后端: Ctrl+C 或 kill $BACKEND_PID${NC}"
    echo ""
    echo -e "${GREEN}📚 查看日志:${NC}"
    echo -e "${BLUE}• 后端日志: tail -f api/logs/backend.log${NC}"
    echo ""
}

# 主函数
main() {
    echo -e "${BLUE}开始启动 DeepWiki-Open...${NC}"
    echo ""

    # 安装依赖
    install_dependencies
    echo ""

    # 设置环境
    setup_environment
    echo ""

    # 安装前端依赖
    install_frontend_deps
    echo ""

    # 安装后端依赖
    install_backend_deps
    echo ""

    # 启动服务
    if start_services; then
        show_status

        # 等待用户停止
        echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"

        # 等待中断信号
        trap 'echo -e "\n${YELLOW}正在停止服务...${NC}"; kill $FRONTEND_PID $BACKEND_PID 2>/dev/null; echo -e "${GREEN}服务已停止${NC}"; exit 0' INT

        # 保持脚本运行
        while true; do
            sleep 1
        done
    else
        echo -e "${RED}启动失败，请检查错误信息${NC}"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo -e "${BLUE}DeepWiki-Open 一键启动脚本${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start     启动服务 (默认)"
    echo "  stop      停止服务"
    echo "  status    查看服务状态"
    echo "  restart   重启服务"
    echo "  logs      查看日志"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0          # 启动服务"
    echo "  $0 stop     # 停止服务"
    echo "  $0 status   # 查看状态"
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}正在停止服务...${NC}"

    # 停止后端
    if [ -f "api/.backend.pid" ]; then
        BACKEND_PID=$(cat api/.backend.pid)
        kill $BACKEND_PID 2>/dev/null
        rm api/.backend.pid
        echo -e "${GREEN}✓ 后端服务已停止${NC}"
    fi

    # 停止前端
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        kill $FRONTEND_PID 2>/dev/null
        rm .frontend.pid
        echo -e "${GREEN}✓ 前端服务已停止${NC}"
    fi

    # 强制停止端口进程
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    lsof -ti:8001 | xargs kill -9 2>/dev/null

    echo -e "${GREEN}所有服务已停止${NC}"
}

# 查看状态
check_status() {
    echo -e "${BLUE}检查服务状态...${NC}"

    # 检查后端
    if curl -s http://localhost:8001/health > /dev/null; then
        echo -e "${GREEN}✓ 后端服务运行中 (http://localhost:8001)${NC}"
    else
        echo -e "${RED}✗ 后端服务未运行${NC}"
    fi

    # 检查前端
    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✓ 前端服务运行中 (http://localhost:3000)${NC}"
    else
        echo -e "${RED}✗ 前端服务未运行${NC}"
    fi
}

# 查看日志
show_logs() {
    echo -e "${BLUE}显示日志...${NC}"
    echo -e "${YELLOW}后端日志:${NC}"
    if [ -f "api/logs/backend.log" ]; then
        tail -f api/logs/backend.log
    else
        echo -e "${RED}后端日志文件不存在${NC}"
    fi
}

# 处理命令行参数
case "${1:-start}" in
    start)
        main
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        main
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}未知选项: $1${NC}"
        show_help
        exit 1
        ;;
esac