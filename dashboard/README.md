# 📊 公司智能体监控看板

> 基于 SQLite 的实时监控和任务管理系统，支持审核机制、实时看板、任务干预、流转审计、热切换模型、技能管理、新闻聚合推送

---

## 🚀 快速启动

### 方式 1：使用启动脚本（推荐）

```bash
cd ~/code/corporation
./start-dashboard.sh
```

### 方式 2：直接启动

```bash
cd ~/code/corporation/dashboard
python3 app.py
```

---

## 📋 访问地址

启动服务后，在浏览器中访问：

| 页面 | 地址 | 功能 |
|------|------|------|
| **监控看板** | http://127.0.0.1:8080/ | 实时数据监控、新闻聚合、流转审计 |
| **任务看板** | http://127.0.0.1:8080/kanban.html | 看板视图、拖拽管理 |
| **任务管理** | http://127.0.0.1:8080/tasks.html | 任务 CRUD、干预操作 |
| **公司政策** | http://127.0.0.1:8080/policies.html | 公司制度、行事准则 |
| **技能管理** | http://127.0.0.1:8080/skills.html | Agent 技能配置 |
| **模型配置** | http://127.0.0.1:8080/models.html | AI 模型热切换 |
| **API 接口** | http://127.0.0.1:8080/api/stats | 统计数据 |

---

## 🎯 功能特性

### 监控看板（index.html）
- ✅ **实时统计** - 从 SQLite 数据库实时读取数据
- ✅ **任务分布图** - 已完成/进行中/待处理比例
- ✅ **Agent 状态** - 12 个部门 Agent 在线状态
- ✅ **最近活动** - 实时任务执行记录
- ✅ **绩效表格** - 各部门真实任务统计
- ✅ **新闻聚合** - AI/行业/公司新闻推送
- ✅ **流转审计** - 任务状态变更历史

### 任务看板（kanban.html）
- ✅ **看板视图** - 待处理/进行中/已完成三列
- ✅ **按 Agent 筛选** - 查看特定部门任务
- ✅ **点击流转** - 点击卡片快速切换状态
- ✅ **优先级显示** - 高优先级任务标记

### 任务管理（tasks.html）
- ✅ **任务列表** - 显示所有任务，支持搜索和筛选
- ✅ **新建任务** - 选择 Agent 并输入任务内容
- ✅ **状态管理** - 待处理 → 进行中 → 已完成
- ✅ **任务干预** - 暂停/恢复/转交/优先级调整
- ✅ **任务详情** - 查看和编辑任务
- ✅ **删除任务** - 支持删除操作

### 公司政策（policies.html）
- ✅ **政策分类** - 运营规范/财务制度/技术规范/人力资源/合规风控
- ✅ **政策管理** - 新增/编辑/删除政策
- ✅ **分类筛选** - 按类别查看政策

### 技能管理（skills.html）
- ✅ **技能列表** - 显示所有 Agent 技能
- ✅ **启用/禁用** - 开关控制技能状态
- ✅ **新增技能** - 自定义技能配置

### 模型配置（models.html）
- ✅ **模型管理** - 配置多个 AI 模型
- ✅ **热切换** - 修改后即时生效，无需重启
- ✅ **多提供商** - 支持阿里百炼、智谱、OpenAI 等

### 数据存储
- 💾 **SQLite 数据库** - 持久化存储所有数据
- 📁 **数据库位置** - `data/corporation.db`
- 🔄 **自动同步** - 页面每 5 秒自动刷新
- 🔌 **WebSocket** - 实时推送任务变化

---

## 📁 文件结构

```
dashboard/
├── app.py              # Python 后端服务（SQLite + API + WebSocket）
├── index.html          # 监控看板（含新闻、审计）
├── kanban.html         # 任务看板视图
├── tasks.html          # 任务管理（含干预功能）
├── policies.html       # 公司政策
├── skills.html         # 技能管理
├── models.html         # 模型配置
└── README.md           # 使用说明

data/
└── corporation.db      # SQLite 数据库（自动生成）
```

---

## 🔌 API 接口

### 任务相关
```bash
# 获取任务列表
curl http://127.0.0.1:8080/api/tasks

# 创建任务
curl -X POST http://127.0.0.1:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "ceo", "content": "测试任务", "status": "pending"}'

# 更新任务状态
curl -X POST http://127.0.0.1:8080/api/tasks/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

# 任务干预（暂停/恢复/转交/优先级）
curl -X POST http://127.0.0.1:8080/api/tasks/1/intervene \
  -H "Content-Type: application/json" \
  -d '{"action": "pause"}'

# 删除任务
curl -X DELETE http://127.0.0.1:8080/api/tasks/1
```

### 审核相关
```bash
# 获取审核列表
curl http://127.0.0.1:8080/api/reviews

# 创建审核
curl -X POST http://127.0.0.1:8080/api/reviews \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "reviewer_id": "qa", "decision": "approved", "comments": "通过"}'

# 更新审核状态
curl -X POST http://127.0.0.1:8080/api/reviews/1/status \
  -H "Content-Type: application/json" \
  -d '{"decision": "approved"}'
```

