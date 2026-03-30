# Harness Engineering 融合实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Harness Engineering 以三层渗透模型融入 ai-coach v3，总增量 < 100 行

**Architecture:** init 奠基（治具健康度检查）→ 各角色使用（对话中引用治具）→ evaluate 揭示（分层改进建议）。不新增子 skill，融入现有步骤。

**Tech Stack:** Markdown SKILL.md 文件编辑，Python 测试脚本

**Spec:** `docs/superpowers/specs/2026-03-28-harness-engineering-fusion-design.md`

---

## Chunk 1: SKILL.md 文件修改（7 个文件）

### Task 1: 主 SKILL.md — 全局规则第 10 条

**Files:**
- Modify: `~/.claude/skills/ai-coach/SKILL.md:25`（第 9 条之后）

- [ ] **Step 1: 在第 9 条全局规则后追加第 10 条**

在 `9. **子 skill description 精简**` 之后追加：

```markdown
10. **治具改进循环** — 引导过程中发现的上下文缺口（CLAUDE.md 缺少约定、Memory 无历史记录、缺少自动化 Hooks），建议用户永久修复到对应治具中，而非只改当前提示词。一次性修复 > 每次重复说明。
```

- [ ] **Step 2: 验证行数增量**

Run: `wc -l ~/.claude/skills/ai-coach/SKILL.md`
Expected: 约 94 行（原 92 + 2）

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/SKILL.md && git commit -m "feat(harness): 主 SKILL.md 全局规则 +治具改进循环"
```

---

### Task 2: fullstack/SKILL.md — 原则扩展 + 资料维度增强 + 出口治具建议

**Files:**
- Modify: `~/.claude/skills/ai-coach/fullstack/SKILL.md:15`（原则 1）
- Modify: `~/.claude/skills/ai-coach/fullstack/SKILL.md:116`（Step 3.1 后）
- Modify: `~/.claude/skills/ai-coach/fullstack/SKILL.md:217`（Step 3.4 末尾）

- [ ] **Step 1: 扩展原则 1**

将第 15 行：
```
1. **AI 是有注意力预算的协作者** — 信噪比越高越好，信息不是越多越好。用户提供过多或过少时提醒。
```
改为：
```
1. **AI 是有注意力预算的协作者** — 信噪比越高越好，信息不是越多越好。用户提供过多或过少时提醒。当 AI 表现不好时，先检查治具（CLAUDE.md/Memory/Skills/Hooks），再检查提示词。
```

- [ ] **Step 2: Step 3.1 资料维度增强**

在 Step 3.1 的上下文收集表之后、Step 3.2 之前，追加：

```markdown
**治具优先提取**：收集资料时，先检查 Memory 有无相关历史方案/决策 → 有则直接引用；检查 CLAUDE.md 有无相关技术约定 → 有则纳入约束。
```

- [ ] **Step 3: Step 3.4 追加出口治具建议**

在 Step 3.4 的引导结束输出内容末尾追加：

```markdown
3. 💡 治具建议（仅在发现缺口时输出）：CLAUDE.md 缺少本次涉及的约定 → 建议补充；本次产出有跨会话价值 → 建议摘要存入 Memory
```

- [ ] **Step 4: 验证行数增量**

Run: `wc -l ~/.claude/skills/ai-coach/fullstack/SKILL.md`
Expected: 约 238 行（原 234 + 4）

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/fullstack/SKILL.md && git commit -m "feat(harness): fullstack 原则扩展+治具优先提取+出口建议"
```

---

### Task 3: init/SKILL.md — 治具健康度检查

**Files:**
- Modify: `~/.claude/skills/ai-coach/init/SKILL.md:17-45`（Layer 1 重构）
- Modify: `~/.claude/skills/ai-coach/init/SKILL.md:47-76`（Layer 2 增强）

- [ ] **Step 1: 重构 Layer 1 CLAUDE.md 检查**

将 Layer 1 第 2 项（CLAUDE.md 检查，约第 21-29 行）从"存在性 + 4 段落"改为"存在性 + 4 关键段健康度"：

