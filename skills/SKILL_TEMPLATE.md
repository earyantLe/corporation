# {Emoji} {技能名称} · {SkillName}

> 版本：v1.0 | 最后更新：{YYYY-MM-DD} | 维护者：{角色}

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | {YYYY-MM-DD} | 初始版本 |

---

## 技能描述

{技能简要描述}

**使用者**: {主要使用者}、{辅助使用者}

**适用场景**:
- {场景 1}
- {场景 2}
- {场景 3}

**依赖技能**:
- `{skill_id}` - {依赖说明}

---

## 使用方法

### 命令格式

```markdown
{命令格式}
```

### 输出格式

```markdown
{输出模板}
```

---

## 使用示例

### 示例 1：{正常场景}

**输入**:
```markdown
{输入}
```

**输出**:
```markdown
{输出}
```

### 示例 2：{异常场景}

**输入**:
```markdown
{异常输入}
```

**输出**:
```markdown
{异常处理输出}
```

### 示例 3：{进阶场景}

**输入**:
```markdown
{进阶输入}
```

**输出**:
```markdown
{进阶输出}
```

---

## 检查清单

### 必查项

```markdown
- [ ] {检查项 1}
- [ ] {检查项 2}
- [ ] {检查项 3}
```

### 选查项

```markdown
- [ ] {检查项 4}
- [ ] {检查项 5}
```

---

## 注意事项

1. {注意事项 1}
2. {注意事项 2}
3. {注意事项 3}
4. {注意事项 4}
5. {注意事项 5}

---

## 相关技能

| 技能 ID | 说明 | 协作方式 |
|---------|------|----------|
| `{skill_id}` | {技能说明} | {协作方式} |

---

## 看板集成（可选）

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