### 流转审计
```bash
# 获取审计日志
curl http://127.0.0.1:8080/api/audit-logs
curl http://127.0.0.1:8080/api/audit-logs?task_id=1  # 指定任务
```

### 模型管理
```bash
# 获取模型列表
curl http://127.0.0.1:8080/api/models

# 更新模型配置
curl -X POST http://127.0.0.1:8080/api/models/qwen3.5-plus \
  -H "Content-Type: application/json" \
  -d '{"name": "Qwen3.5 Plus", "provider": "bailian", "enabled": true}'
```

### 技能管理
```bash
# 获取技能列表
curl http://127.0.0.1:8080/api/skills

# 更新技能配置
curl -X POST http://127.0.0.1:8080/api/skills/task_assignment \
  -H "Content-Type: application/json" \
  -d '{"name": "任务分配", "enabled": true}'
```

### 新闻管理
```bash
# 获取新闻列表
curl http://127.0.0.1:8080/api/news
curl http://127.0.0.1:8080/api/news?category=ai  # 按分类

# 创建新闻
curl -X POST http://127.0.0.1:8080/api/news \
  -H "Content-Type: application/json" \
  -d '{"title": "公司新闻", "summary": "...", "category": "company"}'
```

### 其他
```bash
# 获取统计数据
curl http://127.0.0.1:8080/api/stats

# 获取绩效统计
curl http://127.0.0.1:8080/api/performance

# 获取 Agent 列表
curl http://127.0.0.1:8080/api/agents

# 健康检查
curl http://127.0.0.1:8080/api/health
```

---

## 📊 数据库表结构

### tasks 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 任务 ID（自增） |
| agent_id | TEXT | Agent ID |
| content | TEXT | 任务内容 |
| status | TEXT | 状态（pending/processing/completed） |
| tokens | INTEGER | Token 消耗 |
| result | TEXT | 执行结果 |
| priority | TEXT | 优先级（high/normal/low） |
| assigned_to | TEXT | 转交目标 |
| paused | BOOLEAN | 是否暂停 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| completed_at | TIMESTAMP | 完成时间 |

### reviews 表（审核）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 审核 ID |
| task_id | INTEGER | 关联任务 |
| reviewer_id | TEXT | 审核人 |
| decision | TEXT | 决定（pending/approved/rejected） |
| comments | TEXT | 批注 |

### audit_logs 表（流转审计）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 日志 ID |
| task_id | INTEGER | 关联任务 |
| from_status | TEXT | 原状态 |
| to_status | TEXT | 新状态 |
| operator | TEXT | 操作人 |
| reason | TEXT | 原因 |

### models 表（模型配置）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 模型 ID |
| model_id | TEXT | 模型标识 |
| name | TEXT | 模型名称 |
| provider | TEXT | 提供商 |
| enabled | BOOLEAN | 是否启用 |

### skills 表（技能管理）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 技能 ID |
| skill_id | TEXT | 技能标识 |
| name | TEXT | 技能名称 |
| description | TEXT | 描述 |
| enabled | BOOLEAN | 是否启用 |

### news 表（新闻）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 新闻 ID |
| title | TEXT | 标题 |
| summary | TEXT | 摘要 |
| url | TEXT | 链接 |
| source | TEXT | 来源 |
| category | TEXT | 分类 |

---

## 🎨 界面说明

### 监控看板
- **核心指标** - 活跃 Agent、今日任务、Token 消耗
- **任务分布图** - 环形图显示任务状态分布
- **Agent 状态** - 12 个部门卡片
- **最近活动** - 任务执行记录
- **绩效表格** - 各部门任务数、完成率
- **新闻聚合** - AI/行业/公司新闻
- **流转审计** - 状态变更历史

### 任务看板
- **三列布局** - 待处理/进行中/已完成
- **Agent 筛选** - 按部门查看任务
- **优先级标记** - 高优先级任务显示火焰图标
- **暂停标记** - 暂停任务显示暂停图标

### 任务管理
- **统计卡片** - 全部/进行中/已完成/待处理数量
- **筛选按钮** - 按状态筛选任务
- **搜索框** - 关键词搜索
- **任务列表** - 表格显示任务详情
- **干预操作** - 暂停/恢复/优先级调整

---

## 🔌 WebSocket 实时推送

服务启动后，WebSocket 服务器监听在 `ws://127.0.0.1:8765/`

推送事件类型：
- `task_created` - 任务创建
- `task_status_changed` - 任务状态变更
- `task_intervened` - 任务干预
- `news` - 新闻推送

---

## ⚠️ 注意事项

1. **端口占用**：默认使用 8080（HTTP）和 8765（WebSocket）端口
2. **数据目录**：确保 `data/` 目录存在且有写入权限
3. **依赖安装**：需要安装 `websockets` 模块 (`pip3 install websockets`)

---

## 🛠️ 停止服务

```bash
# 停止服务
pkill -f 'dashboard/app.py'

# 查看日志
tail -f logs/dashboard.log
```

---

**🏢 公司智能体监控看板 - 让数据驱动决策！**