```markdown
### 2. CLAUDE.md
- 存在？→ 缺失则提醒创建（说"项目说明文件"而不是"CLAUDE.md"）
- 存在时检查 4 关键段完整度：
  | 关键段 | 检查方式 | 缺失提示 |
  |--------|---------|---------|
  | 技术栈 | 含 "tech" / "技术栈" / "stack" | 💡 建议补充项目技术栈，AI 能更准确推荐工具 |
  | 构建命令 | 含 "build" / "构建" / "gradlew" / "npm" | 💡 建议补充构建命令，AI 能直接帮你运行 |
  | 架构约定 | 含 "架构" / "architecture" / "目录" / "模块" | 💡 建议补充架构约定，AI 不会随意创建文件 |
  | 测试约定 | 含 "test" / "测试" / "TDD" | 💡 建议补充测试约定，AI 写的测试更符合项目规范 |
- 每个缺失段只提示一行，不阻塞流程
```

- [ ] **Step 2: 重构 Layer 1 Memory 检查**

将 Memory 检查（约第 31-34 行）从"目录存在"改为"目录 + 内容健康度"：

```markdown
### 3. Memory 目录
- `~/.claude/memory/` 或项目级 Memory 存在？→ 缺则静默创建
- 有角色记忆（`AI教练角色:` 格式）？→ 有则记录，跳过角色选择
- 有项目上下文记录？→ 有则在后续引导中可引用
```

- [ ] **Step 3: Layer 1 新增 Hooks 检查**

在 Layer 1 的第 4 项（superpowers skill）之后追加第 5 项：

```markdown
### 5. Hooks 配置（仅非首次用户）
- 仅当 Memory 中已有角色记忆时检查（首次用户跳过，避免信息过载）
- 检查 `.claude/settings.json` 是否配置了 hooks
- 无 hooks 时轻提一句：💡 进阶提示：配置 Hooks 可自动化代码检查，提升 AI 协作效率
- 有 hooks 则跳过，不输出
```

- [ ] **Step 4: Layer 2 增加历史产出检查**

在 Layer 2 各角色专属检查的通用规则部分追加：

```markdown
### 通用：历史产出检查
检查 Memory 中是否有当前角色的历史产出记录（技术方案/测试策略/PRD 决策等），有则标记供后续引导主动引用。
```

- [ ] **Step 5: 验证行数增量**

Run: `wc -l ~/.claude/skills/ai-coach/init/SKILL.md`
Expected: 约 150 行（原 121 + 29）

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/init/SKILL.md && git commit -m "feat(harness): init 治具健康度检查（CLAUDE.md 4 关键段 + Memory 内容 + Hooks）"
```

---

### Task 4: backend/SKILL.md — 入口/出口微引导

**Files:**
- Modify: `~/.claude/skills/ai-coach/backend/SKILL.md:43`（B2 头部）
- Modify: `~/.claude/skills/ai-coach/backend/SKILL.md:217`（B7 后）

- [ ] **Step 1: B2 头部追加治具引用规则**

在 `### Step B2: 技术上下文收集` 标题之后、收集表之前追加：

```markdown
> **治具优先**：收集前先检查 Memory 有无相关历史方案 → 有则"上次你做过 X，要复用吗？"；检查 CLAUDE.md 有无数据库/API 约定 → 有则直接纳入约束。
```

- [ ] **Step 2: B7 后追加出口治具建议**

在 Step B7 交付物检查末尾、"教练提醒"之后追加：

```markdown
💡 治具建议（仅在发现缺口时输出）：CLAUDE.md 缺少本次涉及的约定 → 建议补充；本次技术方案有跨会话价值 → 建议摘要存入 Memory。
```

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/backend/SKILL.md && git commit -m "feat(harness): backend B2 治具优先 + B7 出口建议"
```

---

### Task 5: testing/SKILL.md — 入口/出口微引导

**Files:**
- Modify: `~/.claude/skills/ai-coach/testing/SKILL.md:62`（T2 头部）
- Modify: `~/.claude/skills/ai-coach/testing/SKILL.md:507`（引导结束输出段落）

- [ ] **Step 1: T2 头部追加治具引用规则**

在 `### Step T2: 测试上下文收集` 标题之后、收集说明之前追加：

