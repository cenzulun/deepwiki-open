#!/bin/bash

# DeepWiki-Open 停止服务脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}DeepWiki-Open 停止服务${NC}"
echo -e "${YELLOW}=======================${NC}"

# 停止函数
stop_service() {
    local port=$1
    local service_name=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        echo -e "${YELLOW}正在停止 $service_name (端口: $port)...${NC}"
        lsof -ti:$port | xargs kill -TERM 2>/dev/null

        # 等待进程优雅退出
        sleep 3

        # 如果进程还在运行，强制终止
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
            echo -e "${YELLOW}强制终止 $service_name...${NC}"
            lsof -ti:$port | xargs kill -9 2>/dev/null
        fi

        echo -e "${GREEN}✓ $service_name 已停止${NC}"
    else
        echo -e "${BLUE}$service_name 未在运行${NC}"
    fi
}

# 通过PID文件停止
stop_by_pid() {
    local pid_file=$1
    local service_name=$2

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}正在停止 $service_name (PID: $pid)...${NC}"
            kill $pid 2>/dev/null

            # 等待进程退出
            sleep 2

            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}强制终止 $service_name...${NC}"
                kill -9 $pid 2>/dev/null
            fi

            echo -e "${GREEN}✓ $service_name 已停止${NC}"
        else
            echo -e "${BLUE}$service_name 进程不存在${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${BLUE}$service_name PID文件不存在${NC}"
    fi
}

# 停止所有相关进程
echo -e "${YELLOW}正在查找并停止所有 DeepWiki-Open 相关进程...${NC}"

# 通过PID文件停止
stop_by_pid "api/.backend.pid" "后端服务"
stop_by_pid ".frontend.pid" "前端服务"

# 通过端口停止
stop_service 8001 "后端API服务"
stop_service 3000 "前端开发服务器"

# 额外检查，确保所有相关进程都被停止
echo -e "${YELLOW}检查并清理残留进程...${NC}"

# 查找可能的python进程
pids=$(ps aux | grep "api.main" | grep -v grep | awk '{print $2}')
if [ ! -z "$pids" ]; then
    echo -e "${YELLOW}发现残留的后端进程，正在清理...${NC}"
    echo "$pids" | xargs kill -9 2>/dev/null
fi

# 查找可能的Node.js进程
pids=$(ps aux | grep "next dev\|npm run dev" | grep -v grep | awk '{print $2}')
if [ ! -z "$pids" ]; then
    echo -e "${YELLOW}发现残留的前端进程，正在清理...${NC}"
    echo "$pids" | xargs kill -9 2>/dev/null
fi

echo ""
echo -e "${GREEN}🎉 所有服务已停止！${NC}"
echo ""
echo -e "${BLUE}重新启动请运行: ./start.sh${NC}"
echo -e "${BLUE}查看服务状态: ./start.sh status${NC}"