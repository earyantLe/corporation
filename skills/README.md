# 技能系统 · Skills

>  Corporation 项目的核心技能系统，参考 edict 项目设计

---

## 技能列表

### 核心技能（6 个）

| 技能 ID | 名称 | 使用者 | 说明 |
|---------|------|--------|------|
| `task_assignment` | 任务分配 | CEO, COO | 任务接收与分配给相关部门 |
| `quality_check` | 质量检查 | QA | 质量检查与验收 |
| `strategy_meeting` | 战略会议 | CEO, COO, CTO | 战略会议组织与协调 |
| `budget_planning` | 预算规划 | CFO, Finance | 预算制定与成本效益分析 |
| `document_review` | 文档审查 | Legal, QA | 文档审查与合规检查 |
| `task_tracking` | 任务追踪 | CEO, COO, QA | 任务状态同步和追踪 |

### CTO 技能组（3 个）

| 技能 ID | 名称 | 说明 |
|---------|------|------|
| `tech_architecture` | 技术架构 | 技术架构设计与选型 |
| `tech_decision` | 技术决策 | 技术选型与决策评估 |
| `code_review` | 代码审查 | 代码审查与技术评审 |

### Engineering 技能组（4 个）

| 技能 ID | 名称 | 说明 |
|---------|------|------|
| `coding` | 代码开发 | 代码编写与实现 |
| `debugging` | 调试排查 | 问题调试与排查 |
| `refactoring` | 代码重构 | 代码重构与优化 |
| `deployment` | 部署发布 | 部署与发布管理 |

### QA 增强技能组（3 个）

| 技能 ID | 名称 | 说明 |
|---------|------|------|
| `unit_testing` | 单元测试 | 单元测试编写与执行 |
| `integration_testing` | 集成测试 | 集成测试与系统测试 |
| `bug_tracking` | 缺陷追踪 | 缺陷管理与追踪 |

### 协作技能组（4 个）

| 技能 ID | 名称 | 使用者 | 说明 |
|---------|------|--------|------|
| `status_report` | 状态报告 | 全员 | 进度状态报告 |
| `blocker_escalation` | 阻塞上报 | 全员 | 阻塞问题上报与协调 |
| `handoff` | 工作交接 | 全员 | 部门间工作交接 |
| `collaboration` | 跨部门协作 | COO, 全员 | 跨部门协作协议 |

---

## 技能模板

每个技能都遵循统一的模板格式：

```markdown
# {Emoji} {技能名称} · {SkillName}

> 版本：v1.0 | 最后更新：{YYYY-MM-DD} | 维护者：{角色}

## 变更历史
## 技能描述
## 使用方法
## 使用示例
## 检查清单
## 注意事项
## 相关技能
```

详见 [`skills/SKILL_TEMPLATE.md`](skills/SKILL_TEMPLATE.md)

---

## 技能注册

技能注册表 [`skills/registry.json`](skills/registry.json) 包含：
- 所有技能的元数据（ID、名称、路径、使用者）
- Agent 与技能的映射关系

---

## Agent 技能映射

| Agent | 技能 |
|-------|------|
| CEO | task_assignment, strategy_meeting, task_tracking, status_report, blocker_escalation |
| COO | task_assignment, task_tracking, strategy_meeting, collaboration, handoff, status_report, blocker_escalation |
| CTO | tech_architecture, tech_decision, code_review, deployment, status_report |
| CFO | budget_planning, document_review, status_report |
| Finance | budget_planning, document_review, status_report |
| HR | document_review, status_report |
| Legal | document_review, status_report |
| Marketing | document_review, status_report |
| Sales | document_review, status_report |
| Engineering | coding, debugging, refactoring, deployment, code_review, unit_testing, status_report |
| Design | document_review, quality_check, status_report |
| QA | quality_check, document_review, task_tracking, unit_testing, integration_testing, bug_tracking, status_report |

---

## 看板集成

技能可以与看板系统集成，使用 `kanban_update.py` 命令：

```bash
# 状态更新
python3 scripts/kanban_update.py state <task-id> <state> "<说明>"

# 流转记录
python3 scripts/kanban_update.py flow <task-id> "<from>" "<to>" "<remark>"

# 实时进展
python3 scripts/kanban_update.py progress <task-id> "<当前在做什么>" "<计划 1✅|计划 2🔄|计划 3>"

# 子任务详情
python3 scripts/kanban_update.py todo <task-id> <todo_id> "<title>" <status> --detail "<产出详情>"
```

---

## 技能开发流程

### 1. 创建技能目录
```bash
mkdir -p skills/{skill_id}
```

### 2. 创建 SKILL.md
复制模板并填充内容：
```bash
cp skills/SKILL_TEMPLATE.md skills/{skill_id}/SKILL.md
```

### 3. 更新注册表
编辑 `skills/registry.json` 添加新技能

### 4. 更新 Agent SOUL.md
为相关 Agent 添加技能引用

---

## 最佳实践

### 技能设计原则
1. **单一职责**: 每个技能只做一件事
2. **可复用**: 技能应可被多个 Agent 使用
3. **标准化**: 遵循统一的模板和格式
4. **示例驱动**: 至少包含 3 个使用示例
5. **异常处理**: 包含异常场景的处理示例

### 技能命名规范
- 使用 `snake_case` 格式
- 名称应清晰描述技能用途
- 长度控制在 20 个字符以内

### 技能版本控制
- 每次变更更新版本号
- 记录变更历史
- 重大变更升级主版本号

---

## 参考资料

- [edict 项目](https://github.com/cft0808/edict) - 技能系统设计参考
- [OpenClaw 文档](https://openclaw.ai) - Agent 框架文档

---

<p align="center">🏢 技能系统 v1.0 | 好好工作，天天向上</p>
