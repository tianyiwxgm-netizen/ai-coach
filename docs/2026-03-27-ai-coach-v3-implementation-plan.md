# AI Coach v3 角色化升级实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 ai-coach 从通用教练升级为角色化教练系统，支持 5 种角色（一人全栈、产品、后端、测试、前端）

**Architecture:** 单入口 SKILL.md + 7 个子 skill（通过 Skill 工具加载）。每个角色独立完整，按需加载。评估系统按角色定制维度。首次使用时三层静默自检。

**Tech Stack:** Claude Code Skill（Markdown），Python（analyze_sessions.py），Bash（install.sh）

**Spec:** `ai-coach/docs/2026-03-27-ai-coach-v3-role-based-upgrade-design.md`

**代码目录:** `~/.claude/skills/ai-coach/`（skills 仓库，本身是 git 仓库）

---

## 文件结构

### 新建文件

| 文件 | 职责 |
|------|------|
| `SKILL.md` | 入口：角色选择/记忆 + 路由 + 全局规则（覆写现有） |
| `init/SKILL.md` | 子 skill：首次自检初始化 |
| `fullstack/SKILL.md` | 子 skill：一人全栈角色（现有内容升级版） |
| `product/SKILL.md` | 子 skill：产品角色 |
| `backend/SKILL.md` | 子 skill：后端角色 |
| `testing/SKILL.md` | 子 skill：测试角色 |
| `frontend/SKILL.md` | 子 skill：前端角色 |
| `install.sh` | 安装脚本（幂等，清理旧版本 + 创建软链接） |

### 修改文件

| 文件 | 变更 |
|------|------|
| `enterprise/SKILL.md` | 精简：移除产品/技术知识库（已移入角色子 skill），保留跨角色大型项目知识库 |
| `evaluate/SKILL.md` | 重写：增加角色路由 + 5 套评估维度 |
| `evaluate/analyze_sessions.py` | 升级：新增角色信号字段 |
| `安装使用.md` | 重写：新的安装方式 + 10 个场景示范 |
| `tests/TEST-PLAN.md` | 重写：新的测试计划覆盖角色化场景 |
| `tests/case-*.md` | 更新现有 + 新增角色测试用例 |

---

## Chunk 1: 基础设施（入口 + 自检 + 安装）

### Task 1: 编写 install.sh 安装脚本

**Files:**
- Create: `ai-coach/install.sh`

- [ ] **Step 1: 编写安装脚本**

```bash
#!/bin/bash
# ai-coach v3 安装脚本（幂等）
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.claude/skills"

echo "正在安装 AI 编程教练 v3..."

# 清理旧版本（v2 的 3 个软链接 + v3 的全部）
for name in ai-coach ai-coach-init ai-coach-fullstack ai-coach-product \
            ai-coach-backend ai-coach-testing ai-coach-frontend \
            ai-coach-enterprise ai-coach-evaluate; do
  rm -f "$TARGET/$name"
done

# 创建新的软链接
ln -s "$SKILL_DIR" "$TARGET/ai-coach"
ln -s "$SKILL_DIR/init" "$TARGET/ai-coach-init"
ln -s "$SKILL_DIR/fullstack" "$TARGET/ai-coach-fullstack"
ln -s "$SKILL_DIR/product" "$TARGET/ai-coach-product"
ln -s "$SKILL_DIR/backend" "$TARGET/ai-coach-backend"
ln -s "$SKILL_DIR/testing" "$TARGET/ai-coach-testing"
ln -s "$SKILL_DIR/frontend" "$TARGET/ai-coach-frontend"
ln -s "$SKILL_DIR/enterprise" "$TARGET/ai-coach-enterprise"
ln -s "$SKILL_DIR/evaluate" "$TARGET/ai-coach-evaluate"

echo "✓ 安装完成！重启 Claude Code 后输入 /ai-coach 或 '教练' 即可使用。"
```

- [ ] **Step 2: 设置执行权限并验证**

