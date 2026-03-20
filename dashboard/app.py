#!/usr/bin/env python3
"""
公司智能体监控服务 - SQLite 版
提供实时监控数据和任务管理 API
支持：审核机制、实时看板、任务干预、流转审计、热切换模型、技能管理、新闻聚合
"""

import json
import sqlite3
import asyncio
import websockets
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import urllib.parse
import threading
from typing import Set

# 配置
PORT = 8080
WS_PORT = 8765
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "corporation.db"

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

# WebSocket 客户端集合
websocket_clients: Set = set()

# 默认模型配置
DEFAULT_MODELS = [
    {"id": "qwen3.5-plus", "name": "Qwen3.5 Plus", "provider": "bailian", "enabled": True},
    {"id": "GLM-4-Flash", "name": "GLM-4 Flash", "provider": "zhipu", "enabled": True},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai", "enabled": False},
]

# 默认技能配置
DEFAULT_SKILLS = [
    {"id": "task_assignment", "name": "任务分配", "enabled": True, "description": "智能任务分配给合适的 Agent"},
    {"id": "quality_check", "name": "质量检查", "enabled": True, "description": "QA 质量检测和验收"},
    {"id": "document_review", "name": "文档审查", "enabled": True, "description": "技术文档和商务文档审查"},
    {"id": "strategy_meeting", "name": "战略会议", "enabled": True, "description": "高层战略会议和协调"},
    {"id": "budget_planning", "name": "预算规划", "enabled": True, "description": "财务预算规划和评估"},
]


