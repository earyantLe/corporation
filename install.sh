#!/bin/bash
# 🏢 公司智能体 · 安装脚本
# 用法：./install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🏢 公司智能体 · 安装程序"
echo "========================"
echo ""

# 检查 OpenClaw 是否安装
if ! command -v openclaw &> /dev/null; then
    echo "❌ 未检测到 OpenClaw，请先安装："
    echo "   brew install openclaw"
    echo "   或访问：https://openclaw.ai"
    exit 1
fi

echo "✅ OpenClaw 已安装：$(openclaw --version)"
echo ""

# 检查是否已配置 API Key
echo "📋 检查 API Key 配置..."
MAIN_AUTH=$(find ~/.openclaw/agents -name auth-profiles.json 2>/dev/null | head -1)
if [[ -z "$MAIN_AUTH" ]]; then
    echo "⚠️  未检测到 API Key 配置"
    echo ""
    echo "请先配置至少一个 Agent 的 API Key："
    echo "   openclaw agents add ceo"
    echo ""
    read -p "配置完成后按回车继续..."
    MAIN_AUTH=$(find ~/.openclaw/agents -name auth-profiles.json 2>/dev/null | head -1)
    if [[ -z "$MAIN_AUTH" ]]; then
        echo "❌ 仍未检测到 API Key，退出安装"
        exit 1
    fi
fi
echo "✅ API Key 已配置"
echo ""

# 创建 Agent 工作空间
echo "🏢 创建公司工作空间..."
AGENTS=("ceo" "coo" "cfo" "cto" "hr" "finance" "legal" "marketing" "sales" "engineering" "design" "qa")
AGENT_LABELS=("CEO" "COO" "CFO" "CTO" "HR" "财务总监" "法务总监" "市场总监" "销售总监" "工程总监" "设计总监" "QA 总监")

for i in "${!AGENTS[@]}"; do
    agent_id="${AGENTS[$i]}"
    agent_label="${AGENT_LABELS[$i]}"

    echo "   创建 ${agent_label} (${agent_id})..."

    # 检查是否已存在
    if [[ -d "$HOME/.openclaw/agents/$agent_id" ]]; then
        echo "   ⚠️  ${agent_label} 已存在，跳过创建"
        continue
    fi

    # 创建工作空间
    openclaw agents add "$agent_id" --non-interactive 2>/dev/null || {
        # 如果失败，手动创建目录结构
        mkdir -p "$HOME/.openclaw/agents/$agent_id/agent"
        mkdir -p "$HOME/.openclaw/agents/$agent_id/skills"
    }

    # 复制 SOUL.md
    if [[ -d "$HOME/.openclaw/agents/$agent_id" ]]; then
        cp "agents/$agent_id/SOUL.md" "$HOME/.openclaw/agents/$agent_id/" 2>/dev/null || true
    fi

    # 同步 API Key
    if [[ -n "$MAIN_AUTH" ]] && [[ -d "$HOME/.openclaw/agents/$agent_id/agent" ]]; then
        cp "$MAIN_AUTH" "$HOME/.openclaw/agents/$agent_id/agent/auth-profiles.json" 2>/dev/null || true
    fi
done

echo "✅ 公司工作空间创建完成"
echo ""

# 注册 Agent 到 openclaw.json
echo "📜 注册公司到 openclaw.json..."

OCLAW_CONFIG="$HOME/.openclaw/openclaw.json"

if [[ ! -f "$OCLAW_CONFIG" ]]; then
    echo "   创建 openclaw.json..."
    cat > "$OCLAW_CONFIG" << 'EOF'
{
  "agents": [],
  "permissions": {},
  "skills": {}
}
EOF
fi

# 使用 Python 脚本注册 Agent
python3 - << 'PYTHON_SCRIPT'
import json
import os
from pathlib import Path

config_path = Path.home() / '.openclaw' / 'openclaw.json'

# 读取配置
if config_path.exists():
    with open(config_path) as f:
        config = json.load(f)
