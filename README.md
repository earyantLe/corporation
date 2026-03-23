# 🏢 Corporation · OpenClaw Skills

> 通用公司架构的 AI 多 Agent 协作技能包

---

## 快速开始

```bash
# 克隆项目
git clone https://github.com/earyant/corporation.git
cd corporation

# 运行安装脚本
./install.sh
```

---

## 技能列表

| 技能 | 使用者 | 说明 |
|------|--------|------|
| `task_assignment` | CEO, COO | 任务分配给相关部门 |
| `quality_check` | QA | 质量检查与验收 |
| `strategy_meeting` | CEO, COO, CTO | 战略会议组织 |
| `budget_planning` | CFO | 预算规划与审批 |
| `document_review` | Legal, QA | 文档审查与合规检查 |

---

## Agent 角色

| ID | 角色 | 擅长 |
|----|------|------|
| `ceo` | 首席执行官 | 需求理解、资源调度、最终决策 |
| `coo` | 首席运营官 | 团队管理、流程优化、资源协调 |
| `cfo` | 首席财务官 | 成本评估、预算规划、ROI 分析 |
| `cto` | 首席技术官 | 技术方案、架构评审、技术风险评估 |
| `hr` | 人力总监 | 人员管理、培训、绩效考核 |
| `finance` | 财务总监 | 财务分析、报表编制、预算跟踪 |
| `legal` | 法务总监 | 合同审核、法律风险、合规审查 |
| `marketing` | 市场总监 | 市场分析、营销策略、品牌管理 |
| `sales` | 销售总监 | 客户沟通、商务谈判、销售管理 |
| `engineering` | 工程总监 | 软件开发、系统设计、技术攻坚 |
| `design` | 设计总监 | 界面设计、用户体验、视觉创意 |
| `qa` | QA 总监 | 质量审核、测试用例、验收标准 |

---

## 使用案例

```bash
# 测试 CEO Agent
openclaw agent --agent ceo --message "公司要开发一个电商网站，请组织各部门完成"

# 测试 CTO Agent
openclaw agent --agent cto --message "设计一个电商网站的技术架构"
```

---

## 项目结构

```
corporation/
├── README.md
├── install.sh
├── agents/           # 12 个 Agent 的 SOUL.md 人格定义
│   ├── ceo/
│   ├── coo/
│   └── ...
└── skills/           # 可复用技能
    ├── task_assignment/
    ├── quality_check/
    └── ...
```

---

<p align="center">🏢 好好工作，天天向上</p>