def init_db():
    """初始化数据库"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 任务表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            tokens INTEGER DEFAULT 0,
            result TEXT,
            priority TEXT DEFAULT 'normal',
            assigned_to TEXT,
            paused BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)

    # 活动日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 性能指标表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            metric_type TEXT NOT NULL,
            value REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 审核表（审核机制）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            reviewer_id TEXT NOT NULL,
            decision TEXT DEFAULT 'pending',
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)

    # 流转审计表（流转审计）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            from_status TEXT,
            to_status TEXT NOT NULL,
            operator TEXT NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)

    # 模型配置表（热切换模型）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            provider TEXT NOT NULL,
            enabled BOOLEAN DEFAULT TRUE,
            api_key_env TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 技能配置表（技能管理）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            enabled BOOLEAN DEFAULT TRUE,
            config TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 新闻表（新闻聚合推送）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT,
            url TEXT,
            source TEXT,
            category TEXT,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 政策表（公司政策）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # 初始化示例数据（如果是新数据库）
    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        now = datetime.now()
        sample_tasks = [
            ("ceo", "公司要开发一个 AI 智能客服系统，组织 CTO、CFO、COO 开战略会议", "completed", 2500, "已完成战略会议，确定技术方向和预算", (now - timedelta(days=1)).isoformat()),
            ("cto", "设计电商网站技术架构", "completed", 15000, "已完成架构设计文档", (now - timedelta(hours=12)).isoformat()),
            ("qa", "制定产品质量检测计划", "completed", 8500, "已完成 QA 测试计划", (now - timedelta(hours=6)).isoformat()),
        ]
        cursor.executemany(
            "INSERT INTO tasks (agent_id, content, status, tokens, result, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            sample_tasks
        )

    # 初始化默认模型配置
    cursor.execute("SELECT COUNT(*) FROM models")
    if cursor.fetchone()[0] == 0:
        for model in DEFAULT_MODELS:
            cursor.execute(
                "INSERT INTO models (model_id, name, provider, enabled) VALUES (?, ?, ?, ?)",
                (model["id"], model["name"], model["provider"], model["enabled"])
            )

    # 初始化默认技能配置
    cursor.execute("SELECT COUNT(*) FROM skills")
    if cursor.fetchone()[0] == 0:
        for skill in DEFAULT_SKILLS:
            cursor.execute(
                "INSERT INTO skills (skill_id, name, description, enabled) VALUES (?, ?, ?, ?)",
                (skill["id"], skill["name"], skill["description"], skill["enabled"])
            )

        conn.commit()

    conn.close()
    print(f"📁 数据库：{DB_PATH}")


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class APIHandler(SimpleHTTPRequestHandler):
    """API 请求处理"""

    def do_GET(self):
        """处理 GET 请求"""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/stats":
            self.send_json(self.get_stats())
        elif path == "/api/agents":
            self.send_json({"agents": AGENTS})
        elif path == "/api/health":
            self.send_json({"status": "healthy", "timestamp": datetime.now().isoformat()})
        elif path == "/api/tasks":
            status = query.get("status", [None])[0]
            self.send_json(self.get_tasks(status))
        elif path.startswith("/api/tasks/"):
            task_id = path.split("/")[-1]
            if task_id.isdigit():
                self.send_json(self.get_task(int(task_id)))
            else:
                self.send_error(404)
        elif path == "/api/performance":
            self.send_json(self.get_performance())
        elif path == "/api/activities":
            self.send_json(self.get_activities())
        # 新增 API 端点
        elif path == "/api/reviews":
            task_id = query.get("task_id", [None])[0]
            self.send_json(self.get_reviews(task_id))
        elif path.startswith("/api/reviews/"):
            review_id = path.split("/")[-1]
            if review_id.isdigit():
                self.send_json(self.get_review(int(review_id)))
            else:
                self.send_error(404)
        elif path == "/api/audit-logs":
            task_id = query.get("task_id", [None])[0]
            self.send_json(self.get_audit_logs(task_id))
        elif path == "/api/models":
            self.send_json(self.get_models())
        elif path.startswith("/api/models/"):
            model_id = path.split("/")[-1]
            self.send_json(self.get_model(model_id))
        elif path == "/api/skills":
            self.send_json(self.get_skills())
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/")[-1]
            self.send_json(self.get_skill(skill_id))
        elif path == "/api/news":
            category = query.get("category", [None])[0]
            self.send_json(self.get_news(category))
        elif path == "/api/policies":
            category = query.get("category", [None])[0]
            self.send_json(self.get_policies(category))
        elif path.startswith("/api/policies/"):
            policy_id = path.split("/")[-1]
            if policy_id.isdigit():
                self.send_json(self.get_policy(int(policy_id)))
            else:
                self.send_error(404)
        # 任务干预 API
        elif path == "/api/tasks/intervene":
            self.send_json({"success": True, "actions": ["pause", "resume", "reassign", "prioritize"]})
        elif path.startswith("/api/tasks/") and "/intervene" in path:
            task_id = int(path.split("/")[3])
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            action = data.get("action")
            result = self.intervene_task(task_id, action, data)
            self.send_json({"success": True, "result": result})
        else:
            # 静态文件服务 - 设置正确的目录
            if self.path == "/" or self.path == "/index.html":
                self.path = "/index.html"
            # SimpleHTTPRequestHandler 会在当前目录（dashboard）查找文件
            return super().do_GET()

    def do_POST(self):
        """处理 POST 请求"""
        if self.path == "/api/tasks":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            task = self.create_task(data)
            self.send_json({"success": True, "task": task})
        elif self.path.startswith("/api/tasks/") and "/status" in self.path:
            task_id = int(self.path.split("/")[3])
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            task = self.update_task_status(task_id, data.get("status"))
            self.send_json({"success": True, "task": task})
        elif self.path.startswith("/api/tasks/"):
            task_id = int(self.path.split("/")[-1])
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            task = self.update_task(task_id, data)
            self.send_json({"success": True, "task": task})
        # 新增 POST 端点
        elif self.path == "/api/reviews":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            review = self.create_review(data)
            self.send_json({"success": True, "review": review})
        elif self.path.startswith("/api/reviews/") and "/status" in self.path:
            review_id = int(self.path.split("/")[3])
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            review = self.update_review_status(review_id, data)
            self.send_json({"success": True, "review": review})
        elif self.path == "/api/models":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            model = self.create_model(data)
            self.send_json({"success": True, "model": model})
        elif self.path.startswith("/api/models/"):
            model_id = self.path.split("/")[-1]
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            model = self.update_model(model_id, data)
            self.send_json({"success": True, "model": model})
        elif self.path == "/api/skills":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            skill = self.create_skill(data)
            self.send_json({"success": True, "skill": skill})
        elif self.path.startswith("/api/skills/"):
            skill_id = self.path.split("/")[-1]
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            skill = self.update_skill(skill_id, data)
            self.send_json({"success": True, "skill": skill})
        elif self.path == "/api/news":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            news = self.create_news(data)
            self.send_json({"success": True, "news": news})
        elif self.path == "/api/policies":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            policy = self.create_policy(data)
            self.send_json({"success": True, "policy": policy})
        else:
            self.send_error(404)

    def do_DELETE(self):
        """处理 DELETE 请求"""
        if self.path.startswith("/api/tasks/"):
            task_id = int(self.path.split("/")[-1])
            self.delete_task(task_id)
            self.send_json({"success": True})
        elif self.path.startswith("/api/reviews/"):
            review_id = int(self.path.split("/")[-1])
            self.delete_review(review_id)
            self.send_json({"success": True})
        elif self.path.startswith("/api/models/"):
            model_id = self.path.split("/")[-1]
            self.delete_model(model_id)
            self.send_json({"success": True})
        elif self.path.startswith("/api/skills/"):
            skill_id = self.path.split("/")[-1]
            self.delete_skill(skill_id)
            self.send_json({"success": True})
        elif self.path.startswith("/api/news/"):
            news_id = int(self.path.split("/")[-1])
            self.delete_news(news_id)
            self.send_json({"success": True})
        elif self.path.startswith("/api/policies/"):
            policy_id = int(self.path.split("/")[-1])
            self.delete_policy(policy_id)
            self.send_json({"success": True})
        else:
            self.send_error(404)

    def send_json(self, data):
        """发送 JSON 响应"""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # API 方法
    def get_stats(self):
        """获取统计数据"""
        conn = get_db()
        cursor = conn.cursor()

        # 任务统计
        cursor.execute("SELECT COUNT(*) FROM tasks")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
        completed = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'processing'")
        processing = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
        pending = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(tokens), 0) FROM tasks")
        total_tokens = cursor.fetchone()[0]

        # 今日数据
        today = datetime.now().date().isoformat()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE DATE(created_at) = ?", (today,))
        today_tasks = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(tokens), 0) FROM tasks WHERE DATE(created_at) = ?", (today,))
        today_tokens = cursor.fetchone()[0]

        conn.close()

        return {
            "total": total,
            "completed": completed,
            "processing": processing,
            "pending": pending,
            "total_tokens": total_tokens,
            "today_tasks": today_tasks,
            "today_tokens": today_tokens,
            "active_agents": len(AGENTS)
        }

    def get_tasks(self, status=None):
        """获取任务列表"""
        conn = get_db()
        cursor = conn.cursor()

        if status:
            cursor.execute("SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")

        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                "id": row["id"],
                "agent_id": row["agent_id"],
                "content": row["content"],
                "status": row["status"],
                "tokens": row["tokens"],
                "result": row["result"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "completed_at": row["completed_at"]
            })

        conn.close()
        return {"tasks": tasks}

    def get_task(self, task_id):
        """获取单个任务"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row["id"],
                "agent_id": row["agent_id"],
                "content": row["content"],
                "status": row["status"],
                "tokens": row["tokens"],
                "result": row["result"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "completed_at": row["completed_at"]
            }
        return None

    def create_task(self, data):
        """创建任务"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (agent_id, content, status, tokens) VALUES (?, ?, ?, ?)",
            (data.get("agent_id"), data.get("content"), data.get("status", "pending"), data.get("tokens", 0))
        )
        task_id = cursor.lastrowid

        # 记录创建审计日志
        cursor.execute(
            "INSERT INTO audit_logs (task_id, from_status, to_status, operator, reason) VALUES (?, ?, ?, ?, ?)",
            (task_id, None, data.get("status", "pending"), "user", "任务创建")
        )

        conn.commit()
        conn.close()

        # WebSocket 推送
        asyncio.run(self.broadcast_update("task_created", {"task_id": task_id}))

        return self.get_task(task_id)

    def update_task_status(self, task_id, status):
        """更新任务状态"""
        conn = get_db()
        cursor = conn.cursor()

        # 获取当前状态用于审计
        cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        from_status = row["status"] if row else None

        completed_at = None
        if status == "completed":
            completed_at = datetime.now().isoformat()
            cursor.execute(
                "UPDATE tasks SET status = ?, completed_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, completed_at, task_id)
            )
        else:
            cursor.execute(
                "UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, task_id)
            )

        # 记录流转审计日志
        cursor.execute(
            "INSERT INTO audit_logs (task_id, from_status, to_status, operator, reason) VALUES (?, ?, ?, ?, ?)",
            (task_id, from_status, status, "system", f"状态变更：{from_status} -> {status}")
        )

        conn.commit()
        conn.close()

        # WebSocket 推送
        asyncio.run(self.broadcast_update("task_status_changed", {"task_id": task_id, "status": status}))

        return self.get_task(task_id)

    def update_task(self, task_id, data):
        """更新任务"""
        conn = get_db()
        cursor = conn.cursor()

        # 获取当前状态用于审计
        cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        from_status = row["status"] if row else None

        completed_at = data.get("completed_at")
        cursor.execute(
            "UPDATE tasks SET agent_id = ?, content = ?, status = ?, tokens = ?, result = ?, completed_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (data.get("agent_id"), data.get("content"), data.get("status"), data.get("tokens"), data.get("result"), completed_at, task_id)
        )

        # 如果状态变更，记录审计日志
        if data.get("status") and data.get("status") != from_status:
            cursor.execute(
                "INSERT INTO audit_logs (task_id, from_status, to_status, operator, reason) VALUES (?, ?, ?, ?, ?)",
                (task_id, from_status, data.get("status"), "user", f"任务更新：{from_status} -> {data.get('status')}")
            )

        conn.commit()
        conn.close()
        return self.get_task(task_id)

    def delete_task(self, task_id):
        """删除任务"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()

    def get_performance(self):
        """获取绩效统计"""
        conn = get_db()
        cursor = conn.cursor()

        performance = []
        for agent in AGENTS:
            # 总任务数
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE agent_id = ?", (agent["id"],))
            total = cursor.fetchone()[0]

            # 各状态数量
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE agent_id = ? AND status = 'completed'", (agent["id"],))
            completed = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM tasks WHERE agent_id = ? AND status = 'processing'", (agent["id"],))
            processing = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM tasks WHERE agent_id = ? AND status = 'pending'", (agent["id"],))
            pending = cursor.fetchone()[0]

            # 总 Token 消耗
            cursor.execute("SELECT COALESCE(SUM(tokens), 0) FROM tasks WHERE agent_id = ?", (agent["id"],))
            total_tokens = cursor.fetchone()[0]

            # 平均响应时间（模拟）
            cursor.execute("SELECT AVG(tokens) FROM tasks WHERE agent_id = ? AND status = 'completed'", (agent["id"],))
            avg_tokens = cursor.fetchone()[0] or 0

            # 完成率
            completion_rate = 0
            if total > 0:
                completion_rate = round((completed / total) * 100, 1)

            performance.append({
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "agent_emoji": agent["emoji"],
                "role": agent["role"],
                "total_tasks": total,
                "completed": completed,
                "processing": processing,
                "pending": pending,
                "total_tokens": int(total_tokens),
                "avg_tokens": int(avg_tokens),
                "completion_rate": completion_rate,
                "satisfaction": round(4.0 + (completed / max(total, 1)) * 0.5, 1) if total > 0 else 0
            })

        conn.close()

        # 按任务数排序
        performance.sort(key=lambda x: x["total_tasks"], reverse=True)
        return {"performance": performance}

    def get_activities(self, limit=20):
        """获取最近活动"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*, a.action, a.details
            FROM tasks t
            LEFT JOIN activities a ON t.id = CAST(a.details AS INTEGER)
            ORDER BY t.created_at DESC
            LIMIT ?
        """, (limit,))

        activities = []
        for row in cursor.fetchall():
            activities.append({
                "id": row["id"],
                "agent_id": row["agent_id"],
                "content": row["content"],
                "status": row["status"],
                "created_at": row["created_at"]
            })

        conn.close()
        return {"activities": activities}

    # 新增 API 方法 - 审核机制
    def get_reviews(self, task_id=None):
        """获取审核列表"""
        conn = get_db()
        cursor = conn.cursor()
        if task_id:
            cursor.execute("SELECT * FROM reviews WHERE task_id = ? ORDER BY created_at DESC", (task_id,))
        else:
            cursor.execute("SELECT * FROM reviews ORDER BY created_at DESC")
        reviews = []
        for row in cursor.fetchall():
            reviews.append({
                "id": row["id"],
                "task_id": row["task_id"],
                "reviewer_id": row["reviewer_id"],
                "decision": row["decision"],
                "comments": row["comments"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        conn.close()
        return {"reviews": reviews}

    def get_review(self, review_id):
        """获取单个审核"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row["id"],
                "task_id": row["task_id"],
                "reviewer_id": row["reviewer_id"],
                "decision": row["decision"],
                "comments": row["comments"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None

    def create_review(self, data):
        """创建审核"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reviews (task_id, reviewer_id, decision, comments) VALUES (?, ?, ?, ?)",
            (data.get("task_id"), data.get("reviewer_id"), data.get("decision", "pending"), data.get("comments"))
        )
        review_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return self.get_review(review_id)

    def update_review_status(self, review_id, data):
        """更新审核状态"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE reviews SET decision = ?, comments = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (data.get("decision"), data.get("comments"), review_id)
        )
        conn.commit()
        conn.close()

        # 同时更新任务状态
        if data.get("decision") == "approved":
            cursor = conn.cursor()
            cursor.execute("SELECT task_id FROM reviews WHERE id = ?", (review_id,))
            task_id = cursor.fetchone()[0]
            self.update_task_status(task_id, "completed")
            conn.close()

        return self.get_review(review_id)

    def delete_review(self, review_id):
        """删除审核"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()
        conn.close()

    # 流转审计
    def get_audit_logs(self, task_id=None):
        """获取审计日志"""
        conn = get_db()
        cursor = conn.cursor()
        if task_id:
            cursor.execute("SELECT * FROM audit_logs WHERE task_id = ? ORDER BY created_at DESC", (task_id,))
        else:
            cursor.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 50")
        logs = []
        for row in cursor.fetchall():
            logs.append({
                "id": row["id"],
                "task_id": row["task_id"],
                "from_status": row["from_status"],
                "to_status": row["to_status"],
                "operator": row["operator"],
                "reason": row["reason"],
                "created_at": row["created_at"]
            })
        conn.close()
        return {"audit_logs": logs}

    # 模型管理
    def get_models(self):
        """获取模型列表"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models ORDER BY created_at DESC")
        models = []
        for row in cursor.fetchall():
            models.append({
                "id": row["id"],
                "model_id": row["model_id"],
                "name": row["name"],
                "provider": row["provider"],
                "enabled": bool(row["enabled"]),
                "api_key_env": row["api_key_env"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        conn.close()
        return {"models": models}

    def get_model(self, model_id):
        """获取单个模型"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models WHERE model_id = ?", (model_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row["id"],
                "model_id": row["model_id"],
                "name": row["name"],
                "provider": row["provider"],
                "enabled": bool(row["enabled"]),
                "api_key_env": row["api_key_env"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None

    def create_model(self, data):
        """创建模型配置"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO models (model_id, name, provider, enabled, api_key_env) VALUES (?, ?, ?, ?, ?)",
            (data.get("model_id"), data.get("name"), data.get("provider"), data.get("enabled", True), data.get("api_key_env"))
        )
        conn.commit()
        conn.close()
        return self.get_model(data.get("model_id"))

    def update_model(self, model_id, data):
        """更新模型配置"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE models SET name = ?, provider = ?, enabled = ?, api_key_env = ?, updated_at = CURRENT_TIMESTAMP WHERE model_id = ?",
            (data.get("name"), data.get("provider"), data.get("enabled"), data.get("api_key_env"), model_id)
        )
        conn.commit()
        conn.close()
        return self.get_model(model_id)

    def delete_model(self, model_id):
        """删除模型配置"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM models WHERE model_id = ?", (model_id,))
        conn.commit()
        conn.close()

    # 技能管理
    def get_skills(self):
        """获取技能列表"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills ORDER BY created_at DESC")
        skills = []
        for row in cursor.fetchall():
            skills.append({
                "id": row["id"],
                "skill_id": row["skill_id"],
                "name": row["name"],
                "description": row["description"],
                "enabled": bool(row["enabled"]),
                "config": row["config"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        conn.close()
        return {"skills": skills}

    def get_skill(self, skill_id):
        """获取单个技能"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills WHERE skill_id = ?", (skill_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row["id"],
                "skill_id": row["skill_id"],
                "name": row["name"],
                "description": row["description"],
                "enabled": bool(row["enabled"]),
                "config": row["config"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None

    def create_skill(self, data):
        """创建技能配置"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO skills (skill_id, name, description, enabled, config) VALUES (?, ?, ?, ?, ?)",
            (data.get("skill_id"), data.get("name"), data.get("description"), data.get("enabled", True), json.dumps(data.get("config", {})))
        )
        conn.commit()
        conn.close()
        return self.get_skill(data.get("skill_id"))

    def update_skill(self, skill_id, data):
        """更新技能配置"""
        conn = get_db()
        cursor = conn.cursor()
        config_json = json.dumps(data.get("config", {})) if data.get("config") else None
        cursor.execute(
            "UPDATE skills SET name = ?, description = ?, enabled = ?, config = ?, updated_at = CURRENT_TIMESTAMP WHERE skill_id = ?",
            (data.get("name"), data.get("description"), data.get("enabled"), config_json, skill_id)
        )
        conn.commit()
        conn.close()
        return self.get_skill(skill_id)

    def delete_skill(self, skill_id):
        """删除技能配置"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM skills WHERE skill_id = ?", (skill_id,))
        conn.commit()
        conn.close()

    # 新闻管理
    def get_news(self, category=None):
        """获取新闻列表"""
        conn = get_db()
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM news WHERE category = ? ORDER BY published_at DESC LIMIT 20", (category,))
        else:
            cursor.execute("SELECT * FROM news ORDER BY published_at DESC LIMIT 20")
        news = []
        for row in cursor.fetchall():
            news.append({
                "id": row["id"],
                "title": row["title"],
                "summary": row["summary"],
                "url": row["url"],
                "source": row["source"],
                "category": row["category"],
                "published_at": row["published_at"],
                "created_at": row["created_at"]
            })
        conn.close()
        return {"news": news}

    def create_news(self, data):
        """创建新闻"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO news (title, summary, url, source, category, published_at) VALUES (?, ?, ?, ?, ?, ?)",
            (data.get("title"), data.get("summary"), data.get("url"), data.get("source"), data.get("category"), data.get("published_at"))
        )
        conn.commit()
        conn.close()
        # 推送 WebSocket 通知
        asyncio.run(self.broadcast_news(data))
        return {"id": cursor.lastrowid, **data}

    def delete_news(self, news_id):
        """删除新闻"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM news WHERE id = ?", (news_id,))
        conn.commit()
        conn.close()

    # 政策管理
    def get_policies(self, category=None):
        """获取政策列表"""
        conn = get_db()
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM policies WHERE category = ? ORDER BY created_at DESC", (category,))
        else:
            cursor.execute("SELECT * FROM policies ORDER BY created_at DESC")
        policies = []
        for row in cursor.fetchall():
            policies.append({
                "id": row["id"],
                "title": row["title"],
                "category": row["category"],
                "content": row["content"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        conn.close()
        return {"policies": policies}

    def get_policy(self, policy_id):
        """获取单个政策"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM policies WHERE id = ?", (policy_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row["id"],
                "title": row["title"],
                "category": row["category"],
                "content": row["content"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None

    def create_policy(self, data):
        """创建政策"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO policies (title, category, content) VALUES (?, ?, ?)",
            (data.get("title"), data.get("category"), data.get("content"))
        )
        conn.commit()
        conn.close()
        return {"id": cursor.lastrowid, **data}

    def delete_policy(self, policy_id):
        """删除政策"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM policies WHERE id = ?", (policy_id,))
        conn.commit()
        conn.close()

    # 任务干预
    def intervene_task(self, task_id, action, data):
        """任务干预：暂停/恢复/转交/优先级调整"""
        conn = get_db()
        cursor = conn.cursor()

        # 获取当前任务信息
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        if not task:
            conn.close()
            return {"error": "任务不存在"}

        result = {"task_id": task_id, "action": action}

        if action == "pause":
            cursor.execute("UPDATE tasks SET paused = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
            cursor.execute(
                "INSERT INTO audit_logs (task_id, from_status, to_status, operator, reason) VALUES (?, ?, ?, ?, ?)",
                (task_id, task["status"], task["status"], "user", "任务暂停")
            )
            result["paused"] = True

        elif action == "resume":
            cursor.execute("UPDATE tasks SET paused = FALSE, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
            cursor.execute(
                "INSERT INTO audit_logs (task_id, from_status, to_status, operator, reason) VALUES (?, ?, ?, ?, ?)",
                (task_id, task["status"], task["status"], "user", "任务恢复")
            )
            result["paused"] = False

        elif action == "reassign":
            new_agent = data.get("assigned_to")
            cursor.execute("UPDATE tasks SET assigned_to = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_agent, task_id))
            cursor.execute(
                "INSERT INTO audit_logs (task_id, from_status, to_status, operator, reason) VALUES (?, ?, ?, ?, ?)",
                (task_id, task["status"], task["status"], "user", f"任务转交给 {new_agent}")
            )
            result["assigned_to"] = new_agent

        elif action == "prioritize":
            priority = data.get("priority", "normal")
            cursor.execute("UPDATE tasks SET priority = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (priority, task_id))
            cursor.execute(
                "INSERT INTO audit_logs (task_id, from_status, to_status, operator, reason) VALUES (?, ?, ?, ?, ?)",
                (task_id, task["status"], task["status"], "user", f"优先级调整为 {priority}")
            )
            result["priority"] = priority

        conn.commit()
        conn.close()

        # WebSocket 推送
        asyncio.run(self.broadcast_update("task_intervened", result))

        return result

    async def broadcast_news(self, data):
        """推送新闻到 WebSocket 客户端"""
        if websocket_clients:
            message = json.dumps({"type": "news", "data": data}, ensure_ascii=False)
            await asyncio.gather(
                *[ws.send(message) for ws in websocket_clients],
                return_exceptions=True
            )

    async def broadcast_update(self, event_type, data):
        """通用 WebSocket 广播"""
        if websocket_clients:
            message = json.dumps({"type": event_type, "data": data}, ensure_ascii=False)
            await asyncio.gather(
                *[ws.send(message) for ws in websocket_clients],
                return_exceptions=True
            )


def main():
    """启动服务"""
    # 切换到 dashboard 目录以便提供静态文件
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    init_db()

    # 启动 WebSocket 服务器（后台线程）
    def start_ws():
        asyncio.run(run_websocket_server())

    ws_thread = threading.Thread(target=start_ws, daemon=True)
    ws_thread.start()

    # 启动 HTTP 服务器
    server = HTTPServer(("0.0.0.0", PORT), APIHandler)
    print(f"🏢 公司智能体监控服务启动")
    print(f"📊 访问地址：http://127.0.0.1:{PORT}/")
    print(f"📡 WebSocket 地址：ws://127.0.0.1:{WS_PORT}/")
    print(f"📈 API 地址：http://127.0.0.1:{PORT}/api/stats")
    print(f"💾 数据库：{DB_PATH}")
    print(f"按 Ctrl+C 停止服务")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止服务...")
        server.shutdown()


async def ws_handler(websocket):
    """WebSocket 连接处理"""
    websocket_clients.add(websocket)
    print(f"🔌 客户端连接，当前在线：{len(websocket_clients)}")
    try:
        await websocket.wait_closed()
    finally:
        websocket_clients.remove(websocket)
        print(f"🔌 客户端断开，当前在线：{len(websocket_clients)}")


async def run_websocket_server():
    """运行 WebSocket 服务器"""
    async with websockets.serve(ws_handler, "0.0.0.0", WS_PORT):
        await asyncio.Future()  # 永久运行


if __name__ == "__main__":
    main()