```markdown
> **治具优先**：收集前先检查 Memory 有无历史测试策略/报告 → 有则"上次的测试策略要复用吗？"；检查 CLAUDE.md 有无测试约定 → 有则直接纳入约束。
```

- [ ] **Step 2: 引导结束输出段落追加治具建议**

在"引导结束输出"段落的内容末尾追加：

```markdown
💡 治具建议（仅在发现缺口时输出）：CLAUDE.md 缺少测试约定 → 建议补充；本次测试策略有跨会话价值 → 建议摘要存入 Memory。
```

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/testing/SKILL.md && git commit -m "feat(harness): testing T2 治具优先 + 出口建议"
```

---

### Task 6: product/SKILL.md — 入口/出口微引导

**Files:**
- Modify: `~/.claude/skills/ai-coach/product/SKILL.md:50`（P2 头部）
- Modify: `~/.claude/skills/ai-coach/product/SKILL.md:288`（P6 后）

- [ ] **Step 1: P2 头部追加治具引用规则**

在 `## Step P2: 历史资产盘点` 标题之后、收集清单之前追加：

```markdown
> **治具优先**：盘点前先检查 Memory 有无上次 PRD 决策/产品分析记录 → 有则"上次的分析要复用吗？"；检查 CLAUDE.md 有无产品约定 → 有则纳入约束。
```

- [ ] **Step 2: P6 后追加出口治具建议**

在 Step P6 交付物检查末尾追加：

```markdown
💡 治具建议（仅在发现缺口时输出）：CLAUDE.md 缺少产品约定 → 建议补充；本次 PRD 关键决策有跨会话价值 → 建议摘要存入 Memory。
```

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/product/SKILL.md && git commit -m "feat(harness): product P2 治具优先 + P6 出口建议"
```

---

### Task 7: frontend/SKILL.md — 入口/出口微引导

**Files:**
- Modify: `~/.claude/skills/ai-coach/frontend/SKILL.md:63`（F2 头部）
- Modify: `~/.claude/skills/ai-coach/frontend/SKILL.md:406`（F7 后）

- [ ] **Step 1: F2 头部追加治具引用规则**

在 `## Step F2: 前端上下文收集` 标题之后、收集清单之前追加：

```markdown
> **治具优先**：收集前先检查 Memory 有无历史技术方案/组件设计 → 有则"上次的方案要复用吗？"；检查 CLAUDE.md 有无前端约定 → 有则纳入约束。
```

- [ ] **Step 2: F7 后追加出口治具建议**

在 Step F7 交付物检查末尾追加：

```markdown
💡 治具建议（仅在发现缺口时输出）：CLAUDE.md 缺少前端约定 → 建议补充；本次组件设计有跨会话价值 → 建议摘要存入 Memory。
```

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/frontend/SKILL.md && git commit -m "feat(harness): frontend F2 治具优先 + F7 出口建议"
```

---

## Chunk 2: evaluate/SKILL.md 评分扩展

### Task 8: evaluate — 各角色上下文工程评分子项扩展

**Files:**
- Modify: `~/.claude/skills/ai-coach/evaluate/SKILL.md:151-163`（A2 全栈）
- Modify: `~/.claude/skills/ai-coach/evaluate/SKILL.md:286-289`（B7 产品）
- Modify: `~/.claude/skills/ai-coach/evaluate/SKILL.md:340-342`（C6 后端）
- Modify: `~/.claude/skills/ai-coach/evaluate/SKILL.md:403`（D6 测试）
- Modify: `~/.claude/skills/ai-coach/evaluate/SKILL.md`（E6 前端，需定位）

- [ ] **Step 1: A2 全栈评分公式追加子项**

在 A2 评分公式（第 156-163 行）末尾、下一个维度之前追加：

```markdown
  Memory 有项目上下文记录: +10
  跨会话引用历史记录: +10
```

注意：A2 已有 `Hooks 配置: +10`，不重复加。

- [ ] **Step 2: B7 产品评分公式追加子项**

在 B7 评分公式（第 288 行）末尾追加：

```markdown
  Memory 有产品决策记录: +10, 跨会话引用: +10, Hooks: +5
