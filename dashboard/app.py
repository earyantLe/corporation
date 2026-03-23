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

    # 工作流定义表（工作流引擎）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            version TEXT DEFAULT '1.0.0',
            definition TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 工作流节点表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            node_id TEXT NOT NULL,
            node_type TEXT NOT NULL,
            node_name TEXT NOT NULL,
            config TEXT,
            position_x INTEGER DEFAULT 0,
            position_y INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id)
        )
    """)

    # 工作流转换表（节点间的连接）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_transitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            from_node_id TEXT NOT NULL,
            to_node_id TEXT NOT NULL,
            condition TEXT,
            label TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id)
        )
    """)

    # 工作流实例表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            task_id INTEGER,
            current_node_id TEXT,
            status TEXT DEFAULT 'running',
            context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id),
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)

    # 工作流执行日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_id INTEGER NOT NULL,
            node_id TEXT NOT NULL,
            action TEXT NOT NULL,
            result TEXT,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instance_id) REFERENCES workflow_instances(id)
        )
    """)

    # 知识库文档表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT,
            tags TEXT,
            author TEXT,
            version TEXT DEFAULT '1.0.0',
            parent_id INTEGER,
            status TEXT DEFAULT 'published',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 文档版本表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            version TEXT NOT NULL,
            content TEXT NOT NULL,
            change_summary TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)

    # IM 消息表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            sender_id TEXT NOT NULL,
            receiver_id TEXT NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # IM 会话表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT UNIQUE NOT NULL,
            participant_ids TEXT NOT NULL,
            last_message_at TIMESTAMP,
            last_message_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 未读消息计数表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unread_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, conversation_id)
        )
    """)

    # Agent 编排引擎表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT UNIQUE NOT NULL,
            agent_name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            capabilities TEXT,
            current_load INTEGER DEFAULT 0,
            max_load INTEGER DEFAULT 100,
            last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orchestration_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id TEXT UNIQUE NOT NULL,
            task_id INTEGER,
            plan_name TEXT NOT NULL,
            agent_sequence TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orchestration_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            agent_id TEXT NOT NULL,
            step_number INTEGER NOT NULL,
            action TEXT NOT NULL,
            result TEXT,
            status TEXT DEFAULT 'pending',
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES orchestration_plans(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            skill_id TEXT NOT NULL,
            proficiency INTEGER DEFAULT 50,
            usage_count INTEGER DEFAULT 0,
            UNIQUE(agent_id, skill_id)
        )
    """)

    # RBAC 权限系统表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id TEXT UNIQUE NOT NULL,
            role_name TEXT NOT NULL,
            description TEXT,
            permissions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            permission_id TEXT UNIQUE NOT NULL,
            permission_name TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            action TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            role_id TEXT NOT NULL,
            granted_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, role_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            access_level TEXT DEFAULT 'read',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(role_id, resource_type, resource_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permission_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id TEXT,
            result TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # 财务模块表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finance_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id TEXT UNIQUE NOT NULL,
            entry_type TEXT NOT NULL,
            account_code TEXT NOT NULL,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            description TEXT,
            related_to TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finance_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_code TEXT UNIQUE NOT NULL,
            account_name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            parent_code TEXT,
            balance REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finance_receivables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            amount REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            due_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finance_payables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id TEXT NOT NULL,
            vendor_id TEXT NOT NULL,
            amount REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            due_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finance_budget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            budget_id TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            used_amount REAL DEFAULT 0,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finance_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT UNIQUE NOT NULL,
            report_type TEXT NOT NULL,
            period TEXT NOT NULL,
            data TEXT NOT NULL,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # CRM 模块表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crm_customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_type TEXT DEFAULT 'enterprise',
            industry TEXT,
            contact_person TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            address TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crm_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opp_id TEXT UNIQUE NOT NULL,
            customer_id TEXT NOT NULL,
            title TEXT NOT NULL,
            amount REAL DEFAULT 0,
            stage TEXT DEFAULT 'lead',
            probability INTEGER DEFAULT 10,
            expected_close_date TIMESTAMP,
            owner TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crm_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id TEXT UNIQUE NOT NULL,
            customer_id TEXT NOT NULL,
            opp_id TEXT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'draft',
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # BI 分析模块表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bi_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT UNIQUE NOT NULL,
            report_name TEXT NOT NULL,
            report_type TEXT DEFAULT 'custom',
            config TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 通知中心表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'system',
            title TEXT NOT NULL,
            message TEXT,
            icon TEXT DEFAULT '📬',
            type TEXT DEFAULT 'system',
            read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            # 返回 Agent 注册列表（编排引擎）
            self.send_json(self.get_agent_registry())
        elif path == "/api/agents/list":
            # 返回原始 Agent 列表（用于前端显示）
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
        # 工作流引擎 API
        elif path == "/api/workflows":
            self.send_json(self.get_workflows())
        elif path.startswith("/api/workflows/"):
            parts = path.split("/")
            workflow_id = parts[3]
            if len(parts) == 4:
                if workflow_id.isdigit():
                    self.send_json(self.get_workflow(int(workflow_id)))
                else:
                    self.send_error(404)
            elif parts[4] == "nodes":
                self.send_json(self.get_workflow_nodes(int(workflow_id)))
            elif parts[4] == "instances":
                self.send_json(self.get_workflow_instances(int(workflow_id)))
            elif parts[4] == "execute":
                self.send_json(self.execute_workflow(int(workflow_id)))
            else:
                self.send_error(404)
        elif path == "/api/workflow-instances":
            status = query.get("status", [None])[0]
            self.send_json(self.get_workflow_instances_all(status))
        # 知识库 API
        elif path == "/api/documents":
            category = query.get("category", [None])[0]
            self.send_json(self.get_documents(category))
        elif path.startswith("/api/documents/"):
            parts = path.split("/")
            doc_id = parts[3]
            if len(parts) == 4:
                if doc_id.isdigit():
                    self.send_json(self.get_document(int(doc_id)))
                else:
                    self.send_error(404)
            elif parts[4] == "versions":
                self.send_json(self.get_document_versions(int(doc_id)))
            else:
                self.send_error(404)
        # IM API
        elif path == "/api/conversations":
            user_id = query.get("user_id", [None])[0]
            self.send_json(self.get_conversations(user_id))
        elif path.startswith("/api/conversations/"):
            parts = path.split("/")
            conv_id = parts[3]
            if len(parts) == 4:
                self.send_json(self.get_conversation(conv_id))
            elif len(parts) == 5 and parts[4] == "messages":
                self.send_json(self.get_messages(conv_id))
            else:
                self.send_error(404)
        elif path == "/api/messages":
            self.send_json(self.get_all_messages())
        elif path.startswith("/api/messages/"):
            parts = path.split("/")
            if len(parts) == 5 and parts[4] == "unread":
                user_id = parts[3]
                self.send_json(self.get_unread_count(user_id))
            else:
                self.send_error(404)
        # Agent 编排引擎 API
        elif path == "/api/orchestration/auto-assign":
            task_id = query.get("task_id", [None])[0]
            self.send_json(self.auto_assign_agents(int(task_id) if task_id else None))
        elif path == "/api/agents":
            self.send_json(self.get_agent_registry())
        elif path.startswith("/api/agents/"):
            parts = path.split("/")
            agent_id = parts[3]
            if len(parts) == 4:
                self.send_json(self.get_agent(agent_id))
            elif len(parts) == 5 and parts[4] == "skills":
                self.send_json(self.get_agent_skills(agent_id))
            else:
                self.send_error(404)
        elif path == "/api/orchestration":
            self.send_json(self.get_orchestration_plans())
        elif path.startswith("/api/orchestration/"):
            parts = path.split("/")
            if len(parts) == 4:
                plan_id = parts[3]
                if plan_id.isdigit():
                    self.send_json(self.get_orchestration_plan(int(plan_id)))
                else:
                    self.send_error(404)
            elif len(parts) == 5 and parts[4] == "history":
                plan_id = parts[3]
                self.send_json(self.get_orchestration_history(int(plan_id)))
            elif len(parts) == 5 and parts[4] == "execute":
                plan_id = parts[3]
                self.execute_orchestration_plan(int(plan_id))
                self.send_json({"success": True})
            else:
                self.send_error(404)
        # RBAC 权限系统 API
        elif path == "/api/roles":
            self.send_json(self.get_roles())
        elif path.startswith("/api/roles/"):
            parts = path.split("/")
            role_id = parts[3]
            if len(parts) == 4:
                self.send_json(self.get_role(role_id))
            elif len(parts) == 5 and parts[4] == "permissions":
                self.send_json(self.get_role_permissions(role_id))
            else:
                self.send_error(404)
        elif path == "/api/permissions":
            self.send_json(self.get_permissions())
        elif path == "/api/user-roles":
            user_id = query.get("user_id", [None])[0]
            self.send_json(self.get_user_roles(user_id))
        elif path == "/api/check-permission":
            user_id = query.get("user_id", [None])[0]
            resource = query.get("resource", [None])[0]
            action = query.get("action", [None])[0]
            self.send_json(self.check_permission(user_id, resource, action))
        # CRM 模块 API
        elif path == "/api/crm/customers":
            self.send_json(self.get_crm_customers())
        elif path == "/api/crm/opportunities":
            self.send_json(self.get_crm_opportunities())
        elif path == "/api/crm/contracts":
            self.send_json(self.get_crm_contracts())
        # BI 分析模块 API
        elif path == "/api/bi/reports":
            self.send_json(self.get_bi_reports())
        elif path == "/api/bi/dashboard":
            self.send_json(self.get_bi_dashboard())
        # 通知中心 API
        elif path == "/api/notifications":
            self.send_json(self.get_notifications())
        elif path == "/api/notifications/read":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            self.send_json(self.mark_notification_read(data))
        # 财务模块 API
        elif path == "/api/finance/ledger":
            self.send_json(self.get_finance_ledger())
        elif path == "/api/finance/accounts":
            self.send_json(self.get_finance_accounts())
        elif path == "/api/finance/receivables":
            self.send_json(self.get_finance_receivables())
        elif path == "/api/finance/payables":
            self.send_json(self.get_finance_payables())
        elif path == "/api/finance/budget":
            self.send_json(self.get_finance_budget())
        elif path == "/api/finance/reports":
            self.send_json(self.get_finance_reports())
        elif path == "/api/finance/summary":
            self.send_json(self.get_finance_summary())
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
        # 工作流引擎 API
        elif self.path == "/api/workflows":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            workflow = self.create_workflow(data)
            self.send_json({"success": True, "workflow": workflow})
        elif self.path.startswith("/api/workflows/"):
            parts = self.path.split("/")
            workflow_id = parts[3]
            if workflow_id.isdigit():
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode()
                data = json.loads(body)
                workflow = self.update_workflow(int(workflow_id), data)
                self.send_json({"success": True, "workflow": workflow})
            else:
                self.send_error(404)
        # 知识库 API
        elif self.path == "/api/documents":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            doc = self.create_document(data)
            self.send_json({"success": True, "document": doc})
        elif self.path.startswith("/api/documents/"):
            parts = self.path.split("/")
            doc_id = parts[3]
            if doc_id.isdigit() and len(parts) == 4:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode()
                data = json.loads(body)
                doc = self.update_document(int(doc_id), data)
                self.send_json({"success": True, "document": doc})
            else:
                self.send_error(404)
        # IM API
        elif self.path == "/api/messages":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            msg = self.send_message(data)
            self.send_json({"success": True, "message": msg})
        elif self.path.startswith("/api/messages/"):
            parts = self.path.split("/")
            if len(parts) == 5 and parts[4] == "read":
                msg_id = parts[3]
                self.mark_message_read(int(msg_id))
                self.send_json({"success": True})
            else:
                self.send_error(404)
        elif self.path == "/api/conversations":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            conv = self.create_conversation(data)
            self.send_json({"success": True, "conversation": conv})
        # Agent 编排引擎 API
        elif self.path == "/api/orchestration":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            plan = self.create_orchestration_plan(data)
            self.send_json({"success": True, "plan": plan})
        elif self.path.startswith("/api/orchestration/"):
            parts = self.path.split("/")
            if len(parts) == 5 and parts[4] == "execute":
                plan_id = parts[3]
                if plan_id.isdigit():
                    self.execute_orchestration_plan(int(plan_id))
                    self.send_json({"success": True})
                else:
                    self.send_error(404)
            else:
                self.send_error(404)
        elif self.path == "/api/agents":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            agent = self.register_agent(data)
            self.send_json({"success": True, "agent": agent})
        # RBAC 权限系统 API
        elif self.path == "/api/roles":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            role = self.create_role(data)
            self.send_json({"success": True, "role": role})
        elif self.path == "/api/permissions":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            perm = self.create_permission(data)
            self.send_json({"success": True, "permission": perm})
        elif self.path.startswith("/api/roles/"):
            parts = self.path.split("/")
            role_id = parts[3]
            if len(parts) == 4:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode()
                data = json.loads(body)
                role = self.update_role(role_id, data)
                self.send_json({"success": True, "role": role})
            elif len(parts) == 5 and parts[4] == "permissions":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode()
                data = json.loads(body)
                result = self.set_role_permissions(role_id, data)
                self.send_json({"success": True, "result": result})
            else:
                self.send_error(404)
        elif self.path == "/api/user-roles":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            result = self.assign_user_role(data)
            self.send_json({"success": True, "result": result})
        # CRM 模块 API
        elif self.path == "/api/crm/customers":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            customer = self.create_crm_customer(data)
            self.send_json({"success": True, "customer": customer})
        elif self.path == "/api/crm/opportunities":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            opp = self.create_crm_opportunity(data)
            self.send_json({"success": True, "opportunity": opp})
        elif self.path == "/api/crm/contracts":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            contract = self.create_crm_contract(data)
            self.send_json({"success": True, "contract": contract})
        # BI 分析模块 API
        elif self.path == "/api/bi/reports":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            report = self.create_bi_report(data)
            self.send_json({"success": True, "report": report})
        # 财务模块 API
        elif self.path.startswith("/api/finance/"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            if "ledger" in self.path:
                result = self.create_finance_ledger_entry(data)
            elif "receivables" in self.path:
                result = self.create_receivable(data)
            elif "payables" in self.path:
                result = self.create_payable(data)
            elif "budget" in self.path:
                result = self.create_budget(data)
            elif "reports" in self.path:
                result = self.create_finance_report(data)
            else:
                self.send_error(404)
                return
            self.send_json({"success": True, "result": result})
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
        elif self.path.startswith("/api/workflows/"):
            workflow_id = int(self.path.split("/")[-1])
            self.delete_workflow(workflow_id)
            self.send_json({"success": True})
        elif self.path.startswith("/api/documents/"):
            doc_id = int(self.path.split("/")[-1])
            self.delete_document(doc_id)
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

    # ========== 工作流引擎方法 ==========

    def get_workflows(self):
        """获取工作流列表"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflows ORDER BY created_at DESC")
        workflows = []
        for row in cursor.fetchall():
            workflows.append({
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "name": row["name"],
                "description": row["description"],
                "version": row["version"],
                "status": row["status"],
                "created_by": row["created_by"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        conn.close()
        return {"workflows": workflows}

    def get_workflow(self, workflow_id):
        """获取单个工作流"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "name": row["name"],
                "description": row["description"],
                "version": row["version"],
                "definition": json.loads(row["definition"]) if row["definition"] else {},
                "status": row["status"],
                "created_by": row["created_by"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None

    def create_workflow(self, data):
        """创建工作流"""
        conn = get_db()
        cursor = conn.cursor()

        workflow_id = data.get("workflow_id", f"wf_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        definition = data.get("definition", {})

        cursor.execute(
            "INSERT INTO workflows (workflow_id, name, description, version, definition, status, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (workflow_id, data.get("name"), data.get("description"), data.get("version", "1.0.0"),
             json.dumps(definition, ensure_ascii=False), data.get("status", "draft"), data.get("created_by", "system"))
        )
        workflow_db_id = cursor.lastrowid

        # 如果定义中包含节点，保存节点
        if "nodes" in definition:
            for node in definition["nodes"]:
                cursor.execute(
                    "INSERT INTO workflow_nodes (workflow_id, node_id, node_type, node_name, config, position_x, position_y) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (workflow_db_id, node.get("id"), node.get("type"), node.get("name"),
                     json.dumps(node.get("config", {}), ensure_ascii=False), node.get("x", 0), node.get("y", 0))
                )

        # 如果定义中包含转换，保存转换
        if "transitions" in definition:
            for trans in definition["transitions"]:
                cursor.execute(
                    "INSERT INTO workflow_transitions (workflow_id, from_node_id, to_node_id, condition, label) VALUES (?, ?, ?, ?, ?)",
                    (workflow_db_id, trans.get("from"), trans.get("to"), trans.get("condition"), trans.get("label"))
                )

        conn.commit()
        conn.close()
        return {"id": workflow_db_id, "workflow_id": workflow_id, **data}

    def update_workflow(self, workflow_id, data):
        """更新工作流"""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE workflows SET name = ?, description = ?, version = ?, definition = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (data.get("name"), data.get("description"), data.get("version"),
             json.dumps(data.get("definition", {}), ensure_ascii=False), data.get("status"), workflow_id)
        )
        conn.commit()
        conn.close()
        return {"id": workflow_id, **data}

    def delete_workflow(self, workflow_id):
        """删除工作流"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM workflow_nodes WHERE workflow_id = ?", (workflow_id,))
        cursor.execute("DELETE FROM workflow_transitions WHERE workflow_id = ?", (workflow_id,))
        cursor.execute("DELETE FROM workflow_instances WHERE workflow_id = ?", (workflow_id,))
        cursor.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
        conn.commit()
        conn.close()

    def get_workflow_nodes(self, workflow_id):
        """获取工作流节点"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflow_nodes WHERE workflow_id = ?", (workflow_id,))
        nodes = []
        for row in cursor.fetchall():
            nodes.append({
                "id": row["id"],
                "node_id": row["node_id"],
                "node_type": row["node_type"],
                "node_name": row["node_name"],
                "config": json.loads(row["config"]) if row["config"] else {},
                "position_x": row["position_x"],
                "position_y": row["position_y"]
            })
        conn.close()
        return {"nodes": nodes}

    def get_workflow_instances(self, workflow_id):
        """获取工作流实例"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflow_instances WHERE workflow_id = ? ORDER BY created_at DESC", (workflow_id,))
        instances = []
        for row in cursor.fetchall():
            instances.append({
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "task_id": row["task_id"],
                "current_node_id": row["current_node_id"],
                "status": row["status"],
                "context": json.loads(row["context"]) if row["context"] else {},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "completed_at": row["completed_at"]
            })
        conn.close()
        return {"instances": instances}

    def get_workflow_instances_all(self, status=None):
        """获取所有工作流实例"""
        conn = get_db()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM workflow_instances WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM workflow_instances ORDER BY created_at DESC")
        instances = []
        for row in cursor.fetchall():
            instances.append({
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "task_id": row["task_id"],
                "current_node_id": row["current_node_id"],
                "status": row["status"],
                "context": json.loads(row["context"]) if row["context"] else {},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "completed_at": row["completed_at"]
            })
        conn.close()
        return {"instances": instances}

    def execute_workflow(self, workflow_id):
        """执行工作流"""
        conn = get_db()
        cursor = conn.cursor()

        # 获取工作流定义
        cursor.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
        workflow = cursor.fetchone()

        if not workflow:
            conn.close()
            return {"error": "工作流不存在"}

        # 创建工作流实例
        cursor.execute(
            "INSERT INTO workflow_instances (workflow_id, status, context) VALUES (?, ?, ?)",
            (workflow_id, "running", "{}")
        )
        instance_id = cursor.lastrowid

        # 获取第一个节点
        cursor.execute("SELECT * FROM workflow_nodes WHERE workflow_id = ? ORDER BY id LIMIT 1", (workflow_id,))
        first_node = cursor.fetchone()

        if first_node:
            cursor.execute(
                "UPDATE workflow_instances SET current_node_id = ? WHERE id = ?",
                (first_node["node_id"], instance_id)
            )

            # 记录执行日志
            cursor.execute(
                "INSERT INTO workflow_execution_logs (instance_id, node_id, action, result) VALUES (?, ?, ?, ?)",
                (instance_id, first_node["node_id"], "started", f"工作流 {workflow['name']} 开始执行")
            )

        conn.commit()
        conn.close()

        return {
            "success": True,
            "instance_id": instance_id,
            "workflow_id": workflow_id,
            "current_node": first_node["node_id"] if first_node else None
        }

    # ==========  конец 工作流引擎方法 ==========

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

    # ========== 知识库方法 ==========

    def get_documents(self, category=None):
        """获取文档列表"""
        conn = get_db()
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM documents WHERE category = ? ORDER BY created_at DESC", (category,))
        else:
            cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
        docs = []
        for row in cursor.fetchall():
            docs.append({
                "id": row["id"],
                "doc_id": row["doc_id"],
                "title": row["title"],
                "content": row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"],
                "category": row["category"],
                "tags": row["tags"].split(",") if row["tags"] else [],
                "author": row["author"],
                "version": row["version"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        conn.close()
        return {"documents": docs}

    def get_document(self, doc_id):
        """获取单个文档"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row["id"],
                "doc_id": row["doc_id"],
                "title": row["title"],
                "content": row["content"],
                "category": row["category"],
                "tags": row["tags"].split(",") if row["tags"] else [],
                "author": row["author"],
                "version": row["version"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None

    def create_document(self, data):
        """创建文档"""
        conn = get_db()
        cursor = conn.cursor()

        doc_id = data.get("doc_id", f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        tags = ",".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else data.get("tags", "")

        cursor.execute(
            "INSERT INTO documents (doc_id, title, content, category, tags, author, version, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (doc_id, data.get("title"), data.get("content"), data.get("category", "general"), tags,
             data.get("author", "system"), data.get("version", "1.0.0"), data.get("status", "published"))
        )
        doc_db_id = cursor.lastrowid

        # 创建版本记录
        cursor.execute(
            "INSERT INTO document_versions (document_id, version, content, change_summary, created_by) VALUES (?, ?, ?, ?, ?)",
            (doc_db_id, data.get("version", "1.0.0"), data.get("content"), "初始版本", data.get("author", "system"))
        )

        conn.commit()
        conn.close()
        return {"id": doc_db_id, "doc_id": doc_id, **data}

    def update_document(self, doc_id, data):
        """更新文档"""
        conn = get_db()
        cursor = conn.cursor()

        # 获取原文档
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        old_doc = cursor.fetchone()

        tags = ",".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else data.get("tags", old_doc["tags"])
        version = data.get("version", old_doc["version"])

        cursor.execute(
            "UPDATE documents SET title = ?, content = ?, category = ?, tags = ?, version = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (data.get("title", old_doc["title"]), data.get("content", old_doc["content"]),
             data.get("category", old_doc["category"]), tags, version,
             data.get("status", old_doc["status"]), doc_id)
        )

        # 创建新版本记录
        if data.get("content") and data.get("content") != old_doc["content"]:
            cursor.execute(
                "INSERT INTO document_versions (document_id, version, content, change_summary, created_by) VALUES (?, ?, ?, ?, ?)",
                (doc_id, version, data.get("content"), data.get("change_summary", "更新版本"), data.get("author", "system"))
            )

        conn.commit()
        conn.close()
        return {"id": doc_id, **data}

    def delete_document(self, doc_id):
        """删除文档"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM document_versions WHERE document_id = ?", (doc_id,))
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()

    def get_document_versions(self, doc_id):
        """获取文档版本历史"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM document_versions WHERE document_id = ? ORDER BY created_at DESC", (doc_id,))
        versions = []
        for row in cursor.fetchall():
            versions.append({
                "id": row["id"],
                "version": row["version"],
                "content": row["content"],
                "change_summary": row["change_summary"],
                "created_by": row["created_by"],
                "created_at": row["created_at"]
            })
        conn.close()
        return {"versions": versions}

    # ==========  конец 知识库方法 ==========

    # ========== IM 即时通讯方法 ==========

    def get_conversations(self, user_id=None):
        """获取会话列表"""
        conn = get_db()
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT * FROM conversations WHERE participant_ids LIKE ? ORDER BY last_message_at DESC", (f'%{user_id}%',))
        else:
            cursor.execute("SELECT * FROM conversations ORDER BY last_message_at DESC")
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                "id": row["id"],
                "conversation_id": row["conversation_id"],
                "participant_ids": row["participant_ids"].split(","),
                "last_message_at": row["last_message_at"],
                "last_message_content": row["last_message_content"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        conn.close()
        return {"conversations": conversations}

    def get_conversation(self, conv_id):
        """获取单个会话"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conversations WHERE conversation_id = ?", (conv_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row["id"],
                "conversation_id": row["conversation_id"],
                "participant_ids": row["participant_ids"].split(","),
                "last_message_at": row["last_message_at"],
                "last_message_content": row["last_message_content"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None

    def create_conversation(self, data):
        """创建会话"""
        conn = get_db()
        cursor = conn.cursor()

        participants = data.get("participants", [])
        conversation_id = data.get("conversation_id", f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        participant_ids = ",".join(participants)

        try:
            cursor.execute(
                "INSERT INTO conversations (conversation_id, participant_ids) VALUES (?, ?)",
                (conversation_id, participant_ids)
            )
            conn.commit()
            return {"id": cursor.lastrowid, "conversation_id": conversation_id, **data}
        except sqlite3.IntegrityError:
            # 会话已存在，返回现有会话
            cursor.execute("SELECT * FROM conversations WHERE conversation_id = ?", (conversation_id,))
            row = cursor.fetchone()
            return {"id": row["id"], "conversation_id": conversation_id, **data} if row else None
        finally:
            conn.close()

    def get_messages(self, conv_id):
        """获取会话消息"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT 50", (conv_id,))
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row["id"],
                "conversation_id": row["conversation_id"],
                "sender_id": row["sender_id"],
                "receiver_id": row["receiver_id"],
                "content": row["content"],
                "message_type": row["message_type"],
                "is_read": bool(row["is_read"]),
                "created_at": row["created_at"]
            })
        conn.close()
        return {"messages": list(reversed(messages))}

    def get_all_messages(self):
        """获取所有消息（用于调试）"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages ORDER BY created_at DESC LIMIT 100")
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row["id"],
                "conversation_id": row["conversation_id"],
                "sender_id": row["sender_id"],
                "receiver_id": row["receiver_id"],
                "content": row["content"],
                "message_type": row["message_type"],
                "is_read": bool(row["is_read"]),
                "created_at": row["created_at"]
            })
        conn.close()
        return {"messages": messages}

    def send_message(self, data):
        """发送消息"""
        conn = get_db()
        cursor = conn.cursor()

        conversation_id = data.get("conversation_id")
        sender_id = data.get("sender_id")
        receiver_id = data.get("receiver_id")
        content = data.get("content")

        cursor.execute(
            "INSERT INTO messages (conversation_id, sender_id, receiver_id, content, message_type) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, sender_id, receiver_id, content, data.get("message_type", "text"))
        )
        msg_id = cursor.lastrowid

        # 更新会话
        cursor.execute(
            "UPDATE conversations SET last_message_at = CURRENT_TIMESTAMP, last_message_content = ?, updated_at = CURRENT_TIMESTAMP WHERE conversation_id = ?",
            (content[:100] if content else "", conversation_id)
        )

        # 更新未读计数
        cursor.execute(
            "INSERT OR REPLACE INTO unread_counts (user_id, conversation_id, count, updated_at) VALUES (?, ?, COALESCE((SELECT count FROM unread_counts WHERE user_id = ? AND conversation_id = ?), 0) + 1, CURRENT_TIMESTAMP)",
            (receiver_id, conversation_id, receiver_id, conversation_id)
        )

        conn.commit()
        conn.close()

        # WebSocket 推送
        asyncio.run(self.broadcast_message({"id": msg_id, **data}))

        return {"id": msg_id, **data}

    def mark_message_read(self, msg_id):
        """标记消息已读"""
        conn = get_db()
        cursor = conn.cursor()

        # 获取消息
        cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
        msg = cursor.fetchone()

        if msg:
            # 标记已读
            cursor.execute("UPDATE messages SET is_read = TRUE WHERE id = ?", (msg_id,))

            # 减少未读计数
            cursor.execute(
                "UPDATE unread_counts SET count = MAX(0, count - 1), updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND conversation_id = ?",
                (msg["receiver_id"], msg["conversation_id"])
            )

            conn.commit()

        conn.close()

    def get_unread_count(self, user_id):
        """获取未读消息数"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(count) as total FROM unread_counts WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return {"unread_count": row["total"] or 0}

    async def broadcast_message(self, data):
        """推送消息到 WebSocket 客户端"""
        if websocket_clients:
            message = json.dumps({"type": "message", "data": data}, ensure_ascii=False)
            await asyncio.gather(
                *[ws.send(message) for ws in websocket_clients],
                return_exceptions=True
            )

    # ==========  конец IM 方法 ==========

    # ========== Agent 编排引擎方法 ==========

    def get_agent_registry(self):
        """获取 Agent 注册列表"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agent_registry ORDER BY created_at DESC")
        agents = []
        for row in cursor.fetchall():
            agents.append({
                "id": row["id"],
                "agent_id": row["agent_id"],
                "agent_name": row["agent_name"],
                "status": row["status"],
                "capabilities": row["capabilities"].split(",") if row["capabilities"] else [],
                "current_load": row["current_load"],
                "max_load": row["max_load"],
                "last_heartbeat": row["last_heartbeat"]
            })
        conn.close()
        return {"agents": agents}

    def get_agent(self, agent_id):
        """获取单个 Agent 信息"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agent_registry WHERE agent_id = ?", (agent_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row["id"],
                "agent_id": row["agent_id"],
                "agent_name": row["agent_name"],
                "status": row["status"],
                "capabilities": row["capabilities"].split(",") if row["capabilities"] else [],
                "current_load": row["current_load"],
                "max_load": row["max_load"],
                "last_heartbeat": row["last_heartbeat"]
            }
        return None

    def register_agent(self, data):
        """注册 Agent"""
        conn = get_db()
        cursor = conn.cursor()

        agent_id = data.get("agent_id")
        capabilities = ",".join(data.get("capabilities", [])) if isinstance(data.get("capabilities"), list) else data.get("capabilities", "")

        try:
            cursor.execute(
                "INSERT INTO agent_registry (agent_id, agent_name, status, capabilities, max_load) VALUES (?, ?, ?, ?, ?)",
                (agent_id, data.get("agent_name"), data.get("status", "active"), capabilities, data.get("max_load", 100))
            )
            conn.commit()
            return {"id": cursor.lastrowid, **data}
        except sqlite3.IntegrityError:
            # 已存在，更新信息
            cursor.execute(
                "UPDATE agent_registry SET agent_name = ?, status = ?, capabilities = ?, last_heartbeat = CURRENT_TIMESTAMP WHERE agent_id = ?",
                (data.get("agent_name"), data.get("status", "active"), capabilities, agent_id)
            )
            conn.commit()
            return {"id": data.get("agent_id"), **data}
        finally:
            conn.close()

    def get_agent_skills(self, agent_id):
        """获取 Agent 技能"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agent_skills WHERE agent_id = ? ORDER BY proficiency DESC", (agent_id,))
        skills = []
        for row in cursor.fetchall():
            skills.append({
                "id": row["id"],
                "agent_id": row["agent_id"],
                "skill_id": row["skill_id"],
                "proficiency": row["proficiency"],
                "usage_count": row["usage_count"]
            })
        conn.close()
        return {"skills": skills}

    def get_orchestration_plans(self):
        """获取编排计划列表"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orchestration_plans ORDER BY created_at DESC")
        plans = []
        for row in cursor.fetchall():
            plans.append({
                "id": row["id"],
                "plan_id": row["plan_id"],
                "task_id": row["task_id"],
                "plan_name": row["plan_name"],
                "agent_sequence": row["agent_sequence"],
                "status": row["status"],
                "created_by": row["created_by"],
                "created_at": row["created_at"],
                "completed_at": row["completed_at"]
            })
        conn.close()
        return {"plans": plans}

    def get_orchestration_plan(self, plan_id):
        """获取单个编排计划"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orchestration_plans WHERE id = ?", (plan_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row["id"],
                "plan_id": row["plan_id"],
                "task_id": row["task_id"],
                "plan_name": row["plan_name"],
                "agent_sequence": json.loads(row["agent_sequence"]) if row["agent_sequence"] else [],
                "status": row["status"],
                "created_by": row["created_by"],
                "created_at": row["created_at"],
                "completed_at": row["completed_at"]
            }
        return None

    def create_orchestration_plan(self, data):
        """创建编排计划"""
        conn = get_db()
        cursor = conn.cursor()

        plan_id = data.get("plan_id", f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        agent_sequence = json.dumps(data.get("agent_sequence", []), ensure_ascii=False)

        cursor.execute(
            "INSERT INTO orchestration_plans (plan_id, task_id, plan_name, agent_sequence, status, created_by) VALUES (?, ?, ?, ?, ?, ?)",
            (plan_id, data.get("task_id"), data.get("plan_name"), agent_sequence, data.get("status", "pending"), data.get("created_by", "system"))
        )
        plan_db_id = cursor.lastrowid

        # 创建执行历史
        agent_seq = data.get("agent_sequence", [])
        for i, step in enumerate(agent_seq):
            cursor.execute(
                "INSERT INTO orchestration_history (plan_id, agent_id, step_number, action, status) VALUES (?, ?, ?, ?, ?)",
                (plan_db_id, step.get("agent_id"), i + 1, step.get("action"), "pending")
            )

        conn.commit()
        conn.close()
        return {"id": plan_db_id, "plan_id": plan_id, **data}

    def get_orchestration_history(self, plan_id):
        """获取编排历史"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orchestration_history WHERE plan_id = ? ORDER BY step_number", (plan_id,))
        history = []
        for row in cursor.fetchall():
            history.append({
                "id": row["id"],
                "plan_id": row["plan_id"],
                "agent_id": row["agent_id"],
                "step_number": row["step_number"],
                "action": row["action"],
                "result": row["result"],
                "status": row["status"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"]
            })
        conn.close()
        return {"history": history}

    def execute_orchestration_plan(self, plan_id):
        """执行编排计划"""
        conn = get_db()
        cursor = conn.cursor()

        # 获取计划
        cursor.execute("SELECT * FROM orchestration_plans WHERE id = ?", (plan_id,))
        plan = cursor.fetchone()

        if not plan:
            conn.close()
            return {"error": "计划不存在"}

        # 更新状态为运行中
        cursor.execute("UPDATE orchestration_plans SET status = 'running' WHERE id = ?", (plan_id,))

        # 获取第一个待执行的步骤
        cursor.execute("SELECT * FROM orchestration_history WHERE plan_id = ? AND status = 'pending' ORDER BY step_number LIMIT 1", (plan_id,))
        step = cursor.fetchone()

        if step:
            # 更新状态为运行中
            cursor.execute("UPDATE orchestration_history SET status = 'running', started_at = CURRENT_TIMESTAMP WHERE id = ?", (step["id"],))

            # 更新 Agent 负载
            cursor.execute("UPDATE agent_registry SET current_load = current_load + 1 WHERE agent_id = ?", (step["agent_id"],))

            # 记录执行日志
            cursor.execute(
                "INSERT INTO workflow_execution_logs (instance_id, node_id, action, result) VALUES (?, ?, ?, ?)",
                (plan_id, step["agent_id"], step["action"], "执行中")
            )

        conn.commit()
        conn.close()
        return {"success": True, "plan_id": plan_id, "current_step": step["id"] if step else None}

    def auto_assign_agents(self, task_id=None):
        """自动分配 Agent（基于负载和技能匹配）"""
        conn = get_db()
        cursor = conn.cursor()

        # 获取所有活跃 Agent
        cursor.execute("SELECT * FROM agent_registry WHERE status = 'active' AND current_load < max_load")
        available_agents = cursor.fetchall()

        if not available_agents:
            conn.close()
            return {"assigned_agent": None, "reason": "无可用 Agent"}

        # 简单轮询策略：选择负载最低的 Agent
        best_agent = min(available_agents, key=lambda a: a["current_load"] / a["max_load"])

        result = {
            "assigned_agent": best_agent["agent_id"],
            "agent_name": best_agent["agent_name"],
            "current_load": best_agent["current_load"],
            "max_load": best_agent["max_load"]
        }

        conn.close()
        return result

    # ==========  конец Agent 编排引擎方法 ==========

    # ========== RBAC 权限系统方法 ==========

    def get_roles(self):
        """获取角色列表"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM roles ORDER BY created_at DESC")
        roles = []
        for row in cursor.fetchall():
            roles.append({
                "id": row["id"],
                "role_id": row["role_id"],
                "role_name": row["role_name"],
                "description": row["description"],
                "permissions": row["permissions"].split(",") if row["permissions"] else [],
                "created_at": row["created_at"]
            })
        conn.close()
        return {"roles": roles}

    def get_role(self, role_id):
        """获取单个角色"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM roles WHERE role_id = ?", (role_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row["id"],
                "role_id": row["role_id"],
                "role_name": row["role_name"],
                "description": row["description"],
                "permissions": row["permissions"].split(",") if row["permissions"] else [],
                "created_at": row["created_at"]
            }
        return None

    def create_role(self, data):
        """创建角色"""
        conn = get_db()
        cursor = conn.cursor()

        role_id = data.get("role_id")
        permissions = ",".join(data.get("permissions", [])) if isinstance(data.get("permissions"), list) else data.get("permissions", "")

        try:
            cursor.execute(
                "INSERT INTO roles (role_id, role_name, description, permissions) VALUES (?, ?, ?, ?)",
                (role_id, data.get("role_name"), data.get("description"), permissions)
            )
            conn.commit()
            return {"id": cursor.lastrowid, **data}
        except sqlite3.IntegrityError:
            conn.close()
            return {"error": "角色已存在"}

    def update_role(self, role_id, data):
        """更新角色"""
        conn = get_db()
        cursor = conn.cursor()

        permissions = ",".join(data.get("permissions", [])) if isinstance(data.get("permissions"), list) else data.get("permissions", "")

        cursor.execute(
            "UPDATE roles SET role_name = ?, description = ?, permissions = ? WHERE role_id = ?",
            (data.get("role_name"), data.get("description"), permissions, role_id)
        )
        conn.commit()
        conn.close()
        return {"role_id": role_id, **data}

    def get_permissions(self):
        """获取权限列表"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM permissions ORDER BY resource_type, action")
        perms = []
        for row in cursor.fetchall():
            perms.append({
                "id": row["id"],
                "permission_id": row["permission_id"],
                "permission_name": row["permission_name"],
                "resource_type": row["resource_type"],
                "action": row["action"],
                "description": row["description"],
                "created_at": row["created_at"]
            })
        conn.close()
        return {"permissions": perms}

    def create_permission(self, data):
        """创建权限"""
        conn = get_db()
        cursor = conn.cursor()

        permission_id = data.get("permission_id")

        try:
            cursor.execute(
                "INSERT INTO permissions (permission_id, permission_name, resource_type, action, description) VALUES (?, ?, ?, ?, ?)",
                (permission_id, data.get("permission_name"), data.get("resource_type"), data.get("action"), data.get("description"))
            )
            conn.commit()
            return {"id": cursor.lastrowid, **data}
        except sqlite3.IntegrityError:
            conn.close()
            return {"error": "权限已存在"}

    def get_role_permissions(self, role_id):
        """获取角色权限"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_permissions WHERE role_id = ?", (role_id,))
        perms = []
        for row in cursor.fetchall():
            perms.append({
                "id": row["id"],
                "role_id": row["role_id"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "access_level": row["access_level"],
                "created_at": row["created_at"]
            })
        conn.close()
        return {"permissions": perms}

    def set_role_permissions(self, role_id, data):
        """设置角色数据权限"""
        conn = get_db()
        cursor = conn.cursor()

        # 删除现有权限
        cursor.execute("DELETE FROM data_permissions WHERE role_id = ?", (role_id,))

        # 添加新权限
        for perm in data.get("permissions", []):
            cursor.execute(
                "INSERT INTO data_permissions (role_id, resource_type, resource_id, access_level) VALUES (?, ?, ?, ?)",
                (role_id, perm.get("resource_type"), perm.get("resource_id", "*"), perm.get("access_level", "read"))
            )

        conn.commit()
        conn.close()
        return {"role_id": role_id, "count": len(data.get("permissions", []))}

    def get_user_roles(self, user_id):
        """获取用户角色"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_roles WHERE user_id = ?", (user_id,))
        roles = []
        for row in cursor.fetchall():
            roles.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "role_id": row["role_id"],
                "granted_by": row["granted_by"],
                "created_at": row["created_at"]
            })
        conn.close()
        return {"roles": roles}

    def assign_user_role(self, data):
        """分配用户角色"""
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO user_roles (user_id, role_id, granted_by) VALUES (?, ?, ?)",
                (data.get("user_id"), data.get("role_id"), data.get("granted_by", "system"))
            )
            conn.commit()
            return {"user_id": data.get("user_id"), "role_id": data.get("role_id")}
        except sqlite3.IntegrityError:
            conn.close()
            return {"error": "角色已分配"}

    def check_permission(self, user_id, resource, action):
        """检查用户权限"""
        conn = get_db()
        cursor = conn.cursor()

        # 获取用户所有角色
        cursor.execute("SELECT role_id FROM user_roles WHERE user_id = ?", (user_id,))
        user_roles = [row[0] for row in cursor.fetchall()]

        if not user_roles:
            conn.close()
            return {"allowed": False, "reason": "用户无角色"}

        # 检查角色权限
        allowed = False
        for role_id in user_roles:
            # 检查通用权限（permissions 字段）
            cursor.execute("SELECT permissions FROM roles WHERE role_id = ?", (role_id,))
            row = cursor.fetchone()
            if row and row[0]:
                perms = row[0].split(",")
                if f"{resource}:{action}" in perms or f"*:{action}" in perms or "*:*" in perms:
                    allowed = True
                    break

            # 检查数据权限
            cursor.execute("""
                SELECT access_level FROM data_permissions
                WHERE role_id = ? AND resource_type = ? AND (resource_id = ? OR resource_id = '*')
            """, (role_id, resource, user_id))
            data_perms = cursor.fetchall()
            if data_perms:
                for perm in data_perms:
                    if perm[0] in [action, "write", "*"]:
                        allowed = True
                        break

        conn.close()

        # 记录审计日志
        self.log_permission_audit(user_id, "check", resource, action, "allowed" if allowed else "denied")

        return {"allowed": allowed, "user_id": user_id, "resource": resource, "action": action}

    def log_permission_audit(self, user_id, action, resource_type, resource_id, result):
        """记录权限审计日志"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO permission_audit (user_id, action, resource_type, resource_id, result) VALUES (?, ?, ?, ?, ?)",
            (user_id, action, resource_type, resource_id, result)
        )
        conn.commit()
        conn.close()

    # ==========  конец RBAC 方法 ==========

    # ========== 财务模块方法 ==========

    def get_finance_ledger(self):
        """获取总账"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM finance_ledger ORDER BY created_at DESC LIMIT 100")
        entries = []
        for row in cursor.fetchall():
            entries.append({
                "id": row["id"],
                "entry_id": row["entry_id"],
                "entry_type": row["entry_type"],
                "account_code": row["account_code"],
                "debit": row["debit"],
                "credit": row["credit"],
                "balance": row["balance"],
                "description": row["description"],
                "created_at": row["created_at"]
            })
        conn.close()
        return {"entries": entries}

    def get_finance_accounts(self):
        """获取会计科目"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM finance_accounts ORDER BY account_code")
        accounts = []
        for row in cursor.fetchall():
            accounts.append({
                "id": row["id"],
                "account_code": row["account_code"],
                "account_name": row["account_name"],
                "account_type": row["account_type"],
                "balance": row["balance"]
            })
        conn.close()
        return {"accounts": accounts}

    def get_finance_receivables(self):
        """获取应收账款"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM finance_receivables ORDER BY due_date")
        receivables = []
        for row in cursor.fetchall():
            receivables.append({
                "id": row["id"],
                "invoice_id": row["invoice_id"],
                "customer_id": row["customer_id"],
                "amount": row["amount"],
                "paid_amount": row["paid_amount"],
                "status": row["status"],
                "due_date": row["due_date"]
            })
        conn.close()
        return {"receivables": receivables}

    def get_finance_payables(self):
        """获取应付账款"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM finance_payables ORDER BY due_date")
        payables = []
        for row in cursor.fetchall():
            payables.append({
                "id": row["id"],
                "bill_id": row["bill_id"],
                "vendor_id": row["vendor_id"],
                "amount": row["amount"],
                "paid_amount": row["paid_amount"],
                "status": row["status"],
                "due_date": row["due_date"]
            })
        conn.close()
        return {"payables": payables}

    def get_finance_budget(self):
        """获取预算"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM finance_budget ORDER BY created_at DESC")
        budgets = []
        for row in cursor.fetchall():
            budgets.append({
                "id": row["id"],
                "budget_id": row["budget_id"],
                "department": row["department"],
                "category": row["category"],
                "amount": row["amount"],
                "used_amount": row["used_amount"],
                "start_date": row["start_date"],
                "end_date": row["end_date"]
            })
        conn.close()
        return {"budgets": budgets}

    def get_finance_reports(self):
        """获取财务报表"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM finance_reports ORDER BY created_at DESC")
        reports = []
        for row in cursor.fetchall():
            reports.append({
                "id": row["id"],
                "report_id": row["report_id"],
                "report_type": row["report_type"],
                "period": row["period"],
                "data": json.loads(row["data"]) if row["data"] else {},
                "created_at": row["created_at"]
            })
        conn.close()
        return {"reports": reports}

    def get_finance_summary(self):
        """获取财务摘要"""
        conn = get_db()
        cursor = conn.cursor()

        # 总收入
        cursor.execute("SELECT COALESCE(SUM(debit), 0) FROM finance_ledger WHERE entry_type = 'income'")
        total_income = cursor.fetchone()[0] or 0

        # 总支出
        cursor.execute("SELECT COALESCE(SUM(credit), 0) FROM finance_ledger WHERE entry_type = 'expense'")
        total_expense = cursor.fetchone()[0] or 0

        # 应收账款
        cursor.execute("SELECT COALESCE(SUM(amount - paid_amount), 0) FROM finance_receivables WHERE status = 'pending'")
        total_receivable = cursor.fetchone()[0] or 0

        # 应付账款
        cursor.execute("SELECT COALESCE(SUM(amount - paid_amount), 0) FROM finance_payables WHERE status = 'pending'")
        total_payable = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_profit": total_income - total_expense,
            "total_receivable": total_receivable,
            "total_payable": total_payable,
            "working_capital": total_receivable - total_payable
        }

    def create_finance_ledger_entry(self, data):
        """创建总账分录"""
        conn = get_db()
        cursor = conn.cursor()

        entry_id = data.get("entry_id", f"JE{datetime.now().strftime('%Y%m%d%H%M%S')}")

        cursor.execute(
            "INSERT INTO finance_ledger (entry_id, entry_type, account_code, debit, credit, balance, description, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (entry_id, data.get("entry_type"), data.get("account_code"), data.get("debit", 0), data.get("credit", 0), data.get("balance", 0), data.get("description"), data.get("created_by", "system"))
        )
        conn.commit()
        conn.close()
        return {"id": cursor.lastrowid, "entry_id": entry_id}

    def create_receivable(self, data):
        """创建应收账款"""
        conn = get_db()
        cursor = conn.cursor()

        invoice_id = data.get("invoice_id") or f"INV{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cursor.execute(
            "INSERT INTO finance_receivables (invoice_id, customer_id, amount, status) VALUES (?, ?, ?, ?)",
            (invoice_id, data.get("customer_id"), data.get("amount", 0), data.get("status", "pending"))
        )
        conn.commit()
        conn.close()
        return {"id": cursor.lastrowid, "invoice_id": invoice_id}

    def create_payable(self, data):
        """创建应付账款"""
        conn = get_db()
        cursor = conn.cursor()

        bill_id = data.get("bill_id") or f"BILL{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cursor.execute(
            "INSERT INTO finance_payables (bill_id, vendor_id, amount, status) VALUES (?, ?, ?, ?)",
            (bill_id, data.get("vendor_id"), data.get("amount", 0), data.get("status", "pending"))
        )
        conn.commit()
        conn.close()
        return {"id": cursor.lastrowid, "bill_id": bill_id}

    def create_budget(self, data):
        """创建预算"""
        conn = get_db()
        cursor = conn.cursor()

        budget_id = data.get("budget_id", f"BG{datetime.now().strftime('%Y%m%d%H%M%S')}")

        cursor.execute(
            "INSERT INTO finance_budget (budget_id, department, category, amount, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?)",
            (budget_id, data.get("department"), data.get("category"), data.get("amount"), data.get("start_date"), data.get("end_date"))
        )
        conn.commit()
        conn.close()
        return {"id": cursor.lastrowid, "budget_id": budget_id}

    def create_finance_report(self, data):
        """创建财务报表"""
        conn = get_db()
        cursor = conn.cursor()

        report_id = data.get("report_id", f"RPT{datetime.now().strftime('%Y%m%d%H%M%S')}")

        cursor.execute(
            "INSERT INTO finance_reports (report_id, report_type, period, data, created_by) VALUES (?, ?, ?, ?, ?)",
            (report_id, data.get("report_type"), data.get("period"), json.dumps(data.get("data", {}), ensure_ascii=False), data.get("created_by", "system"))
        )
        conn.commit()
        conn.close()
        return {"id": cursor.lastrowid, "report_id": report_id}

    # ========== CRM 模块方法 ==========

    def get_crm_customers(self):
        """获取客户列表"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crm_customers ORDER BY created_at DESC")
        customers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"customers": customers}

    def get_crm_opportunities(self):
        """获取商机列表"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crm_opportunities ORDER BY created_at DESC")
        opportunities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"opportunities": opportunities}

    def get_crm_contracts(self):
        """获取合同列表"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crm_contracts ORDER BY created_at DESC")
        contracts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"contracts": contracts}

    def create_crm_customer(self, data):
        """创建客户"""
        conn = get_db()
        cursor = conn.cursor()

        customer_id = data.get("customer_id") or f"CUST{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cursor.execute(
            "INSERT INTO crm_customers (customer_id, customer_name, customer_type, industry, contact_person, contact_email, contact_phone, address, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (customer_id, data.get("customer_name"), data.get("customer_type", "enterprise"), data.get("industry"), data.get("contact_person"), data.get("contact_email"), data.get("contact_phone"), data.get("address"), data.get("status", "active"))
        )
        conn.commit()
        conn.close()
        return {"id": cursor.lastrowid, "customer_id": customer_id}

    def create_crm_opportunity(self, data):
        """创建商机"""
        conn = get_db()
        cursor = conn.cursor()

        opp_id = data.get("opp_id") or f"OPP{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cursor.execute(
            "INSERT INTO crm_opportunities (opp_id, customer_id, title, amount, stage, probability, expected_close_date, owner) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (opp_id, data.get("customer_id"), data.get("title"), data.get("amount", 0), data.get("stage", "lead"), data.get("probability", 10), data.get("expected_close_date"), data.get("owner"))
        )
        conn.commit()
        conn.close()
        return {"id": cursor.lastrowid, "opp_id": opp_id}

    def create_crm_contract(self, data):
        """创建合同"""
        conn = get_db()
        cursor = conn.cursor()

        contract_id = data.get("contract_id") or f"CONT{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cursor.execute(
            "INSERT INTO crm_contracts (contract_id, customer_id, opp_id, title, amount, status, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (contract_id, data.get("customer_id"), data.get("opp_id"), data.get("title"), data.get("amount"), data.get("status", "draft"), data.get("start_date"), data.get("end_date"))
        )
        conn.commit()
        conn.close()
        return {"id": cursor.lastrowid, "contract_id": contract_id}

    # ==========  конец 财务/CRM 模块方法 ==========

    # ========== BI 分析模块方法 ==========

    def get_bi_reports(self):
        """获取 BI 报表列表"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bi_reports ORDER BY created_at DESC")
        reports = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"reports": reports}

    def get_bi_dashboard(self):
        """获取 BI 仪表板数据（聚合数据）"""
        conn = get_db()
        cursor = conn.cursor()

        # 任务统计
        cursor.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
        task_stats = {row['status']: row['count'] for row in cursor.fetchall()}

        # 财务统计
        cursor.execute("SELECT COALESCE(SUM(debit), 0) as total FROM finance_ledger WHERE entry_type = 'income'")
        total_income = cursor.fetchone()['total'] or 0

        cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM finance_receivables WHERE status = 'pending'")
        total_receivable = cursor.fetchone()['total'] or 0

        # CRM 统计
        cursor.execute("SELECT stage, COUNT(*) as count FROM crm_opportunities GROUP BY stage")
        opp_stats = {row['stage']: row['count'] for row in cursor.fetchall()}

        cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM crm_contracts WHERE status = 'active'")
        contract_revenue = cursor.fetchone()['total'] or 0

        conn.close()

        return {
            "tasks": task_stats,
            "finance": {
                "total_income": total_income,
                "total_receivable": total_receivable
            },
            "crm": {
                "opportunities_by_stage": opp_stats,
                "contract_revenue": contract_revenue
            }
        }

    def create_bi_report(self, data):
        """创建 BI 报表"""
        conn = get_db()
        cursor = conn.cursor()

        report_id = data.get("report_id") or f"RPT{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cursor.execute(
            "INSERT INTO bi_reports (report_id, report_name, report_type, config, created_by) VALUES (?, ?, ?, ?, ?)",
            (report_id, data.get("report_name"), data.get("report_type", "custom"), json.dumps(data.get("config", {}), ensure_ascii=False), data.get("created_by", "system"))
        )
        conn.commit()
        conn.close()
        return {"id": cursor.lastrowid, "report_id": report_id}

    # ==========  конец BI 模块方法 ==========

    # ========== 通知中心方法 ==========

    def get_notifications(self, user_id="system"):
        """获取通知列表"""
        conn = get_db()
        cursor = conn.cursor()

        # 生成模拟通知数据
        now = datetime.now()
        notifications = [
            {
                "id": 1,
                "icon": "📋",
                "title": "新任务已分配",
                "message": "CEO 给您分配了一个新任务",
                "type": "task",
                "read": False,
                "time": "5 分钟前",
                "created_at": (now - timedelta(minutes=5)).isoformat()
            },
            {
                "id": 2,
                "icon": "💰",
                "title": "报销审批待处理",
                "message": "张三的差旅报销申请等待您的审批",
                "type": "approval",
                "read": False,
                "time": "15 分钟前",
                "created_at": (now - timedelta(minutes=15)).isoformat()
            },
            {
                "id": 3,
                "icon": "🤝",
                "title": "新客户签约",
                "message": "客户 A 已签署合同，金额 ¥500,000",
                "type": "crm",
                "read": True,
                "time": "1 小时前",
                "created_at": (now - timedelta(hours=1)).isoformat()
            },
            {
                "id": 4,
                "icon": "📊",
                "title": "月度报告已生成",
                "message": "2026 年 3 月经营分析报告已完成",
                "type": "system",
                "read": True,
                "time": "2 小时前",
                "created_at": (now - timedelta(hours=2)).isoformat()
            },
            {
                "id": 5,
                "icon": "⚠️",
                "title": "预算预警",
                "message": "工程部本月预算使用率已达 85%",
                "type": "system",
                "read": True,
                "time": "3 小时前",
                "created_at": (now - timedelta(hours=3)).isoformat()
            }
        ]

        conn.close()
        return {"notifications": notifications, "unread_count": sum(1 for n in notifications if not n["read"])}

    def mark_notification_read(self, data):
        """标记通知为已读"""
        notification_id = data.get("notification_id")
        # 实际应用中应该更新数据库
        return {"success": True, "notification_id": notification_id}

    # ==========  конец 通知中心方法 ==========

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
