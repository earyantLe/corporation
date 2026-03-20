#!/usr/bin/env python3
"""
公司智能体监控数据服务
提供实时监控数据接口
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.request
import urllib.error

# 配置
PORT = 8080
GATEWAY_URL = "http://127.0.0.1:18789"
DATA_DIR = Path(__file__).parent.parent / "data"

# Agent 列表
AGENTS = [
    {"id": "ceo", "name": "CEO", "emoji": "👔", "role": "战略决策"},
    {"id": "coo", "name": "COO", "emoji": "👕", "role": "运营协调"},
    {"id": "cfo", "name": "CFO", "emoji": "👗", "role": "财务法务"},
    {"id": "cto", "name": "CTO", "emoji": "💼", "role": "技术产品"},
    {"id": "hr", "name": "人力", "emoji": "👥", "role": "团队建设"},
    {"id": "finance", "name": "财务", "emoji": "💰", "role": "会计核算"},
    {"id": "legal", "name": "法务", "emoji": "⚖️", "role": "合规风控"},
    {"id": "marketing", "name": "市场", "emoji": "📢", "role": "品牌营销"},
    {"id": "sales", "name": "销售", "emoji": "🤝", "role": "客户开发"},
    {"id": "engineering", "name": "工程", "emoji": "🔧", "role": "核心开发"},
    {"id": "design", "name": "设计", "emoji": "🎨", "role": "UI/UX"},
    {"id": "qa", "name": "QA", "emoji": "✅", "role": "质量检查"},
]


class MonitorData:
    """监控数据管理"""

    def __init__(self):
        self.data_file = DATA_DIR / "monitor_data.json"
        self.data = self.load_data()

    def load_data(self):
        """加载数据"""
        if self.data_file.exists():
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "tasks": [],
            "agents": {a["id"]: {"requests": 0, "tokens": 0, "errors": 0} for a in AGENTS},
            "metrics": {
                "total_requests": 0,
                "total_tokens": 0,
                "start_time": datetime.now().isoformat(),
            },
        }

    def save_data(self):
        """保存数据"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_task(self, agent_id: str, message: str, tokens: int = 0):
        """添加任务记录"""
        task = {
            "id": len(self.data["tasks"]) + 1,
            "agent_id": agent_id,
            "message": message[:50] + "..." if len(message) > 50 else message,
            "tokens": tokens,
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
        }
        self.data["tasks"].append(task)
        self.data["agents"][agent_id]["requests"] += 1
        self.data["agents"][agent_id]["tokens"] += tokens
        self.data["metrics"]["total_requests"] += 1
        self.data["metrics"]["total_tokens"] += tokens
        self.save_data()
        return task

    def get_stats(self):
        """获取统计数据"""
        today = datetime.now().date().isoformat()
        today_tasks = [
            t for t in self.data["tasks"] if t["timestamp"].startswith(today)
        ]

        return {
            "active_agents": len(AGENTS),
            "today_tasks": len(today_tasks),
            "total_tokens": sum(t["tokens"] for t in today_tasks),
            "avg_response_time": 850,  # 模拟数据
            "agents": self.data["agents"],
            "tasks": self.data["tasks"][-10:],  # 最近 10 条
            "metrics": self.data["metrics"],
        }


# 全局数据实例
monitor = MonitorData()


class APIHandler(SimpleHTTPRequestHandler):
    """API 请求处理"""

    def do_GET(self):
        """处理 GET 请求"""
        if self.path == "/api/stats":
            self.send_json(monitor.get_stats())
        elif self.path == "/api/agents":
            self.send_json({"agents": AGENTS, "status": "ok"})
        elif self.path == "/api/health":
            self.send_json({"status": "healthy", "timestamp": datetime.now().isoformat()})
        else:
            # 静态文件服务
            if self.path == "/":
                self.path = "/dashboard/index.html"
            return super().do_GET()

    def do_POST(self):
        """处理 POST 请求"""
        if self.path == "/api/task":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            task = monitor.add_task(
                data.get("agent_id", "ceo"),
                data.get("message", ""),
                data.get("tokens", 0),
            )
            self.send_json({"success": True, "task": task})
        else:
            self.send_error(404)

    def send_json(self, data):
        """发送 JSON 响应"""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())


def main():
    """启动服务"""
    # 确保数据目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 启动服务器
    server = HTTPServer(("127.0.0.1", PORT), APIHandler)
    print(f"🏢 公司智能体监控服务启动")
    print(f"📊 访问地址：http://127.0.0.1:{PORT}/")
    print(f"📈 API 地址：http://127.0.0.1:{PORT}/api/stats")
    print(f"按 Ctrl+C 停止服务")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止服务...")
        server.shutdown()


if __name__ == "__main__":
    main()
