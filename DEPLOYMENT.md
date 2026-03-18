# 🏢 公司智能体部署说明

> 部署完成时间：2026-03-18
> 状态：✅ 已部署就绪

---

## ✅ 部署检查清单

| 项目 | 状态 | 说明 |
|------|------|------|
| OpenClaw Gateway | ✅ 运行中 | 端口 18789 |
| CEO Agent | ✅ 已配置 | workspace-ceo |
| COO Agent | ✅ 已配置 | workspace-coo |
| CFO Agent | ✅ 已配置 | workspace-cfo |
| CTO Agent | ✅ 已配置 | workspace-cto |
| HR Agent | ✅ 已配置 | workspace-hr |
| Finance Agent | ✅ 已配置 | workspace-finance |
| Legal Agent | ✅ 已配置 | workspace-legal |
| Marketing Agent | ✅ 已配置 | workspace-marketing |
| Sales Agent | ✅ 已配置 | workspace-sales |
| Engineering Agent | ✅ 已配置 | workspace-engineering |
| Design Agent | ✅ 已配置 | workspace-design |
| QA Agent | ✅ 已配置 | workspace-qa |

---

## 📋 访问方式

### 1. Dashboard 访问

```bash
# 浏览器打开
http://127.0.0.1:18789/
```

### 2. CLI 命令测试

```bash
# 测试 CEO Agent
openclaw agent --agent ceo --message "你好，请介绍一下公司架构"

# 测试 CTO Agent
openclaw agent --agent cto --message "设计一个电商网站的技术架构"

# 测试 QA Agent
openclaw agent --agent qa --message "制定一个产品质量检测计划"

# 测试 COO Agent
openclaw agent --agent coo --message "组建一个 10 人的开发团队"

# 测试 CFO Agent
openclaw agent --agent cfo --message "规划一个项目的预算"
```

### 3. 多 Agent 协作测试

```bash
# 完整战略会议场景
openclaw agent --agent ceo --message "公司要开发一个 AI 智能客服系统，需要你组织 CTO、CFO、COO 开个战略会议，讨论技术方案、预算和团队组建。请输出会议纪要和行动计划。"
```

---

## 📁 工作空间文件位置

| Agent | 工作空间路径 | SOUL.md 位置 |
|-------|-------------|-------------|
| CEO | `~/.openclaw/workspace-ceo/` | `agents/ceo/SOUL.md` |
| COO | `~/.openclaw/workspace-coo/` | `agents/coo/SOUL.md` |
| CFO | `~/.openclaw/workspace-cfo/` | `agents/cfo/SOUL.md` |
| CTO | `~/.openclaw/workspace-cto/` | `agents/cto/SOUL.md` |
| ... | ... | ... |

---

## 📊 已生成的文档

### CTO 技术文档
- **位置**: `~/.openclaw/workspace-cto/docs/ai-customer-service-architecture.md`
- **内容**: 1500+ 行完整技术架构方案
- **包含**: 技术栈选型、微服务设计、数据库 ER 图、API 规范、安全设计、K8s 部署配置

### QA 测试文档
- **位置**: `~/.openclaw/workspace-qa/qa-test-plan-ai-customer-service.md`
- **内容**: 360+ 行质量检测计划
- **包含**: 150+ 测试用例、性能指标、AI 模型评估标准、验收流程

---

## 🔧 故障排查

### Gateway 无法访问
```bash
# 检查状态
openclaw gateway status

# 重启 Gateway
openclaw gateway restart
```

### Agent 无响应
```bash
# 检查 Agent 配置
cat ~/.openclaw/openclaw.json | python3 -c "import json,sys; print(json.load(sys.stdin)['agents']['list'])"

# 检查 workspace 是否存在
ls -la ~/.openclaw/workspace-ceo/
```

### 重新安装
```bash
cd ~/code/corporation
./install.sh
```

---

## 🎯 下一步建议

1. **体验单 Agent 能力** - 分别测试不同部门的职责
2. **测试多 Agent 协作** - 下达复杂任务，观察 CEO 如何协调各部门
3. **查看生成文档** - 阅读 CTO 和 QA 输出的专业文档
4. **配置消息渠道** - 对接飞书/微信，实现消息通知
5. **自定义 Agent** - 修改 SOUL.md 文件，调整角色行为

---

## 📞 技术支持

- 项目地址：https://github.com/earyant/corporation
- OpenClaw 文档：https://docs.openclaw.ai
- 问题反馈：提交 Issue

---

**🏢 公司智能体已就绪，随时可以执行任务！**
