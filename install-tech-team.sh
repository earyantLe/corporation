#!/bin/bash
# 🚀 技术团队 Agent · 安装脚本
# 用法：./install-tech-team.sh
#
# 功能：
# - 检查系统依赖
# - 注册技术团队 Agent
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

echo "🚀 技术团队 Agent · 安装程序"
echo "============================"
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

# 查找已配置的 API Key
MAIN_AUTH=""
if [[ -f "$HOME/.openclaw/agents/ceo/agent/models.json" ]]; then
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
    log_warning "未检测到 API Key 配置"
    echo ""
    echo "请先配置至少一个 Agent 的 API Key："
    echo "   openclaw agents add ceo"
    echo ""
    read -p "配置完成后按回车继续..."

    if [[ -f "$HOME/.openclaw/agents/ceo/agent/models.json" ]]; then
        MAIN_AUTH="$HOME/.openclaw/agents/ceo/agent/models.json"
    elif [[ -f "$HOME/.openclaw/agents/ceo/agent/auth-profiles.json" ]]; then
        MAIN_AUTH="$HOME/.openclaw/agents/ceo/agent/auth-profiles.json"
    else
        MAIN_AUTH=$(find "$HOME/.openclaw/agents" -name "models.json" 2>/dev/null | head -1)
        if [[ -z "$MAIN_AUTH" ]]; then
            log_error "仍未检测到 API Key，退出安装"
            exit 1
        fi
    fi
fi
log_success "API Key 已配置：$MAIN_AUTH"
echo ""

# 创建 Agent 工作空间
echo "🚀 创建技术团队 Agent..."
AGENTS=("product-manager" "backend-dev" "algorithm-dev" "frontend-dev" "qa-tester")
AGENT_LABELS=("产品经理" "后端研发" "算法研发" "前端研发" "测试工程师")
AGENT_SOULS=("agents-tech/product-manager/SOUL.md" "agents-tech/backend-dev/SOUL.md" "agents-tech/algorithm-dev/SOUL.md" "agents-tech/frontend-dev/SOUL.md" "agents-tech/qa-tester/SOUL.md")

for i in "${!AGENTS[@]}"; do
    AGENT_ID="${AGENTS[$i]}"
    AGENT_LABEL="${AGENT_LABELS[$i]}"
    AGENT_SOUL="${AGENT_SOULS[$i]}"
    
    log_info "注册 $AGENT_LABEL ($AGENT_ID)..."
    
    # 检查 SOUL.md 是否存在
    if [[ ! -f "$AGENT_SOUL" ]]; then
        log_error "SOUL.md 不存在：$AGENT_SOUL"
        exit 1
    fi
    
    # 创建 Agent 目录
    AGENT_DIR="$HOME/.openclaw/agents/$AGENT_ID"
    mkdir -p "$AGENT_DIR/agent"
    
    # 复制 SOUL.md
    cp "$AGENT_SOUL" "$AGENT_DIR/SOUL.md"
    
    # 创建 openclaw.json（如果不存在）
    if [[ ! -f "$AGENT_DIR/openclaw.json" ]]; then
        cat > "$AGENT_DIR/openclaw.json" <<EOF
{
  "label": "$AGENT_LABEL",
  "model": "default"
}
EOF
    fi
    
    log_success "✅ $AGENT_LABEL 已注册"
done

echo ""

# 验证安装
echo "🔍 验证安装结果..."
echo ""

INSTALLED_COUNT=0
for AGENT_ID in "${AGENTS[@]}"; do
    AGENT_DIR="$HOME/.openclaw/agents/$AGENT_ID"
    if [[ -d "$AGENT_DIR" ]] && [[ -f "$AGENT_DIR/SOUL.md" ]]; then
        log_success "$AGENT_ID: 已安装"
        ((INSTALLED_COUNT++))
    else
        log_error "$AGENT_ID: 安装失败"
    fi
done

echo ""
echo "============================"
log_success "技术团队 Agent 安装完成！"
echo ""
echo "已安装 $INSTALLED_COUNT/5 个 Agent："
for i in "${!AGENTS[@]}"; do
    echo "  - ${AGENT_LABELS[$i]} (${AGENTS[$i]})"
done
echo ""
echo "使用示例："
echo "  openclaw agent --agent product-manager --message \"设计一个用户签到功能\""
echo "  openclaw agent --agent backend-dev --message \"实现登录 API\""
echo "  openclaw agent --agent frontend-dev --message \"开发个人中心页面\""
echo "  openclaw agent --agent qa-tester --message \"设计登录功能测试用例\""
echo ""
