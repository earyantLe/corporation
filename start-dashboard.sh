#!/bin/bash
# 🏢 公司智能体监控看板启动脚本
# 用法：./start-dashboard.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$SCRIPT_DIR/dashboard"
PORT=8080

echo "🏢 公司智能体监控看板"
echo "========================"
echo ""

# 检查端口是否被占用
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  端口 $PORT 已被占用，停止旧服务..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# 创建数据目录
mkdir -p "$SCRIPT_DIR/data"

# 启动 Python 后端服务
echo "🚀 启动监控服务..."
cd "$DASHBOARD_DIR"
nohup python3 app.py > "$SCRIPT_DIR/logs/dashboard.log" 2>&1 &
PID=$!

sleep 3

echo ""
echo "✅ 服务已启动 (PID: $PID)"
echo ""
echo "📊 访问地址："
echo "   监控看板：http://127.0.0.1:$PORT/"
echo "   任务管理：http://127.0.0.1:$PORT/tasks.html"
echo "   API 接口：http://127.0.0.1:$PORT/api/stats"
echo ""
echo "💡 提示："
echo "   - 在浏览器中打开上述地址即可查看"
echo "   - 日志文件：$SCRIPT_DIR/logs/dashboard.log"
echo "   - 停止服务：pkill -f 'dashboard/app.py'"
echo "   - 数据库位置：$SCRIPT_DIR/data/corporation.db"
echo ""
