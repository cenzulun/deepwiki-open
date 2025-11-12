#!/bin/bash

# DeepWiki-Open 最终修复版启动脚本
# 解决了所有已知问题的稳定版本

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
echo "  \___ \ / _ \ '_ \| |/ _ \ '_ \   | | | | '_ ` |/ _ \ '__|"
echo "   ___) |  __/ | | | |  __/ | | |  | | | | |  __/ |   "
echo "  |____/ \___|_| |_|_|\___|_| |_|  |_|_|_| |_|\___|_|   "
echo -e "${NC}"
echo -e "${CYAN}DeepWiki-Open 最终修复版启动脚本${NC}"
echo -e "${YELLOW}========================================${NC}"

# 切换到项目目录
cd /Users/mac/github-local/deepwiki-open-main

# 停止所有现有服务
echo -e "${YELLOW}正在停止所有现有服务...${NC}"
pkill -f "api.main" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓ 现有服务已停止${NC}"

# 创建必要目录
mkdir -p api/logs

# 检查并设置环境变量
echo -e "${YELLOW}检查环境配置...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env 文件存在${NC}"
    # 确保关键配置正确
    if ! grep -q "DEEPWIKI_EMBEDDER_TYPE=mock" .env; then
        echo -e "${YELLOW}正在更新配置文件...${NC}"
        sed -i.bak 's/DEEPWIKI_EMBEDDER_TYPE=.*/DEEPWIKI_EMBEDDER_TYPE=mock/' .env
    fi
    if ! grep -q "SKIP_EMBEDDING=true" .env; then
        echo "SKIP_EMBEDDING=true" >> .env
    fi
else
    echo -e "${RED}错误: .env 文件不存在${NC}"
    exit 1
fi

# 验证关键修复文件
echo -e "${YELLOW}验证修复文件...${NC}"

# 检查 MockEmbedderClient 修复
if ! grep -q "_combine_input_and_model_kwargs" api/mock_embedder.py; then
    echo -e "${RED}错误: MockEmbedderClient 修复未应用${NC}"
    exit 1
fi
echo -e "${GREEN}✓ MockEmbedderClient 修复已应用${NC}"

# 检查 DeepSeekClient 修复
if ! grep -q "class DeepSeekClient(ModelClient)" api/deepseek_client.py; then
    echo -e "${RED}错误: DeepSeekClient 修复未应用${NC}"
    exit 1
fi
echo -e "${GREEN}✓ DeepSeekClient 修复已应用${NC}"

# 检查默认提供商配置
if ! grep -q '"default_provider": "deepseek"' api/config/generator.json; then
    echo -e "${RED}错误: 默认提供商配置未更新${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 默认提供商配置已更新${NC}"

# 启动后端服务
echo -e "${YELLOW}启动后端服务...${NC}"
export PYTHONPATH="/Users/mac/github-local/deepwiki-open-main:$PYTHONPATH"
python3 -m api.main > api/logs/backend.log 2>&1 &
BACKEND_PID=$!

# 等待后端启动
sleep 8

# 检查后端状态
if kill -0 $BACKEND_PID 2>/dev/null; then
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务启动成功 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${RED}✗ 后端服务启动失败${NC}"
        tail -10 api/logs/backend.log
        exit 1
    fi
else
    echo -e "${RED}✗ 后端服务进程启动失败${NC}"
    exit 1
fi

# 启动前端服务
echo -e "${YELLOW}启动前端服务...${NC}"
npm run dev > /dev/null 2>&1 &
FRONTEND_PID=$!

# 等待前端启动
sleep 10

# 检查前端状态
if kill -0 $FRONTEND_PID 2>/dev/null; then
    if curl -s -I http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 前端服务启动成功 (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${RED}✗ 前端服务连接失败${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
else
    echo -e "${RED}✗ 前端服务进程启动失败${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 保存进程ID
echo $BACKEND_PID > api/.backend.pid
echo $FRONTEND_PID > .frontend.pid

# 显示成功信息
echo ""
echo -e "${GREEN}🎉 DeepWiki-Open 最终修复版启动成功！${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "${CYAN}📱 前端应用: http://localhost:3000${NC}"
echo -e "${CYAN}🔧 后端API:  http://localhost:8001${NC}"
echo -e "${CYAN}📊 健康检查: http://localhost:8001/health${NC}"
echo ""
echo -e "${YELLOW}🎯 已修复的问题:${NC}"
echo -e "${GREEN}• MockEmbedderClient 接口实现${NC}"
echo -e "${GREEN}• DeepSeekClient ModelClient 继承${NC}"
echo -e "${GREEN}• 默认模型提供商配置${NC}"
echo -e "${GREEN}• 模拟嵌入模式启用${NC}"
echo ""
echo -e "${YELLOW}📖 使用说明:${NC}"
echo -e "${BLUE}• 本地路径: /Users/mac/github-local/deepwiki-open-main${NC}"
echo -e "${BLUE}• GitHub仓库: owner/repo${NC}"
echo -e "${BLUE}• 当前模型: DeepSeek (deepseek-chat)${NC}"
echo -e "${BLUE}• 嵌入模式: 模拟模式 (无需真实API)${NC}"
echo ""
echo -e "${YELLOW}🛑 停止服务:${NC}"
echo -e "${BLUE}• 按 Ctrl+C 停止所有服务${NC}"
echo -e "${BLUE}• 或运行: ./stop.sh${NC}"
echo ""
echo -e "${GREEN}📚 查看日志:${NC}"
echo -e "${BLUE}• 后端日志: tail -f api/logs/backend.log${NC}"
echo ""

# 设置信号处理
cleanup() {
    echo -e "\n${YELLOW}正在停止服务...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    rm -f api/.backend.pid .frontend.pid
    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}

trap cleanup INT TERM

# 等待用户中断
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
while true; do
    sleep 1
done