# 🧪 单元测试 · Unit Testing

> 版本：v1.0 | 最后更新：2026-03-28 | 维护者：QA

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2026-03-28 | 初始版本 |

---

## 技能描述

本技能用于编写和执行单元测试，确保代码质量和功能正确性。

**使用者**: QA、Engineering

**适用场景**:
- 新功能测试编写
- 回归测试
- TDD 测试驱动开发
- 代码覆盖率提升

**依赖技能**:
- `coding` - 代码开发（被测代码）
- `quality_check` - 质量检查

---

## 使用方法

### 命令格式

```markdown
🧪 单元测试

**测试对象**: {模块/函数}
**测试框架**: {pytest/unittest/jest}
**覆盖率目标**: {百分比}
```

### 输出格式

```markdown
📋 测试报告

**测试对象**: {对象}
**测试日期**: {日期}
**测试者**: {测试者}

## 测试结果
| 类型 | 总数 | 通过 | 失败 | 跳过 | 通过率 |
|------|------|------|------|------|--------|
| 单元测试 | {数量} | {数量} | {数量} | {数量} | {比例} |

## 覆盖率
| 指标 | 覆盖率 | 目标 | 状态 |
|------|--------|------|------|
| 语句覆盖 | {比例} | {目标} | 🟢/🔴 |
| 分支覆盖 | {比例} | {目标} | 🟢/🔴 |
| 函数覆盖 | {比例} | {目标} | 🟢/🔴 |

## 失败用例
| 用例名 | 失败原因 | 严重程度 |
|--------|----------|----------|
| {用例} | {原因} | 高/中/低 |

## 测试用例清单
- [x] {用例 1}
- [x] {用例 2}
- [ ] {用例 3}
```

---

## 使用示例

### 示例 1：新用户注册测试

**输入**:
```markdown
🧪 单元测试

**测试对象**: 用户注册模块
**测试框架**: pytest
**覆盖率目标**: 90%
```

**输出**:
```markdown
📋 测试报告

**测试对象**: user_registration.py
**测试日期**: 2026-03-28
**测试者**: QA

## 测试结果
| 类型 | 总数 | 通过 | 失败 | 跳过 | 通过率 |
|------|------|------|------|------|--------|
| 单元测试 | 25 | 25 | 0 | 0 | 100% |

## 覆盖率
| 指标 | 覆盖率 | 目标 | 状态 |
|------|--------|------|------|
| 语句覆盖 | 95% | 90% | 🟢 |
| 分支覆盖 | 92% | 90% | 🟢 |
| 函数覆盖 | 100% | 90% | 🟢 |

## 测试用例详情

### 正常场景
- [x] test_register_success: 正常注册流程
- [x] test_register_with_special_chars: 特殊字符用户名
- [x] test_register_duplicate_email: 重复邮箱检测

### 边界条件
- [x] test_username_min_length: 用户名最小长度
- [x] test_username_max_length: 用户名最大长度
- [x] test_password_min_length: 密码最小长度

### 异常情况
- [x] test_register_empty_username: 空用户名
- [x] test_register_empty_password: 空密码
- [x] test_register_invalid_email: 无效邮箱格式
- [x] test_register_sql_injection: SQL 注入防御
- [x] test_register_xss_attack: XSS 攻击防御

## 测试代码示例
```python
def test_register_success():
    """测试正常注册流程"""
    result = register_user("testuser", "password123", "test@example.com")
    assert result.success is True
    assert result.user_id is not None
    assert result.token is not None

def test_register_sql_injection():
    """测试 SQL 注入防御"""
    malicious_input = "admin' OR '1'='1"
    result = register_user(malicious_input, "password123", "test@example.com")
    assert result.success is False
    assert "无效输入" in result.error
```

## 整体评价
✅ 测试通过，覆盖率达标

**需要同步的部门**:
@CTO @Engineering
```

### 示例 2：测试失败

**输入**:
```markdown
🧪 单元测试

**测试对象**: 订单计算模块
**测试框架**: pytest
```

**输出**:
```markdown
📋 测试报告

**测试对象**: order_calculation.py
**测试日期**: 2026-03-28
**测试者**: QA

## 测试结果
| 类型 | 总数 | 通过 | 失败 | 跳过 | 通过率 |
|------|------|------|------|------|--------|
| 单元测试 | 18 | 15 | 3 | 0 | 83% |

## 失败用例
| 用例名 | 失败原因 | 严重程度 |
|--------|----------|----------|
| test_discount_calculation | 断言失败：预期 100，实际 90 | 高 |
| test_tax_with_free_shipping | AssertionError: 运费计算错误 | 中 |
| test_bulk_discount | TypeError: NoneType 错误 | 中 |

## 失败详情

### test_discount_calculation
```python
# 失败信息
E AssertionError: 预期 100，实际 90
E 位置：tests/test_order.py:45

# 问题分析
折扣计算未考虑满减活动，少计算了¥10 优惠
```

### test_tax_with_free_shipping
```python
# 失败信息
E AssertionError: 运费计算错误
E 预期：0，实际：10

# 问题分析
包邮条件判断逻辑有误，订单满¥99 应包邮
```

## 处理决定
❌ 测试未通过

## 行动项
1. Engineering 修复折扣计算逻辑
2. Engineering 修复包邮条件判断
3. 修复后重新运行测试

**需要同步的部门**:
@CTO @Engineering
```

---

## 检查清单

### 必查项

```markdown
- [ ] 正常场景测试覆盖
- [ ] 边界条件测试覆盖
- [ ] 异常情况测试覆盖
- [ ] 安全测试（SQL 注入、XSS 等）
- [ ] 测试独立，不依赖外部状态
- [ ] 测试用例命名清晰
```

### 选查项

```markdown
- [ ] 性能测试
- [ ] 并发测试
- [ ]  Mock 外部依赖
```

---

## 注意事项

1. 测试用例要独立，不互相依赖
2. 测试命名要清晰，说明测试目的
3. 一个测试只验证一个行为
4. 测试要有断言，不写无意义测试
5. 定期清理失败的测试

---

## 相关技能

| 技能 ID | 说明 | 协作方式 |
|---------|------|----------|
| `quality_check` | 质量检查 | 测试是 QC 一部分 |
| `integration_testing` | 集成测试 | 单元测试后执行 |
| `bug_tracking` | 缺陷追踪 | 失败用例转缺陷 |

---

## 看板集成

```bash
# 开始测试
python3 scripts/kanban_update.py progress JJC-xxx "正在编写单元测试用例，覆盖正常和异常场景" "用例设计🔄|编写测试|执行测试|覆盖率检查"

# 测试完成
python3 scripts/kanban_update.py flow JJC-xxx "QA" "CTO" "📋 单元测试报告：✅ 通过率 100%，覆盖率 95%"
```
