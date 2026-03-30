---
name: ai-coach-init
version: 3.1.0
description: "AI Coach 环境自检与初始化：三层检查（全局/角色/日常），静默修复，确保工具链就绪"
---

# AI Coach Init — 环境自检与初始化

## 触发时机

| 场景 | 执行内容 |
|------|---------|
| 首次使用 ai-coach（Memory 中无角色记忆） | Layer 1 全局检查 + Layer 2 角色专属检查 |
| 首次切换到新角色 | 仅 Layer 2 该角色的专属检查 |
| 日常使用（已有角色记忆） | Layer 3 静默快检 |

## Layer 1：全局检查

按顺序执行以下 6 项，记录每项结果（通过/缺失/建议）：

### 1. CLAUDE.md 存在
- 检查项目根目录是否有 CLAUDE.md
- **缺失时**：告诉用户"我需要了解一下你的项目，帮你生成一个项目说明文件"，引导使用 `/init` skill
- **存在时**：通过

### 2. CLAUDE.md 关键段落完整
- 存在时检查 4 关键段完整度：
  | 关键段 | 检查关键词 | 缺失提示 |
  |--------|-----------|---------|
  | 技术栈 | tech/技术栈/stack | 💡 建议补充项目技术栈，AI 能更准确推荐工具 |
  | 快速命令 | build/start/run/dev/构建/gradlew/npm | 💡 建议补充快速命令（构建/启动/测试），AI 能直接帮你运行 |
  | 架构约定 | 架构/architecture/目录/模块 | 💡 建议补充架构约定，AI 不会随意创建文件 |
  | 测试约定 | test/测试/TDD | 💡 建议补充测试约定，AI 写的测试更符合项目规范 |
- 每个缺失段只提示一行，不阻塞流程

### 3. Memory 目录
- `~/.claude/memory/` 或项目级 Memory 存在？→ 缺则静默创建
- 有角色记忆（`AI教练角色:` 格式）？→ 有则记录，跳过角色选择
- 有项目上下文记录（技术方案/测试策略/PRD 决策等）？→ 有则标记供后续引用

### 4. superpowers skill
- 检查 `~/.claude/skills/superpowers/` 是否存在
- **缺失时**：告诉用户"需要安装一个核心工具包，我来帮你装？"，等用户确认后执行安装
- **存在时**：通过

### 5. Hooks 配置（仅非首次用户）
- 仅当 Memory 中已有角色记忆时检查（首次用户跳过，避免信息过载）
- 检查 `.claude/settings.json` 是否配置了 hooks
- 无 hooks 时轻提：💡 进阶提示：配置 Hooks 可自动化代码检查，提升 AI 协作效率
- 有 hooks 则跳过，不输出

### 6. 推荐配置（建议项，不阻塞）
- 列出以下建议，标记为"有空时可设置"：
  - LSP 插件（代码实时检查，减少低级错误）
  - `CLAUDE_CODE_SUBAGENT_MODEL=sonnet`（子代理用更快的模型，省成本）
  - 常用命令权限白名单（避免每次运行测试都要点确认）

## Layer 2：角色专属检查

根据用户选择的角色，执行对应检查项：

### 产品角色
- `prd-development` skill 是否已安装（~/.claude/skills/prd-development/）
- `user-story` skill 是否已安装（~/.claude/skills/user-story/）
- `jobs-to-be-done` skill 是否已安装（推荐，非必须）
- 项目中是否有 `docs/` 目录（存放 PRD 和需求文档）

### 后端角色
- 项目构建命令是否可执行（如 `./gradlew build`、`mvn compile`、`npm run build`）
- 测试框架是否可运行（如 `./gradlew test`、`mvn test`、`npm test`）
- 数据库连接配置是否存在（检查配置文件中有无数据源配置）

### 测试角色
- Playwright 是否已安装（`npx playwright --version`）
- Playwright MCP 是否已配置（检查 MCP 配置文件）
- `webapp-testing` skill 是否已安装（~/.claude/skills/webapp-testing/）
- 项目中是否有 `tests/` 或 `test/` 目录

### 前端角色
- 前端构建工具是否可运行（如 `npm run build`、`pnpm build`、`yarn build`）
- Playwright 是否已安装（自测用）
- 测试框架是否可运行（如 `npm test`、`vitest`、`jest`）

### 一人全栈角色
- 执行后端角色全部检查项
- 执行前端角色全部检查项

### 通用：历史产出检查
检查 Memory 中是否有当前角色的历史产出记录（技术方案/测试策略/PRD 决策等），有则标记供后续引导主动引用。

## Layer 3：日常快检

完全静默执行，不输出任何内容，除非发现问题：
- CLAUDE.md 是否存在
- Memory 中角色记忆是否完整

**有问题时**：输出一行提醒，如"检测到项目说明文件被删除，建议重新生成"。
**无问题时**：不输出任何内容，直接进入正常流程。

## 输出格式

### 全部通过
```
环境检查完成，一切就绪。
```

### 有缺失项
```
环境检查完成。有 N 项需要配置：
1. {缺失描述} → {修复建议}？(Y/n)
2. {缺失描述} → {修复建议}？(Y/n)
其余 M 项检查均正常。
```

### 日常快检（无问题）
不输出任何内容。

## 自动修复能力

| 操作 | 是否需要用户确认 |
|------|----------------|
| 创建 Memory 目录 | 否（静默执行） |
| 创建 docs/ 目录 | 是（询问后执行） |
| 安装 skill（核心工具包、PRD 写作工具等） | 是（询问后执行） |
| 安装工具（自动化测试框架等） | 是（询问后执行） |
| 修改配置文件 | 是（询问后执行） |

## 语言风格

所有提示信息使用非技术语言，确保产品经理也能看懂：
- 说"项目说明文件"而不是"CLAUDE.md 配置"
- 说"核心工具包"而不是"superpowers skill 依赖"
- 说"PRD 写作工具"而不是"prd-development skill"
- 说"自动化测试框架"而不是"Playwright binary"
- 说"代码实时检查"而不是"LSP integration"
