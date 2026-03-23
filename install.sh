#!/bin/bash
# 🏢 公司智能体 · 安装脚本
# 用法：./install.sh
#
# 功能：
# - 检查系统依赖
# - 配置 API Key
# - 注册公司 Agent
# - 初始化工作空间
# - 验证安装结果

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🏢 公司智能体 · 安装程序"
echo "========================"
echo ""

# 检查 OpenClaw 是否安装
log_info "检查 OpenClaw 安装..."
if ! command -v openclaw &> /dev/null; then
    log_error "未检测到 OpenClaw"
    echo ""
    echo "请先安装 OpenClaw："
    echo "   npm install -g openclaw"
    echo "   或访问：https://openclaw.ai"
    echo ""
    exit 1
fi

OPENCLAW_VERSION=$(openclaw --version 2>&1 || echo "未知版本")
log_success "OpenClaw 已安装：$OPENCLAW_VERSION"
echo ""

# 检查是否已配置 API Key
echo "📋 检查 API Key 配置..."

# 查找已配置的 API Key（支持 models.json 和 auth-profiles.json 两种格式）
MAIN_AUTH=""
if [[ -f "$HOME/.openclaw/agents/taizi/agent/models.json" ]]; then
    MAIN_AUTH="$HOME/.openclaw/agents/taizi/agent/models.json"
elif [[ -f "$HOME/.openclaw/agents/ceo/agent/models.json" ]]; then
    MAIN_AUTH="$HOME/.openclaw/agents/ceo/agent/models.json"
elif [[ -f "$HOME/.openclaw/agents/ceo/agent/auth-profiles.json" ]]; then
    MAIN_AUTH="$HOME/.openclaw/agents/ceo/agent/auth-profiles.json"
else
    # 查找任意 agent 的配置文件
    MAIN_AUTH=$(find "$HOME/.openclaw/agents" -name "models.json" 2>/dev/null | head -1)
    if [[ -z "$MAIN_AUTH" ]]; then
        MAIN_AUTH=$(find "$HOME/.openclaw/agents" -name "auth-profiles.json" 2>/dev/null | head -1)
    fi
fi

if [[ -z "$MAIN_AUTH" ]]; then
    echo "⚠️  未检测到 API Key 配置"
    echo ""
    echo "请先配置至少一个 Agent 的 API Key："
    echo "   openclaw agents add ceo"
    echo ""
    read -p "配置完成后按回车继续..."

    # 重新查找
    if [[ -f "$HOME/.openclaw/agents/taizi/agent/models.json" ]]; then
        MAIN_AUTH="$HOME/.openclaw/agents/taizi/agent/models.json"
    elif [[ -f "$HOME/.openclaw/agents/ceo/agent/models.json" ]]; then
        MAIN_AUTH="$HOME/.openclaw/agents/ceo/agent/models.json"
    elif [[ -f "$HOME/.openclaw/agents/ceo/agent/auth-profiles.json" ]]; then
        MAIN_AUTH="$HOME/.openclaw/agents/ceo/agent/auth-profiles.json"
    else
        MAIN_AUTH=$(find "$HOME/.openclaw/agents" -name "models.json" 2>/dev/null | head -1)
        if [[ -z "$MAIN_AUTH" ]]; then
            MAIN_AUTH=$(find "$HOME/.openclaw/agents" -name "auth-profiles.json" 2>/dev/null | head -1)
        fi
    fi

    if [[ -z "$MAIN_AUTH" ]]; then
        echo "❌ 仍未检测到 API Key，退出安装"
        exit 1
    fi
