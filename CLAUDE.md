# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 项目概述

**公司集团 (Corporation)** - 基于 OpenClaw 框架的 AI 多 Agent 协作系统，采用通用公司架构模拟 12 个部门角色的协作。

## 核心架构

### 12 Agent 角色

```
CEO (首席执行官) → 战略决策、任务分配、最终审批
├── COO (首席运营官) → 日常运营、人力资源、进度管理
├── CFO (首席财务官) → 财务分析、预算控制、法务
└── CTO (首席技术官) → 技术决策、架构设计、技术管理
    ├── 工程 (Engineering) → 核心开发
    ├── 设计 (Design) → UI/UX 设计
    ├── 销售 (Sales) → 客户开发
    └── QA → 质量检查

独立部门：
├── 人力 (HR) → 团队建设、绩效评估
├── 财务 (Finance) → 财务报表、成本控制
├── 法务 (Legal) → 合同审查、合规检查
└── 市场 (Marketing) → 市场调研、品牌推广
```

### 文件结构约定

- **Agent 人格**: `agents/{role}/SOUL.md` - 定义角色身份、职责、工作流、输出规范
- **技能定义**: `skills/{skill_name}/SKILL.md` - 定义可复用的工作技能
- **权限配置**: `~/.openclaw/openclaw.json` - Agent 注册和权限矩阵

### 标准工作流程

1. **CEO 接收任务** → 分析类型 → 分配给相关部门
2. **部门执行** → 工程/设计/市场等完成各自任务
3. **QA 质量检查** → 检查产出质量，不合格则打回
4. **CEO 最终审批** → 审批通过后提交给用户

## 开发规范

### Agent 人格文件 (SOUL.md) 结构

```markdown
# {角色名称}

## 身份
## 核心职责
## 工作流
## 输出规范 (含模板)
## 行为准则 (✅ 应该做 / ❌ 不应该做)
## 特殊能力
## 与其他角色的关系
## 示例对话
## 人格特质
## 开场白模板
```

### 技能文件 (SKILL.md) 结构

```markdown
# {技能名称}

## 技能描述 (使用者、适用场景)
## 使用方法 (命令格式、输出格式)
## 使用示例
## 注意事项
```

### 权限矩阵

所有 12 个部门可以互相协作（权限配置在 `openclaw.json` 中通过 `allowAgents` 字段定义）。

## 常用命令

```bash
# 安装依赖
./install.sh

# 启动 Gateway
openclaw gateway start

# 配置消息渠道
openclaw channels add --type feishu --agent ceo

# 添加新 Agent
openclaw agents add {agent_id}
```

## 已知问题与修复

### 已修复问题

1. **install.sh API Key 查找路径** - 优先从 ceo agent 的多个可能位置查找
2. **install.sh 错误处理** - 增加了详细的错误日志和失败回显
3. **COO SOUL.md 表格格式** - 修复了"与其他角色关系"表格的不规范条目
4. **CFO SOUL.md 表格格式** - 同上
5. **budget_planning SKILL.md 使用者描述** - 明确 CFO 为主要使用者
6. **README.md 跨平台安装说明** - 添加了 Linux 安装命令
7. **Agent 身份配置** - install.sh 现在自动配置 workspace 的 IDENTITY.md、SOUL.md 和 AGENTS.md
8. **OpenClaw 配置格式** - 修复了 Agent 注册时使用的正确配置格式（`agents.list` + `subagents.allowAgents`）

### 运行时配置

install.sh 会自动为每个 Agent 配置 workspace 目录：
- `~/.openclaw/workspace-{id}/SOUL.md` - 完整角色定义（从 `agents/{id}/SOUL.md` 复制）
- `~/.openclaw/workspace-{id}/IDENTITY.md` - 角色身份摘要（自动生成）
- `~/.openclaw/workspace-{id}/AGENTS.md` - 可协作的子 Agent 列表（从 openclaw.json 读取）

### 待优化

- CFO 和 财务 角色职责边界需在运行时通过具体任务分配进一步明确

## 测试验证

```bash
# 测试 CEO Agent
openclaw agent --agent ceo --message "你好，请介绍一下自己"

# 测试 CTO Agent
openclaw agent --agent cto --message "设计一个电商网站的技术架构"

# 测试任务分配
openclaw agent --agent ceo --message "公司要开发一个电商网站，请组织各部门完成"
```

## 关键设计决策

1. **角色驱动**: 每个 Agent 通过 SOUL.md 定义独立人格，而非共享 prompt
2. **质量门禁**: QA 作为独立的质检角色，所有产出必须经过检查
3. **技能复用**: 通用能力（如任务分配、质量检查）封装为 SKILL 文件
4. **全互联协作**: 所有部门可以互相沟通，没有严格的层级限制
5. **企业级平台**: Dashboard 提供 17 个管理页面，覆盖企业运营全流程

## Dashboard 监控系统

### 页面列表 (17 个)

| 页面 | 文件名 | 功能描述 |
|------|--------|----------|
| 监控看板 | `index.html` | 系统状态、Agent 绩效、实时活动 |
| 任务看板 | `kanban.html` | 任务看板视图、拖拽管理 |
| 任务管理 | `tasks.html` | 任务 CRUD、分配、干预 |
| 组织架构 | `org.html` | 12 Agent 角色、职责说明 |
| 会议管理 | `meeting.html` | 会议安排、记录 |
| 行事准则 | `conduct.html` | 员工行为规范 |
| 公司政策 | `policies.html` | 政策制度管理 |
| 技能管理 | `skills.html` | 技能配置、启用/禁用 |
| 模型配置 | `models.html` | AI 模型配置、热切换 |
| 工作流 | `workflow.html` | 可视化流程设计器、5 个预置模板 |
| 知识库 | `knowledge.html` | 文档管理、版本控制、搜索 |
| IM 通讯 | `im.html` | Agent-User 实时沟通 |
| Agent 编排 | `orchestration.html` | Agent 注册、负载均衡、编排计划 |
| 权限管理 | `rbac.html` | RBAC 角色权限管理 |
| 财务管理 | `finance.html` | 总账、应收/应付、预算 |
| CRM | `crm.html` | 客户档案、商机漏斗、合同管理 |
| BI 分析 | `bi.html` | 仪表板、数据可视化、自定义报表 |

### API 端点

```
任务管理：/api/tasks, /api/reviews, /api/audit-logs
工作流：/api/workflows, /api/workflows/{id}/nodes, /api/workflows/{id}/execute
知识库：/api/documents, /api/documents/{id}/versions
IM: /api/messages, /api/conversations, /api/unread
Agent 编排：/api/orchestration, /api/orchestration/auto-assign, /api/agents
RBAC: /api/roles, /api/permissions, /api/user-roles, /api/permission/check
财务：/api/finance/ledger, /api/finance/receivables, /api/finance/payables, /api/finance/budget, /api/finance/summary
CRM: /api/crm/customers, /api/crm/opportunities, /api/crm/contracts
BI: /api/bi/reports, /api/bi/dashboard
```
