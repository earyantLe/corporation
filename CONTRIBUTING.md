# 贡献指南

感谢你考虑为 **公司集团 (Corporation)** 项目做出贡献！🎉

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [问题报告](#问题报告)
- [功能请求](#功能请求)

---

## 行为准则

本项目采用开放、包容的行为准则。请尊重所有贡献者和用户。

---

## 如何贡献

### 1. Fork 项目

```bash
# 在 GitHub 上点击 Fork 按钮
```

### 2. Clone 你的 Fork

```bash
git clone https://github.com/YOUR_USERNAME/corporation.git
cd corporation
```

### 3. 创建分支

```bash
# 功能开发
git checkout -b feature/your-feature-name

# Bug 修复
git checkout -b fix/issue-number-description
```

### 4. 进行修改

- 阅读 [CLAUDE.md](./CLAUDE.md) 了解项目结构
- 遵循代码规范
- 添加必要的测试

### 5. 提交更改

```bash
git add .
git commit -m "feat: 添加新功能"
```

### 6. 推送并创建 PR

```bash
git push origin feature/your-feature-name
# 然后在 GitHub 上创建 Pull Request
```

---

## 开发流程

### 环境设置

```bash
# 安装依赖
./install.sh

# 验证安装
openclaw agent --agent ceo --message "你好"
```

### 添加新 Agent

1. 在 `agents/` 目录创建新文件夹
2. 创建 `SOUL.md` 定义角色
3. 在 `install.sh` 中添加角色定义
4. 更新 `openclaw.json` 配置

### 添加新技能

1. 在 `skills/` 目录创建新文件夹
2. 创建 `SKILL.md` 定义技能
3. 在相关 Agent 的 SOUL.md 中引用

---

## 代码规范

### Shell 脚本

- 使用 `#!/bin/bash`
- 变量使用双引号：`"$var"`
- 错误检查：`set -e`

### Markdown 文件

- 使用 UTF-8 编码
- 标题使用 ATX 风格（#）
- 列表使用 `-` 或 `*`

### JSON 配置

- 2 空格缩进
- 键名使用双引号
- 保持键的字母顺序

---

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Type 类型

| 类型 | 描述 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具/配置 |

### 示例

```bash
feat(ceo): 添加任务优先级分析功能
fix(install): 修复 API Key 查找路径问题
docs(readme): 更新安装说明
refactor(agents): 优化 Agent 初始化逻辑
```

---

## 问题报告

### Bug 报告

请使用 GitHub Issues，并包含：

1. **问题描述**：清晰描述问题
2. **复现步骤**：如何复现问题
3. **期望行为**：应该发生什么
4. **实际行为**：实际发生了什么
5. **环境信息**：
   - OpenClaw 版本
   - 操作系统
   - Python/Node.js 版本
6. **日志输出**：相关错误日志

### 安全问题

发现安全漏洞请**不要**公开报告，而是直接联系维护者。

---

## 功能请求

欢迎新功能建议！请包含：

1. **功能描述**：想要什么功能
2. **使用场景**：为什么需要这个功能
3. **实现建议**：如何实现（可选）

---

## 审查流程

1. 所有 PR 需要至少一个维护者审查
2. CI 检查必须通过
3. 代码需要符合项目规范
4. 新功能需要包含文档更新

---

## 常见问题

### Q: 如何测试我的修改？

```bash
# 运行安装脚本
./install.sh

# 测试相关 Agent
openclaw agent --agent ceo --message "测试消息"
```

### Q: 如何添加新语言支持？

在相应 Agent 的 SOUL.md 中添加多语言支持，并更新文档。

### Q: 我的 PR 多久会被审查？

通常在 1-3 个工作日内，请耐心等待。

---

## 致谢

感谢所有为这个项目做出贡献的人！🙏

---

有任何问题？欢迎在 Issues 中提问！