Run: `chmod +x ~/.claude/skills/ai-coach/install.sh && bash ~/.claude/skills/ai-coach/install.sh`
Expected: 输出"✓ 安装完成！"，9 个软链接正确创建

- [ ] **Step 3: 验证幂等性**

Run: `bash ~/.claude/skills/ai-coach/install.sh && ls -la ~/.claude/skills/ | grep ai-coach`
Expected: 重复执行无报错，软链接指向正确

- [ ] **Step 4: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/install.sh && git commit -m "feat: add install.sh for ai-coach v3"
```

### Task 2: 创建子 skill 目录结构

**Files:**
- Create: `ai-coach/init/SKILL.md`（占位）
- Create: `ai-coach/fullstack/SKILL.md`（占位）
- Create: `ai-coach/product/SKILL.md`（占位）
- Create: `ai-coach/backend/SKILL.md`（占位）
- Create: `ai-coach/testing/SKILL.md`（占位）
- Create: `ai-coach/frontend/SKILL.md`（占位）

- [ ] **Step 1: 创建所有子 skill 目录和占位 SKILL.md**

每个占位文件只写 frontmatter（name + 一行 description），后续 Task 逐个填充完整内容。description 必须精简（一行），避免 Claude Code 启动时上下文膨胀。

```markdown
---
name: ai-coach-init
description: AI 编程教练的环境自检初始化模块。由 ai-coach 主 skill 在首次使用时自动调用。
---
# 占位 — 待实现
```

对 6 个子 skill 各创建一个类似的占位文件。

- [ ] **Step 2: 运行 install.sh 验证软链接**

Run: `bash ~/.claude/skills/ai-coach/install.sh && ls ~/.claude/skills/ai-coach-*/SKILL.md`
Expected: 6 个新子 skill + 2 个已有子 skill 的 SKILL.md 都能找到

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/init ai-coach/fullstack ai-coach/product ai-coach/backend ai-coach/testing ai-coach/frontend && git commit -m "feat: create sub-skill directory structure for ai-coach v3"
```

### Task 3: 重写入口 SKILL.md

**Files:**
- Modify: `ai-coach/SKILL.md`（覆写）

- [ ] **Step 1: 备份现有 SKILL.md**

Run: `cp ~/.claude/skills/ai-coach/SKILL.md ~/.claude/skills/ai-coach/SKILL.md.v2.bak`

- [ ] **Step 2: 编写新的入口 SKILL.md**

内容参照 spec 第三节"入口流程"，包含：
- frontmatter（name: ai-coach, version: 3.0.0, description 精简一行）
- 启动时输出："AI 编程教练已就绪。"
- 全局规则 9 条（spec 第三节）
- 角色选择逻辑（检查 Memory → 有则确认/展示菜单 → 无则选择 → 存入 Memory）
- 快捷路由逻辑（带任务描述直接路由到角色子 skill）
- 路由表（角色名 → 子 skill 名映射）
- When to Activate 触发词列表

关键约束：控制在 ~80 行，不含任何角色具体流程内容。

- [ ] **Step 3: 验证语法正确**

用 Read 工具读取新 SKILL.md，检查 frontmatter 格式、Markdown 语法。

- [ ] **Step 4: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/SKILL.md && git commit -m "feat: rewrite ai-coach entry SKILL.md with role routing"
```

### Task 4: 编写 init/SKILL.md（首次自检）

**Files:**
- Modify: `ai-coach/init/SKILL.md`（覆写占位）

- [ ] **Step 1: 编写完整的 init/SKILL.md**

内容参照 spec 第四节"首次自检初始化"，包含：
- frontmatter（name: ai-coach-init, description 一行）
- 触发时机说明（三种场景）
- Layer 1 全局检查（5 项：CLAUDE.md/Memory/superpowers/推荐配置）
- Layer 2 角色专属检查（5 个角色各自的检查项）
- Layer 3 日常快检（静默执行逻辑）
- 输出格式（全通过/有缺失/静默）
- 自动修复逻辑（能自动解决的直接做，需确认的用 AskUserQuestion）
- 非技术语言提示模板

关键约束：~100 行。init 是唯一可执行环境配置的模块。

- [ ] **Step 2: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/init/SKILL.md && git commit -m "feat: implement init sub-skill for first-time setup check"
```