```

- [ ] **Step 3: C6 后端评分公式追加子项**

在 C6 评分公式（第 342 行）末尾追加：

```markdown
  Memory 有技术方案记录: +10, 跨会话引用: +10
```

注意：C6 已有 `Hooks+10`，不重复加。

- [ ] **Step 4: D6 测试评分公式追加子项**

在 D6 评分公式（第 403 行附近）追加：

```markdown
  Memory 有测试策略记录: +10, 跨会话引用: +10, Hooks: +5
```

- [ ] **Step 5: E6 前端评分公式追加子项**

定位 E6 前端上下文工程维度，追加同样的子项：

```markdown
  Memory 有技术方案记录: +10, 跨会话引用: +10, Hooks: +5
```

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/evaluate/SKILL.md && git commit -m "feat(harness): evaluate 5 角色上下文工程评分子项扩展（Memory+跨会话+Hooks）"
```

---

### Task 9: evaluate — L1/L2/L3 分层改进建议

**Files:**
- Modify: `~/.claude/skills/ai-coach/evaluate/SKILL.md:527`（TOP 3 改进建议处）

- [ ] **Step 1: 在 TOP 3 改进建议生成逻辑后追加分层规则**

在第 530 行 `3. {基于第三低分维度的具体建议}` 之后追加：

```markdown
**上下文工程维度改进建议分层规则**（当该维度进入 TOP 3 最低分时使用）：

| 分数段 | 层级 | 建议聚焦 | 话术模板 |
|--------|------|---------|---------|
| < 40 | L1 基础 | 补全 CLAUDE.md 4 关键段 + 安装 3 个核心 Skills | "你的项目配置还比较基础，补全后 AI 能更准确理解你的项目" |
| 40-70 | L2 进阶 | Memory 跨会话利用 + Hooks 自动化 | "基础配置不错。下一步利用 Memory 记录决策，配置 Hooks 自动化检查" |
| > 70 | L3 专家 | 系统化治具审计 + 自定义约束 | "你已具备完整 AI 工作环境。了解 Harness Engineering 框架可帮你系统化维护和优化——治具质量决定 AI 产出上限" |

注意：仅 L3 话术包含 "Harness Engineering" 术语。L1/L2 只给操作建议。
```

- [ ] **Step 2: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/evaluate/SKILL.md && git commit -m "feat(harness): evaluate L1/L2/L3 分层改进建议"
```

---

## Chunk 3: 测试用例评审 + 优化 + 全量测试

### Task 10: 更新自动化测试脚本

**Files:**
- Modify: `~/.claude/skills/ai-coach/tests/test_skill_structure.py`

- [ ] **Step 1: 测试组 2 增加全局规则第 10 条检查**

在主 SKILL.md 结构测试中增加：
```python
# 检查全局规则第 10 条：治具改进循环
_check("主 skill: 治具改进循环规则", "治具改进循环" in main_content)
```

- [ ] **Step 2: 测试组 3 增加治具优先检查**

在各角色 sub-skill 结构测试中增加：
```python
# 检查各角色的治具优先提取
for role in ["backend", "testing", "product", "frontend"]:
    content = _read(SKILL_FILES[role])
    _check(f"{role}: 包含「治具优先」", "治具优先" in content)
```

- [ ] **Step 3: 测试组 4 增加 init 治具健康度检查**

```python
# 检查 init 治具健康度
_check("init: CLAUDE.md 4 关键段检查", "关键段" in init_content or "技术栈" in init_content)
_check("init: Hooks 检查", "Hooks" in init_content or "hooks" in init_content)
_check("init: 历史产出检查", "历史产出" in init_content)
```

- [ ] **Step 4: 测试组 5 增加 evaluate 分层建议检查**

```python
# 检查 evaluate L1/L2/L3 分层
_check("evaluate: L1 基础建议", "L1" in eval_content or "< 40" in eval_content)
_check("evaluate: L2 进阶建议", "L2" in eval_content or "40-70" in eval_content)
_check("evaluate: L3 专家建议含 Harness", "Harness Engineering" in eval_content)
```

- [ ] **Step 5: 运行测试验证新增项**

Run: `cd ~/.claude/skills/ai-coach && python3 tests/test_skill_structure.py`
Expected: 所有新增检查项通过

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/tests/test_skill_structure.py && git commit -m "test(harness): 自动化测试增加 Harness Engineering 检查项"
```