else:
    config = {"agents": [], "permissions": {}, "skills": {}}

# 公司角色定义
company_roles = [
    {"id": "ceo", "label": "CEO", "description": "任务接收与分配/战略决策/成果审批"},
    {"id": "coo", "label": "COO", "description": "运营管理/人力资源/进度跟踪/跨部门协调"},
    {"id": "cfo", "label": "CFO", "description": "财务管理/预算规划/财务分析/法务支持"},
    {"id": "cto", "label": "CTO", "description": "技术决策/技术管理/产品规划/技术支持"},
    {"id": "hr", "label": "HR", "description": "招聘管理/绩效管理/培训发展/员工关系"},
    {"id": "finance", "label": "财务总监", "description": "会计核算/资金管理/税务管理/成本管理"},
    {"id": "legal", "label": "法务总监", "description": "合同管理/合规管理/风险控制/知识产权"},
    {"id": "marketing", "label": "市场总监", "description": "市场调研/品牌管理/营销策划/数字营销"},
    {"id": "sales", "label": "销售总监", "description": "销售管理/客户开发/商务谈判/客户服务"},
    {"id": "engineering", "label": "工程总监", "description": "软件开发/技术攻坚/代码质量/团队协作"},
    {"id": "design", "label": "设计总监", "description": "UI 设计/UX 设计/品牌设计/设计评审"},
    {"id": "qa", "label": "QA 总监", "description": "质量检查/测试管理/流程优化/风险评估"},
]

# 权限矩阵（所有部门可以互相协作）
all_agents = ["ceo", "coo", "cfo", "cto", "hr", "finance", "legal", "marketing", "sales", "engineering", "design", "qa"]
permissions = {}
for role in company_roles:
    # 每个角色可以协作除了自己之外的所有其他角色
    permissions[role["id"]] = [a for a in all_agents if a != role["id"]]

# 添加 Agent
existing_ids = {a.get("id") for a in config.get("agents", [])}
for role in company_roles:
    if role["id"] not in existing_ids:
        config.setdefault("agents", []).append({
            "id": role["id"],
            "label": role["label"],
            "description": role["description"],
            "allowAgents": permissions.get(role["id"], []),
        })
        print(f"   注册 {role['label']} ({role['id']})")

# 保存配置
with open(config_path, "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✅ 公司注册完成")
PYTHON_SCRIPT

echo ""

# 安装 Skills
echo "🏢 安装公司技能..."

SKILLS_DIR="$SCRIPT_DIR/skills"
if [[ -d "$SKILLS_DIR" ]]; then
    for skill_dir in "$SKILLS_DIR"/*/; do
        skill_name=$(basename "$skill_dir")
        echo "   安装技能：$skill_name"

        # 复制技能到各 Agent 的 skills 目录
        for agent_id in "${AGENTS[@]}"; do
            agent_skills="$HOME/.openclaw/agents/$agent_id/skills"
            if [[ -d "$agent_skills" ]]; then
                cp -r "$skill_dir" "$agent_skills/" 2>/dev/null || true
            fi
        done
    done
    echo "✅ 技能安装完成"
else
    echo "⚠️  技能目录不存在，跳过技能安装"
fi

echo ""

# 创建数据目录
echo "📁 初始化数据目录..."
mkdir -p "$SCRIPT_DIR/data"
mkdir -p "$SCRIPT_DIR/logs"
echo "✅ 数据目录初始化完成"
echo ""

# 输出使用说明
echo "========================"
echo "🎉 公司智能体安装完成!"
echo ""
echo "📋 下一步:"
echo ""
echo "1. 启动 OpenClaw Gateway:"
echo "   openclaw gateway start"
echo ""
echo "2. 配置消息渠道 (可选):"
echo "   openclaw channels add --type feishu --agent ceo"
echo ""
echo "3. 下达任务:"
echo "   给 CEO Agent 发送消息即可"
echo ""
echo "🏢 公司智能体已就绪，随时可以执行任务!"
echo ""