---

## Chunk 2: 核心角色（一人全栈 + 产品）

### Task 5: 编写 fullstack/SKILL.md（一人全栈角色）

**Files:**
- Modify: `ai-coach/fullstack/SKILL.md`（覆写占位）

- [ ] **Step 1: 从现有 SKILL.md v2 备份中提取核心内容**

读取 `SKILL.md.v2.bak`，提取以下内容作为 fullstack 的基础：
- 教练内功心法（五大原则、六个心智跃迁、复杂度阶梯）
- Step 0 经验检测
- Step 1 意图识别（快捷路由 + 主菜单）
- Step 2 任务诊断（复杂度判断 + 领域专项触发）
- Step 3 通用引导（四维度收集 + 方法论推荐 + 示范提示词）
- Bug 修复铁律、安全修复三原则、重构铁律
- 零资料降级策略

- [ ] **Step 2: 应用升级改动**

在提取的基础上应用 spec 第五节的 5 个升级点：
1. Skill 精准映射表（替换旧的简单推荐）
2. 示范提示词模板增加【验收验证】段
3. 新增 Step 3.4 上下文管理提醒
4. 升级零资料降级（增加"5 分钟快速收集法"）
5. 移除 enterprise 混合内容引用（改为按需调用 ai-coach-enterprise 子 skill）

- [ ] **Step 3: 写入文件并验证**

写入 fullstack/SKILL.md，用 Read 检查行数（目标 ~250 行）和格式。

- [ ] **Step 4: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/fullstack/SKILL.md && git commit -m "feat: implement fullstack role sub-skill (upgraded from v2)"
```

### Task 6: 编写 product/SKILL.md（产品角色）

**Files:**
- Modify: `ai-coach/product/SKILL.md`（覆写占位）

- [ ] **Step 1: 编写产品角色完整内容**

内容参照 spec 第六节，包含：
- frontmatter
- 角色定位说明
- Step P1 意图识别（写 PRD/补充 PRD/需求分析/复盘）
- Step P2 历史资产盘点（6 项收集清单 + 零资料降级）
- Step P3 业务分析（6 个子环节：商业/用户/竞品/差距/需求列表/沟通准备）
- Step P4 PRD 产出引导（结构规划 + AI 可执行 PRD 标准 + 示范提示词）
- Step P5 原型产出引导（路径 A HTML + 路径 B 线框图）
- Step P6 交付物检查 + 开发交接指引
- 推荐 Skill 表
- 从 enterprise/SKILL.md 移入的产品知识库内容（战略分析、PRD 编写、用户研究）

- [ ] **Step 2: 验证行数和格式**

用 Read 检查，目标 ~300 行。确保 PRD 标准对比表、示范提示词模板完整。

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/product/SKILL.md && git commit -m "feat: implement product role sub-skill"
```

---

## Chunk 3: 开发角色（后端 + 测试 + 前端）

### Task 7: 编写 backend/SKILL.md（后端角色）

**Files:**
- Modify: `ai-coach/backend/SKILL.md`（覆写占位）

- [ ] **Step 1: 编写后端角色完整内容**

内容参照 spec 第七节，包含：
- frontmatter
- 角色定位（偏全栈，后台管理页面 100% 负责）
- Step B1 意图识别（5 选项 + 快捷路由）
- Step B2 技术上下文收集（7 项 + 零资料降级）
- Step B3 技术方案设计引导（方案结构 + 后台页面特别引导 + 示范提示词）
- Step B4 实施计划引导（6 Phase 任务拆分参考）
- Step B5 编码执行引导（5 条必须规则）
- Step B6 自测与交付引导（完整自测检查清单 + 示范提示词）
- Step B7 交付物检查
- B-Bug 修复流程
- B-Emergency 紧急故障流程
- B-Large 大型项目流程
- 推荐 Skill 表
- 从 enterprise/SKILL.md 移入的技术知识库内容（新功能/Bug/重构 checklist）

