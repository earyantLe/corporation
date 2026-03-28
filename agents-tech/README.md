# 🚀 技术团队 Agent · Tech Team

> 基于 Claude Code Agent Teams 和 Sub-Agents 理念打造的专业研发团队

---

## 快速开始

```bash
# 进入项目目录
cd corporation

# 运行安装脚本
./install-tech-team.sh
```

---

## 团队角色

| 角色 | ID | 擅长 | 使用场景 |
|------|-----|------|----------|
| 📋 产品经理 | `product-manager` | 需求分析、PRD 撰写、优先级管理 | 新功能规划、需求评审 |
| 💻 后端研发 | `backend-dev` | API 设计、服务端开发、数据库设计 | 接口开发、技术方案 |
| 🤖 算法研发 | `algorithm-dev` | 模型开发、算法优化、性能调优 | AI 功能、推荐系统 |
| 🎨 前端研发 | `frontend-dev` | 界面开发、组件设计、性能优化 | 页面开发、交互实现 |
| ✅ 测试工程师 | `qa-tester` | 测试设计、Bug 排查、质量保障 | 测试用例、验收测试 |

---

## 与 Corporation 主项目的关系

```
corporation/
├── agents/              # 公司管理层（CEO/COO/CTO 等 12 角色）
│   ├── ceo/
│   ├── cto/
│   └── ...
└── agents-tech/         # 技术执行层（本目录）
    ├── product-manager/
    ├── backend-dev/
    ├── algorithm-dev/
    ├── frontend-dev/
    └── qa-tester/
```

**管理层**（`agents/`）：负责战略决策、资源调度、跨部门协调  
**执行层**（`agents-tech/`）：负责具体技术任务的执行和交付

---

## 使用案例

### 案例 1：新功能开发

```bash
# 产品经理主导
openclaw agent --agent product-manager \
  --message "设计一个用户签到功能，包含每日签到、连续奖励、签到日历"

# 后端研发承接 API 开发
openclaw agent --agent backend-dev \
  --message "实现签到功能的 API：/api/v1/checkin, /api/v1/checkin/history"

# 前端研发承接页面开发
openclaw agent --agent frontend-dev \
  --message "开发签到页面，包含日历展示、签到按钮、奖励提示"

# 测试工程师设计测试用例
openclaw agent --agent qa-tester \
  --message "为签到功能设计测试用例，覆盖正常流程、边界场景、异常处理"
```

### 案例 2：算法功能集成

```bash
# 产品经理定义需求
openclaw agent --agent product-manager \
  --message "设计商品推荐功能，目标提升 CTR 到 5%"

# 算法研发设计模型
openclaw agent --agent algorithm-dev \
  --message "设计推荐算法方案，支持冷启动，P99 延迟<100ms"

# 后端研发集成服务
openclaw agent --agent backend-dev \
  --message "实现推荐 API：/api/v1/recommend/products，集成算法服务"

# 前端研发展示结果
openclaw agent --agent frontend-dev \
  --message "开发推荐商品展示组件，支持瀑布流加载"

# 测试工程师验收
openclaw agent --agent qa-tester \
  --message "设计推荐功能测试用例，包括准确性、性能、AB 测试"
```

---

## Agent Teams 工作流

参考 Claude Code 的 [Agent Teams](https://code.claude.com/docs/en/agent-teams) 理念：

```
┌─────────────────────────────────────────────────────────────┐
│                    技术负责人 (CTO)                          │
│                   Team Lead / Coordinator                    │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   产品经理       │ │   后端研发       │ │   前端研发       │
│ Product Manager │ │ Backend Dev     │ │ Frontend Dev    │
│                 │ │                 │ │                 │
│ • 需求分析       │ │ • API 设计       │ │ • 界面开发       │
│ • PRD 撰写       │ │ • 服务端开发     │ │ • 组件设计       │
│ • 优先级管理     │ │ • 数据库设计     │ │ • 性能优化       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   算法研发       │ │   测试工程师     │ │   设计 (外部)    │
│ Algorithm Dev   │ │ QA Tester       │ │ Designer        │
│                 │ │                 │ │                 │
│ • 模型开发       │ │ • 测试设计       │ │ • 视觉设计       │
│ • 算法优化       │ │ • Bug 排查       │ │ • 交互设计       │
│ • 性能调优       │ │ • 质量保障       │ │ • 原型设计       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 与 Sub-Agents 的对比

| 特性 | Corporation 主项目 | 技术团队 (本目录) |
|------|-------------------|------------------|
| 定位 | 公司管理层 | 技术执行层 |
| 角色 | CEO/COO/CFO/CTO 等 | PM/后端/前端/算法/QA |
| 擅长 | 战略决策、资源调度 | 具体技术任务执行 |
| 使用场景 | 跨部门协作、任务分配 | 功能开发、技术实现 |

---

## 输出规范

每个角色都有标准化的输出模板：

| 角色 | 核心输出 |
|------|----------|
| 产品经理 | PRD 文档、需求评审、竞品分析 |
| 后端研发 | API 设计、技术方案、数据库设计 |
| 算法研发 | 算法方案、实验报告、性能优化 |
| 前端研发 | 技术方案、组件设计、性能优化 |
| 测试工程师 | 测试用例、Bug 报告、测试报告 |

---

## 安装说明

### 方式 1：自动安装（推荐）

```bash
./install-tech-team.sh
```

### 方式 2：手动注册

```bash
# 注册产品经理
openclaw agents add product-manager \
  --label "产品经理" \
  --soul agents-tech/product-manager/SOUL.md

# 注册后端研发
openclaw agents add backend-dev \
  --label "后端研发" \
  --soul agents-tech/backend-dev/SOUL.md

# 注册算法研发
openclaw agents add algorithm-dev \
  --label "算法研发" \
  --soul agents-tech/algorithm-dev/SOUL.md

# 注册前端研发
openclaw agents add frontend-dev \
  --label "前端研发" \
  --soul agents-tech/frontend-dev/SOUL.md

# 注册测试工程师
openclaw agents add qa-tester \
  --label "测试工程师" \
  --soul agents-tech/qa-tester/SOUL.md
```

---

## 最佳实践

### 1. 明确角色边界

- **产品经理**：负责"做什么"和"为什么做"
- **研发团队**：负责"怎么做"和"何时交付"
- **测试工程师**：负责"做得怎么样"和"能否发布"

### 2. 使用标准化输出

每个角色都有标准输出模板，确保信息传递准确：
- PRD 文档 → 研发评审
- API 设计 → 前端对接
- 测试用例 → 验收标准

### 3. 迭代协作

```
需求评审 → 技术方案 → 开发实现 → 测试验收 → 上线发布
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
  PM        后端/前端    后端/前端    QA        PM
```

---

## 扩展技能

技术团队可复用 Corporation 主项目的技能：

| 技能 | 使用者 | 说明 |
|------|--------|------|
| `task_assignment` | 所有角色 | 任务分配给相关角色 |
| `document_review` | 所有角色 | 文档审查与合规检查 |
| `quality_check` | QA, CTO | 质量检查与验收 |

---

## 参考文档

- [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Claude Code Sub-Agents](https://code.claude.com/docs/en/sub-agents)
- [Corporation 主项目](../README.md)

---

<p align="center">🚀 高效协作，快速交付</p>