fi
echo "✅ API Key 已配置：$MAIN_AUTH"
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
        # 即使已存在，也要确保 SOUL.md 和 API Key 已同步
        if [[ -f "agents/$agent_id/SOUL.md" ]] && [[ -d "$HOME/.openclaw/agents/$agent_id" ]]; then
            cp "agents/$agent_id/SOUL.md" "$HOME/.openclaw/agents/$agent_id/" 2>/dev/null || true
        fi
        if [[ -n "$MAIN_AUTH" ]] && [[ -d "$HOME/.openclaw/agents/$agent_id/agent" ]]; then
            cp "$MAIN_AUTH" "$HOME/.openclaw/agents/$agent_id/agent/auth-profiles.json" 2>/dev/null || true
        fi
        continue
    fi

    # 创建工作空间（带错误处理）
    if ! openclaw agents add "$agent_id" --non-interactive 2>/dev/null; then
        echo "   ⚠️  openclaw agents add 失败，尝试手动创建目录..."
        mkdir -p "$HOME/.openclaw/agents/$agent_id/agent"
        mkdir -p "$HOME/.openclaw/agents/$agent_id/skills"
    fi

    # 复制 SOUL.md
    if [[ -f "agents/$agent_id/SOUL.md" ]]; then
        if [[ -d "$HOME/.openclaw/agents/$agent_id" ]]; then
            cp "agents/$agent_id/SOUL.md" "$HOME/.openclaw/agents/$agent_id/" && \
                echo "   ✅ SOUL.md 已复制" || \
                echo "   ⚠️  SOUL.md 复制失败"
        fi
    else
        echo "   ⚠️  未找到 SOUL.md 文件：agents/$agent_id/SOUL.md"
    fi

    # 同步 API Key（复制 models.json 或 auth-profiles.json）
    if [[ -n "$MAIN_AUTH" ]]; then
        AUTH_FILE_NAME=$(basename "$MAIN_AUTH")
        if [[ -d "$HOME/.openclaw/agents/$agent_id/agent" ]]; then
            cp "$MAIN_AUTH" "$HOME/.openclaw/agents/$agent_id/agent/$AUTH_FILE_NAME" && \
                echo "   ✅ API 配置已同步 ($AUTH_FILE_NAME)" || \
                echo "   ⚠️  API 配置同步失败"
        else
            echo "   ⚠️  agent 目录不存在，跳过 API 配置同步"
        fi
    fi
done

echo "✅ 公司工作空间创建完成"
echo ""

# 配置 workspace 的 IDENTITY.md
echo "📝 配置 Agent 身份文件..."