- [ ] **Step 2: 验证行数和格式**

目标 ~350 行。确保自测检查清单、示范提示词完整。

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/backend/SKILL.md && git commit -m "feat: implement backend role sub-skill"
```

### Task 8: 编写 testing/SKILL.md（测试角色）

**Files:**
- Modify: `ai-coach/testing/SKILL.md`（覆写占位）

- [ ] **Step 1: 编写测试角色完整内容**

内容参照 spec 第八节，包含：
- frontmatter
- 角色定位 + 输入依赖表（含降级策略）
- Step T1 意图识别
- Step T2 测试上下文收集（7 项 + 零资料降级）
- Step T3 测试策略规划（测试范围 + 金字塔 + 数据策略）
- Step T4 测试用例设计（三层：T4.1 单元 + T4.2 接口 + T4.3 e2e，含示例格式）
- Step T5 自动化执行引导（T5.1 TDD + T5.2 Playwright + T5.3 三代理模式）
- Step T6 测试报告生成引导（标准化报告模板 + 示范提示词）
- Step T7 缺陷管理与回归
- T-Quick 单接口快速测试
- T-Regression 回归测试流程
- 推荐 Skill 表

- [ ] **Step 2: 验证行数和格式**

目标 ~350 行。确保测试报告模板、用例格式完整。

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/testing/SKILL.md && git commit -m "feat: implement testing role sub-skill"
```

### Task 9: 编写 frontend/SKILL.md（前端角色）

**Files:**
- Modify: `ai-coach/frontend/SKILL.md`（覆写占位）

- [ ] **Step 1: 编写前端角色完整内容**

内容参照 spec 第九节（已修正为覆盖 Web+移动端+小程序），包含：
- frontmatter
- 角色定位（客户端应用全平台覆盖）+ 输入依赖表
- Step F1 意图识别
- Step F2 前端上下文收集（8 项，含目标平台判断 + 零资料降级）
- Step F3 技术方案设计引导（方案结构 + 技术选型引导表含 Web/移动端/小程序 + 示范提示词）
- Step F4 实施计划引导（6 Phase）
- Step F5 编码执行引导（6 条规则：TDD + 原型对照 + Mock 优先 + 小步提交 + Bug 处理 + 验证）
- Step F6 自测与交付引导（完整检查清单 + 示范提示词）
- Step F7 交付物检查
- F-Bug/F-Emergency/F-Large 特殊流程
- 推荐 Skill 表

- [ ] **Step 2: 验证行数和格式**

目标 ~350 行。

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/frontend/SKILL.md && git commit -m "feat: implement frontend role sub-skill"
```

---

## Chunk 4: 支撑模块（enterprise 精简 + evaluate 升级 + analyze_sessions.py）

### Task 10: 精简 enterprise/SKILL.md

**Files:**
- Modify: `ai-coach/enterprise/SKILL.md`

- [ ] **Step 1: 备份现有文件**

Run: `cp ~/.claude/skills/ai-coach/enterprise/SKILL.md ~/.claude/skills/ai-coach/enterprise/SKILL.md.v2.bak`

- [ ] **Step 2: 精简内容**

移除已迁移到角色子 skill 的内容：
- 第一部分"产品经理知识库" → 已移入 product/SKILL.md
- 第二部分"技术知识库"（新功能/Bug/重构）→ 已移入 backend/SKILL.md
- 第四部分"引导指南生成参考" → 已移入各角色子 skill

保留并整理：
- 第三部分"巨型项目全链路知识库"（六阶段框架 + 阶段引导指南）
- "企业级/巨型级通用"（跨团队协调 + 架构分析 + 风险评估 + 路线图模板 + Strangler Fig + 评估驱动开发）

更新 frontmatter：version 改为 3.0.0，description 精简为一行。

- [ ] **Step 3: 验证行数**

目标 ~150 行（从现有 ~350 行大幅精简）。

- [ ] **Step 4: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/enterprise/SKILL.md && git commit -m "refactor: slim down enterprise knowledge base, move role-specific content to sub-skills"
```