---

### Task 11: 新增 Harness 相关手动测试用例

**Files:**
- Create: `~/.claude/skills/ai-coach/tests/case-72-harness-init-health-check.md`
- Create: `~/.claude/skills/ai-coach/tests/case-73-harness-memory-reuse.md`
- Create: `~/.claude/skills/ai-coach/tests/case-74-harness-exit-suggestion.md`
- Create: `~/.claude/skills/ai-coach/tests/case-75-evaluate-l1-l2-l3.md`

- [ ] **Step 1: 创建 case-72（init 治具健康度检查）**

P0 用例：验证 init 对 CLAUDE.md 4 关键段缺失的提示行为。

- [ ] **Step 2: 创建 case-73（Memory 跨会话复用）**

P0 用例：验证后端角色 B2 收集时检查 Memory 并主动引用历史方案。

- [ ] **Step 3: 创建 case-74（出口治具建议）**

P1 用例：验证引导结束时条件性输出治具建议（有缺口才输出）。

- [ ] **Step 4: 创建 case-75（evaluate L1/L2/L3 分层建议）**

P1 用例：验证 evaluate 按分数分层输出不同话术，L3 含 Harness Engineering 术语。

- [ ] **Step 5: 更新 TEST-PLAN.md 加入新用例**

在 v3 用例执行批次中追加 case-72~75。

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills && git add ai-coach/tests/ && git commit -m "test(harness): 新增 4 个 Harness 相关测试用例 (case-72~75)"
```

---

### Task 12: 运行全量测试 + 行数验证

- [ ] **Step 1: 运行自动化测试**

Run: `cd ~/.claude/skills/ai-coach && python3 tests/test_skill_structure.py`
Expected: 100% 通过

- [ ] **Step 2: 验证总增量 < 100 行**

Run: `wc -l SKILL.md */SKILL.md | tail -1` 对比原始 3227 行
Expected: < 3327

- [ ] **Step 3: 修复任何失败的测试**

如有失败，定位根因并修复对应 SKILL.md 或测试脚本。

- [ ] **Step 4: Commit 修复（如有）**

---

## Chunk 4: 发布与交付

### Task 13: 最终提交 + tag

- [ ] **Step 1: 确认所有改动已提交**

Run: `cd ~/.claude/skills && git status`
Expected: nothing to commit, working tree clean

- [ ] **Step 2: 打 tag**

```bash
cd ~/.claude/skills && git tag v3.1.0-ai-coach -m "AI Coach v3.1.0: Harness Engineering 融合

三层渗透：init 治具健康度检查 → 各角色治具优先提取+出口建议 → evaluate L1/L2/L3 分层
总增量 < 100 行，不新增子 skill，不改核心叙事"
```

### Task 14: 整体替换 kos 项目路径

- [ ] **Step 1: 清空目标目录并复制**

```bash
rm -rf /Users/zhongtianyi01/work/claudecode/kos/skills/ai-coach
cp -r ~/.claude/skills/ai-coach /Users/zhongtianyi01/work/claudecode/kos/skills/ai-coach
```

- [ ] **Step 2: 清理不需要的文件**

移除软链接和 `.git` 相关（如有）：
```bash
cd /Users/zhongtianyi01/work/claudecode/kos/skills/ai-coach
rm -f ai-coach-backend ai-coach-frontend ai-coach-fullstack ai-coach-init ai-coach-product ai-coach-testing ai-coach-enterprise ai-coach-evaluate 2>/dev/null
```

- [ ] **Step 3: 验证目标目录结构完整**

```bash
ls -la /Users/zhongtianyi01/work/claudecode/kos/skills/ai-coach/*/SKILL.md
```
Expected: 8 个子 skill SKILL.md 文件

- [ ] **Step 4: 通知用户手动上传**

输出：
```
v3.1.0-ai-coach 已准备就绪：
- 源码路径：/Users/zhongtianyi01/work/claudecode/kos/skills/ai-coach/
- 请手动上传到 GitLab 仓库
- 团队成员安装命令：bash ai-coach/install.sh
```
