# 变更日志

本文件记录项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [未发布]

### Added
- 添加 `.gitignore` 文件，排除敏感配置和临时文件
- 添加 `LICENSE` 文件（MIT License）
- 添加 `CONTRIBUTING.md` 贡献指南
- 添加 `CHANGELOG.md` 变更日志

### Fixed
- 修复 `install.sh` 中 `openclaw.json` 注册时的 `KeyError: 'list'` 问题
  - 处理 `agents` 字段没有 `list` 键的边界情况
  - 兼容不同的 `openclaw.json` 结构
  - 确保配置初始化后再添加 Agent

---

## [1.0.0] - 2026-03-23

### Added
- **公司架构系统** - 完整的 12 部门 AI Agent 协作框架
  - CEO（首席执行官）- 任务接收与分配
  - COO（首席运营官）- 运营管理
  - CFO（首席财务官）- 财务管理
  - CTO（首席技术官）- 技术决策
  - HR（人力总监）- 招聘管理
  - 财务总监 - 会计核算
  - 法务总监 - 合同管理
  - 市场总监 - 市场调研
  - 销售总监 - 销售管理
  - 工程总监 - 软件开发
  - 设计总监 - UI/UX 设计
  - QA 总监 - 质量检查

- **技能系统** - 5 个核心技能
  - `task_assignment` - 任务分配
  - `strategy_meeting` - 战略会议
  - `budget_planning` - 预算规划
  - `document_review` - 文档审查
  - `quality_check` - 质量检查

- **Dashboard 监控系统** - 17 个管理页面
  - 监控看板、任务看板、任务管理
  - 组织架构、会议管理、行事准则
  - 公司政策、技能管理、模型配置
  - 工作流、知识库、IM 通讯
  - Agent 编排、权限管理、财务管理
  - CRM、BI 分析

- **安装脚本** (`install.sh`)
  - 自动化 Agent 配置
  - API Key 自动查找
  - 工作空间初始化
  - 跨平台支持（macOS/Linux）

- **文档系统**
  - `README.md` - 项目说明和快速开始
  - `CLAUDE.md` - 开发者指南
  - `SYSTEM_GUIDE.md` - 系统架构说明

### Changed
- 优化 Agent 配置格式，使用 `agents.list` + `subagents.allowAgents`
- 改进 SOUL.md 表格格式，统一规范

### Technical Details
- 基于 OpenClaw 平台
- 支持多 Agent 协作
- 全互联协作网络（所有部门可互相沟通）
- QA 独立质检机制

---

## 版本说明

### 版本号规则

- **主版本号**：不兼容的 API 变更
- **次版本号**：向后兼容的功能新增
- **修订号**：向后兼容的问题修正

### 发布周期

- 主要版本：根据功能完成情况
- 补丁版本：随时发布

---

## 贡献者

感谢所有为这个项目做出贡献的人！

详见：[CONTRIBUTING.md](./CONTRIBUTING.md)