### Task 11: 重写 evaluate/SKILL.md

**Files:**
- Modify: `ai-coach/evaluate/SKILL.md`

- [ ] **Step 1: 备份现有文件**

Run: `cp ~/.claude/skills/ai-coach/evaluate/SKILL.md ~/.claude/skills/ai-coach/evaluate/SKILL.md.v2.bak`

- [ ] **Step 2: 编写角色路由逻辑**

新增入口逻辑：
- 读取 Memory 中的角色 → 路由到对应评估维度
- 无角色记忆时默认"一人全栈"维度

- [ ] **Step 3: 编写 5 套评估维度**

参照 spec 第十节，每套 8 维：
1. 一人全栈（现有微调）
2. 产品角色（历史资产利用/业务分析/PRD 完整度/原型交付/沟通质量/Skill 使用/上下文/成长）
3. 后端角色（TDD/技术方案/自测交付/SOP/代码提交/上下文/Bug 规范/成长）
4. 测试角色（用例设计/自动化比例/PRD 覆盖/金字塔/报告规范/Skill 使用/缺陷有效性/成长）
5. 前端角色（TDD/视觉还原/技术方案/自测交付/接口对接/SOP+提交/性能意识/成长）

每个维度包含：评分信号、评分规则、教学引导模板。

- [ ] **Step 4: 更新报告格式**

报告头部新增角色标识。history.json 新增 role 字段。

- [ ] **Step 5: 保留通用部分**

保留：Step 10-11（会话扫描）、Step 14-15（报告生成+回显）、Step 16（教学引导框架）。
更新 version 为 3.0.0。

- [ ] **Step 6: 验证行数**

目标 ~800 行。

