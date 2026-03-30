#!/bin/bash
# ai-coach v3 安装脚本（幂等）
set -e

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.claude/skills"

echo "正在安装 AI 编程教练 v3..."

# 确保目标目录存在
mkdir -p "$TARGET"

# 检查主目录：如果 ai-coach 是软链接则重建，如果是真实目录则保留
if [ -L "$TARGET/ai-coach" ]; then
  rm -f "$TARGET/ai-coach"
  ln -s "$SKILL_DIR" "$TARGET/ai-coach"
elif [ ! -d "$TARGET/ai-coach" ]; then
  ln -s "$SKILL_DIR" "$TARGET/ai-coach"
fi
# 如果是真实目录（skills 仓库内的 ai-coach/），不需要软链接

# 创建子 skill 链接（跳过已存在的真实目录）
create_link() {
  local src="$1" dst="$2"
  if [ -L "$dst" ]; then
    rm -f "$dst"
    ln -s "$src" "$dst"
  elif [ -d "$dst" ]; then
    echo "  跳过 $(basename "$dst")（已是真实目录）"
  else
    ln -s "$src" "$dst"
  fi
}

create_link "$SKILL_DIR/init" "$TARGET/ai-coach-init"
create_link "$SKILL_DIR/fullstack" "$TARGET/ai-coach-fullstack"
create_link "$SKILL_DIR/product" "$TARGET/ai-coach-product"
create_link "$SKILL_DIR/backend" "$TARGET/ai-coach-backend"
create_link "$SKILL_DIR/testing" "$TARGET/ai-coach-testing"
create_link "$SKILL_DIR/frontend" "$TARGET/ai-coach-frontend"
create_link "$SKILL_DIR/enterprise" "$TARGET/ai-coach-enterprise"
create_link "$SKILL_DIR/evaluate" "$TARGET/ai-coach-evaluate"

echo "✓ 安装完成！重启 Claude Code 后输入 /ai-coach 或 '教练' 即可使用。"