configure_workspace_identity() {
    local agent_id="$1"
    local workspace_dir="$HOME/.openclaw/workspace-$agent_id"
    local soul_file="$SCRIPT_DIR/agents/$agent_id/SOUL.md"

    if [[ ! -d "$workspace_dir" ]]; then
        return
    fi

    if [[ -f "$soul_file" ]]; then
        # 复制 SOUL.md 到 workspace
        cp "$soul_file" "$workspace_dir/SOUL.md" 2>/dev/null

        # 从 SOUL.md 提取角色名称和描述 (使用 python 提取)
        local role_info=$(python3 -c "
import re
with open('$soul_file', 'r', encoding='utf-8') as f:
    content = f.read()
# 提取标题，如 '# 👔 CEO · 首席执行官' -> 'CEO (首席执行官)'
match = re.search(r'^#\s*.*?\s+(CEO|COO|CFO|CTO|HR|CFO|总监).*?·\s*(.+?)\s*$', content, re.MULTILINE)
if match:
    print(f'{match.group(1)} ({match.group(2)})')
else:
    # 尝试简单提取
    match = re.search(r'^#\s*(.+?)\s*·', content)
    if match:
        print(match.group(1).strip())
    else:
        print('$agent_id')
" 2>/dev/null)

        local description=$(python3 -c "
import re
with open('$soul_file', 'r', encoding='utf-8') as f:
    content = f.read()
match = re.search(r'你擅长\*\*(.+?)\*\*', content)
if match:
    print(match.group(1))
else:
    print('负责公司相关工作')
" 2>/dev/null)

        # 生成简化的 IDENTITY.md
        cat > "$workspace_dir/IDENTITY.md" << EOF
# $role_info

## 角色定位
你是**$role_info**，$description。

## 核心职责
- 查看 SOUL.md 获取完整职责定义
- 按照工作流执行任务
- 与相关部门协作完成工作

## 工作空间
- SOUL.md: 完整角色定义和工作流
- AGENTS.md: 可调用的子 Agent 列表
- TOOLS.md: 可用工具列表
EOF
        echo "   ✅ $agent_id IDENTITY.md 已配置"
    fi
}

for agent_id in "${AGENTS[@]}"; do
    configure_workspace_identity "$agent_id"
done

echo "✅ Agent 身份文件配置完成"
echo ""

# 配置 AGENTS.md (子 Agent 列表)
echo "🤖 配置 Agent 协作关系..."

configure_agents_file() {
    local agent_id="$1"
    local workspace_dir="$HOME/.openclaw/workspace-$agent_id"

    if [[ ! -d "$workspace_dir" ]]; then
        return
    fi

    # 从 openclaw.json 读取该 Agent 的 allowAgents 列表
    local allow_agents=$(python3 -c "
import json
from pathlib import Path
config_path = Path.home() / '.openclaw' / 'openclaw.json'
if config_path.exists():
    config = json.load(open(config_path))
    agents_list = config.get('agents', {}).get('list', [])
    for agent in agents_list:
        if agent.get('id') == '$agent_id':
            allow = agent.get('subagents', {}).get('allowAgents', [])
            print(' '.join(allow))
            break
" 2>/dev/null)

    if [[ -n "$allow_agents" ]]; then
        cat > "$workspace_dir/AGENTS.md" << EOF
# 可协作的部门

本部门可以调用以下部门协助工作：

| 部门 ID | 说明 |
|---------|------|
EOF
        for sub_id in $allow_agents; do
            local sub_label=$(grep -l "id.*$sub_id" "$SCRIPT_DIR/agents/"*/SOUL.md 2>/dev/null | head -1 | xargs -I{} basename {} | sed 's/SOUL.md//')
            echo "| $sub_id | $sub_label |" >> "$workspace_dir/AGENTS.md"
        done

        echo "   ✅ $agent_id AGENTS.md 已配置 (${allow_agents})"
    fi
}

for agent_id in "${AGENTS[@]}"; do
    configure_agents_file "$agent_id"
done

echo "✅ Agent 协作关系配置完成"
echo ""

# 注册 Agent 到 OpenClaw
echo "📜 注册 Agent 到 OpenClaw..."

OCLAW_CONFIG="$HOME/.openclaw/openclaw.json"

# 使用 openclaw agents add 命令注册每个 Agent
for agent_id in "${AGENTS[@]}"; do
    agent_label=$(python3 -c "
import json
from pathlib import Path
config_path = Path('$SCRIPT_DIR/agents/$agent_id/SOUL.md')
if config_path.exists():
    content = config_path.read_text(encoding='utf-8')
    import re
    match = re.search(r'^#\s*.*?(\S+)\s+·\s*(.+?)\s*$', content, re.MULTILINE)
    if match:
        print(f'{match.group(1)} ({match.group(2)})')
    else:
        print('$agent_id')
else:
    print('$agent_id')
" 2>/dev/null || echo "$agent_id")

    # 检查工作空间是否存在
    workspace_dir="$HOME/.openclaw/workspace-$agent_id"
    if [[ ! -d "$workspace_dir" ]]; then
        echo "   ⚠️  $agent_id 工作空间不存在，跳过注册"
        continue
    fi

    # 检查是否已在配置中存在
    if python3 -c "
import json
from pathlib import Path
config_path = Path.home() / '.openclaw' / 'openclaw.json'
if config_path.exists():
    config = json.load(open(config_path))
    agents_list = config.get('agents', {}).get('list', [])
    for agent in agents_list:
        if isinstance(agent, dict) and agent.get('id') == '$agent_id':
            exit(0)
exit(1)
" 2>/dev/null; then
        echo "   ✅ $agent_id 已注册，跳过"
        continue
    fi

    # 使用 openclaw agents add 命令注册
    echo "   注册 $agent_label (${agent_id})..."
    if openclaw agents add "$agent_id" --non-interactive 2>/dev/null; then
        echo "   ✅ $agent_id 注册成功"
    else
        echo "   ⚠️  openclaw agents add 失败，将尝试手动配置"
    fi
done

# 配置 openclaw.json 的子 Agent 权限（所有部门可以互相协作）
echo "🔐 配置 Agent 协作权限..."

python3 << 'PYTHON_SCRIPT'
import json
from pathlib import Path

config_path = Path.home() / '.openclaw' / 'openclaw.json'

if not config_path.exists():
    print("   ⚠️  openclaw.json 不存在，跳过权限配置")
    exit(0)

with open(config_path) as f:
    config = json.load(f)

# 确保 agents 是 dict 格式
if "agents" not in config or not isinstance(config["agents"], dict):
    config["agents"] = {"list": []}

if "list" not in config["agents"]:
    config["agents"]["list"] = []

agents_list = config["agents"]["list"]

# 所有部门可以互相协作
all_agents = ["ceo", "coo", "cfo", "cto", "hr", "finance", "legal", "marketing", "sales", "engineering", "design", "qa"]

# 为每个已注册的 Agent 配置 allowAgents
for agent in agents_list:
    if isinstance(agent, dict) and agent.get("id") in all_agents:
        agent_id = agent["id"]
        # 计算可协作的部门（排除自己）
        allow_agents = [a for a in all_agents if a != agent_id]
        if "subagents" not in agent:
            agent["subagents"] = {}
        agent["subagents"]["allowAgents"] = allow_agents
        print(f"   ✅ {agent_id} 协作权限已配置")

# 保存配置
with open(config_path, "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✅ 协作权限配置完成")
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