- [ ] **Step 7: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/evaluate/SKILL.md && git commit -m "feat: upgrade evaluate with role-based scoring dimensions"
```

### Task 12: 升级 analyze_sessions.py

**Files:**
- Modify: `ai-coach/evaluate/analyze_sessions.py`

- [ ] **Step 1: 阅读现有脚本理解结构**

读取 analyze_sessions.py，理解现有信号提取逻辑。

- [ ] **Step 2: 新增角色信号字段**

在输出 JSON 中新增：
```python
"role": "",                  # 从 Memory 文件读取
"prd_references": 0,         # 提示词中引用 PRD 的次数
"prototype_outputs": 0,      # 产出原型的次数
"test_report_outputs": 0,    # 产出测试报告的次数
"mock_api_usage": 0,         # 使用 mock 接口的次数
"screenshot_count": 0,       # 截图验证的次数
"device_test_count": 0,      # 设备测试的次数
"verification_skill_usage": 0 # verification-before-completion 使用次数
```

- [ ] **Step 3: 添加角色读取逻辑**

从 `~/.claude/projects/*/memory/MEMORY.md` 中提取角色信息。

- [ ] **Step 4: 运行脚本验证**

Run: `python3 ~/.claude/skills/ai-coach/evaluate/analyze_sessions.py --dir ~/.claude/projects/ --days 1 --max 5`
Expected: 输出包含新增字段的 JSON

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/evaluate/analyze_sessions.py && git commit -m "feat: add role-based signal fields to session analyzer"
```

---

## Chunk 5: 文档 + 测试 + 验证

### Task 13: 重写安装使用.md

**Files:**
- Modify: `ai-coach/安装使用.md`

- [ ] **Step 1: 编写新的使用说明**

参照 spec 安装使用升级部分，包含：
- 快速开始（3 步说明）
- 五个角色介绍表
- 快捷用法示范
- 切换角色说明
- 复盘说明

- [ ] **Step 2: 更新安装说明**

改为引导运行 install.sh，保留手动安装方式作为备选。

- [ ] **Step 3: 编写 10 个场景示范**

保留现有 6 个场景（适配新版本格式），新增 4 个：
- 场景 7：产品经理写 PRD（产品角色完整流程）
- 场景 8：后端开发新功能含后台管理页面
- 场景 9：测试工程师做自动化测试
- 场景 10：前端开发移动端页面

- [ ] **Step 4: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/安装使用.md && git commit -m "docs: rewrite installation and usage guide for v3"
```

### Task 14: 重写测试计划 + 更新/新增测试用例

**Files:**
- Modify: `ai-coach/tests/TEST-PLAN.md`
- Modify: `ai-coach/tests/case-01-trigger-word-coach.md`（更新为角色选择场景）
- Create: `ai-coach/tests/case-51-*.md` ~ `case-70-*.md`（新增角色测试用例）

- [ ] **Step 1: 审查现有 50 个测试用例**

阅读所有 case-*.md 的标题和预期行为，标记：
- 需更新的用例（涉及入口流程、菜单变化的）
- 仍然适用的用例（Bug 修复、重构、评估等通用场景，对应 fullstack 角色）
- 需删除的用例（与新版本逻辑矛盾的）

- [ ] **Step 2: 更新需要修改的现有用例**

主要更新点：
- case-01：触发词"教练"现在先显示角色选择（首次）或角色菜单（已选角色）
- case-02：触发词"复盘"现在按角色维度评估
- case-40：新人首次使用现在包含自检初始化
- 其他涉及主菜单交互的用例

- [ ] **Step 3: 新增产品角色测试用例**

```
case-51-product-prd-with-history.md    # 有历史 PRD 和代码时写新 PRD
case-52-product-prd-zero-history.md    # 全新项目写 PRD
case-53-product-gap-analysis.md        # 产品能力差距分析
case-54-product-prototype-html.md      # 产出 HTML 原型
case-55-product-handoff-to-dev.md      # 交付物交接给开发
```

- [ ] **Step 4: 新增后端角色测试用例**

```
case-56-backend-new-feature-with-prd.md  # 基于 PRD 做技术方案+开发
case-57-backend-admin-page.md            # 后台管理页面开发
case-58-backend-self-test.md             # 自测达到交付标准
case-59-backend-emergency-hotfix.md      # 紧急线上故障处理
```

- [ ] **Step 5: 新增测试角色测试用例**

```
case-60-testing-full-flow.md           # 从 PRD+代码到测试报告全流程
case-61-testing-playwright-e2e.md      # Playwright e2e 测试引导
case-62-testing-regression.md          # 回归测试流程
case-63-testing-quick-api-test.md      # 单接口快速测试
```

- [ ] **Step 6: 新增前端角色测试用例**

```
case-64-frontend-mobile-new-feature.md  # 移动端新功能开发
case-65-frontend-web-spa.md             # Web SPA 开发
case-66-frontend-mock-first.md          # Mock 优先开发流程
case-67-frontend-device-compat.md       # 设备兼容测试
```

- [ ] **Step 7: 新增跨角色/通用测试用例**

```
case-68-role-selection-first-time.md   # 首次角色选择 + 自检初始化
case-69-role-switch.md                 # 角色切换
case-70-role-evaluate-product.md       # 产品角色复盘评估
```

- [ ] **Step 8: 重写 TEST-PLAN.md**

更新测试计划：
- P0 核心路径（~20 个）：入口+角色选择、各角色核心流程、评估
- P1 扩展路径（~25 个）：各角色变体场景、降级、特殊流程
- P2 边界场景（~25 个）：极端输入、错误处理、兼容性

- [ ] **Step 9: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/tests/ && git commit -m "test: update test plan and add 20 role-based test cases for v3"
```

### Task 15: 运行全量测试

- [ ] **Step 1: 运行 P0 核心路径测试（~20 个）**

按 TEST-PLAN.md 的 P0 批次，逐个执行测试用例：
1. 读取用例文档
2. 在新会话中调用 `/ai-coach`
3. 按用例描述交互
4. 对照验收标准检查
5. 将结果回写到用例文档

- [ ] **Step 2: 记录 P0 测试结果**

收集所有 P0 用例的通过/失败状态，记录失败原因。

- [ ] **Step 3: 修复 P0 中发现的问题**

对失败的用例，定位 SKILL.md 中的问题并修复。每次修复后重跑该用例确认通过。

- [ ] **Step 4: 运行 P1 扩展路径测试（~25 个）**

同 Step 1 流程。

- [ ] **Step 5: 修复 P1 中发现的问题**

同 Step 3。

- [ ] **Step 6: 运行 P2 边界场景测试（~25 个）**

同 Step 1 流程。

- [ ] **Step 7: 修复 P2 中发现的问题**

同 Step 3。

- [ ] **Step 8: 生成测试报告**

创建 `tests/TEST-REPORT-v3.md`，包含：
- 总通过率
- 各批次通过率
- 失败用例详情和修复记录
- 发现的问题和优化建议

- [ ] **Step 9: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/tests/ ai-coach/*.md ai-coach/**/*.md && git commit -m "test: complete v3 full test run and fixes"
```

### Task 16: 最终优化与发布

- [ ] **Step 1: 基于测试结果优化**

根据测试报告中的问题和建议，对各 SKILL.md 做最终调整：
- 修复引导流程中的措辞问题
- 优化示范提示词的实际效果
- 调整评估维度的评分规则（如果测试中发现不合理）
- 补充缺失的降级策略

- [ ] **Step 2: 清理临时文件**

```bash
rm -f ~/.claude/skills/ai-coach/SKILL.md.v2.bak
rm -f ~/.claude/skills/ai-coach/enterprise/SKILL.md.v2.bak
rm -f ~/.claude/skills/ai-coach/evaluate/SKILL.md.v2.bak
```

- [ ] **Step 3: 最终验证**

重新运行 install.sh 确认安装正常。
在新会话中输入"教练"，确认角色选择→引导流程正常。

- [ ] **Step 4: 最终 Commit + Tag**

```bash
cd ~/.claude/skills && git add -A ai-coach/ && git commit -m "feat: ai-coach v3.0.0 role-based upgrade complete"
git tag v3.0.0-ai-coach
```

- [ ] **Step 5: 推送到 GitLab**

```bash
cd ~/.claude/skills && git push origin main && git push origin v3.0.0-ai-coach
```

---

## 任务依赖关系

```
Task 1 (install.sh) ──┐
Task 2 (目录结构)  ────┤
Task 3 (入口 SKILL) ──┤
Task 4 (init) ────────┘
         │
         ▼
Task 5 (fullstack) ─── 可与 Task 6 并行
Task 6 (product)   ─── 可与 Task 5 并行
         │
         ▼
Task 7 (backend) ──── 可与 Task 8, 9 并行
Task 8 (testing) ──── 可与 Task 7, 9 并行
Task 9 (frontend) ─── 可与 Task 7, 8 并行
         │
         ▼
Task 10 (enterprise 精简) ── 可与 Task 11, 12 并行
Task 11 (evaluate 重写)  ── 可与 Task 10, 12 并行
Task 12 (analyze_sessions) ─ 可与 Task 10, 11 并行
         │
         ▼
Task 13 (安装使用.md)
Task 14 (测试用例)
Task 15 (全量测试 + 修复)
Task 16 (最终优化 + 发布)
```

**可并行的任务组：**
- Task 5 + 6（一人全栈 + 产品）
- Task 7 + 8 + 9（后端 + 测试 + 前端）
- Task 10 + 11 + 12（enterprise + evaluate + analyzer）

---

## 估算

| Chunk | 任务数 | 预计工作量 |
|-------|--------|-----------|
| Chunk 1: 基础设施 | 4 | 中 |
| Chunk 2: 核心角色 | 2 | 中 |
| Chunk 3: 开发角色 | 3 | 大 |
| Chunk 4: 支撑模块 | 3 | 大 |
| Chunk 5: 文档+测试 | 4 | 最大（测试+修复是重点） |
| **合计** | **16** | |
