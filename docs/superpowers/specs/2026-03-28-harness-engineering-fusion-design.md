# AI Coach v3.1：Harness Engineering 融合设计

**日期**: 2026-03-28
**版本**: v3.1.0-ai-coach
**状态**: 设计中

## 背景

### 什么是 Harness Engineering

Harness Engineering 是 2025-2026 年兴起的工程学科，核心观点：AI agent 的产出质量不取决于模型本身，而取决于围绕模型的"治具系统"（harness）——包括上下文文件（CLAUDE.md/AGENTS.md）、持久化记忆（Memory）、工具链（Skills）、自动化钩子（Hooks）和架构约束。

三大支柱：
1. **Context Engineering**：设计 AI 看到的信息环境
2. **Architectural Constraints**：约束解空间提高可靠性
3. **Entropy Management**：对抗代码和上下文的熵增

业界共识："模型是商品，治具是护城河"（NxCode 2026）。LangChain 仅改治具不换模型，Terminal Bench 2.0 排名从 Top 30 跃升至 Top 5。

### ai-coach v3 现状

ai-coach v3 已隐式覆盖 ~65% 的 Harness Engineering 内容：
- Skills 推荐跨角色完整
- TDD 铁律、Bug 修复铁律、6 Phase 拆分 = 架构约束
- evaluate 有上下文工程评分维度

但存在关键缺失：
- **从未用 Harness Engineering 框架命名和组织**，用户无法建立系统性认知
- **Memory/Hooks 在执行角色（backend/testing/product/frontend）中完全缺失**
- **治具改进循环缺失**：AI 表现不好时不引导用户改进治具
- **评分建议无分层**：新手和专家看到相同的改进建议

### 参考资料

- Martin Fowler: [Harness Engineering](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html)
- Anthropic: [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- NxCode: [Harness Engineering Complete Guide 2026](https://www.nxcode.io/resources/news/harness-engineering-complete-guide-ai-agent-codex-2026)
- OpenAI: [Harness Engineering](https://openai.com/index/harness-engineering/)

## 设计目标

将 Harness Engineering 融合到 ai-coach v3 中，使用户在正常使用过程中**自然习得**治具建设能力。

### 约束

1. **渐进式融合**：不改核心叙事和定位，行为中植入
2. **轻量融入**：不新增步骤/收集项，融入现有对话流
3. **分层揭示**：L1 只做操作 → L2 感知价值 → L3 揭示完整框架
4. **控制膨胀**：总增量 < 100 行

## 架构：三层渗透模型

```
init（奠基层）→ 各角色（使用层）→ evaluate（揭示层）
  治具健康度检查     对话中自然引用治具    评分 + 分层改进建议
```

Harness Engineering 作为**横切关注点**渗透到现有架构中，不新增子 skill。

## 详细设计

### 变更 1：主 SKILL.md — 全局规则 +1 条

**位置**：全局规则第 10 条

```markdown
10. **治具改进循环** — 引导过程中发现的上下文缺口（CLAUDE.md 缺少约定、Memory 无历史记录、
    缺少自动化 Hooks），建议用户永久修复到对应治具中，而非只改当前提示词。
    一次性修复 > 每次重复说明。
```

**行数**：+3

### 变更 2：fullstack/SKILL.md — 原则扩展 + 资料维度增强

**位置 A**：五大核心原则第 1 条

当前：
```
1. AI 是有注意力预算的协作者——信噪比越高越好
```

改为：
```
1. AI 是有注意力预算的协作者——信噪比越高越好。
   当 AI 表现不好时，先检查治具（CLAUDE.md/Memory/Skills/Hooks），再检查提示词。
```

**位置 B**：Step 3.1 四维诊断，"资料"维度后追加

```markdown
资料收集时，优先从治具提取：
- Memory 中是否有相关历史方案/决策记录 → 有则直接引用
- CLAUDE.md 中是否有相关技术约定 → 有则纳入约束条件
```

**行数**：+4

### 变更 3：init/SKILL.md — 治具健康度检查

**Layer 1 重构**：从存在性检查升级为健康度检查

| 检查项 | 当前 | 重构后 |
|--------|------|--------|
| CLAUDE.md | 存在？缺则提醒 | 存在？→ 4 关键段完整？（技术栈/构建命令/架构约定/测试约定）→ 缺段提醒补充 |
| Memory | 目录存在？缺则创建 | 目录存在？→ 有角色记忆？→ 有项目上下文记录？ |
| Skills | superpowers 装了？ | 不变 |
| Hooks | （无） | 新增：settings.json 有 hooks？→ 非首次用户轻提"进阶可配 hooks" |

**检查原则**：
- 发现缺失时**只提示不阻塞**，用 `💡` 标记
- 首次用户不提 "Harness" 术语
- Hooks 检查仅对非首次用户（Memory 有角色记忆）触发

**Layer 2 增强**：角色专属检查增加通用规则

```markdown
检查 Memory 中是否有当前角色的历史产出记录（技术方案/测试策略/PRD 决策等），
有则在后续引导中主动引用。
```

**行数**：+29（121→约 150）

### 变更 4：四个角色入口/出口微引导

**入口（上下文收集时）**：各角色收集步骤头部增加

```markdown
收集上下文时，优先从治具提取：
- 检查 Memory 有无相关历史记录 → 有则主动说"上次你做过 X，要复用/参考吗？"
- 检查 CLAUDE.md 有无相关约定 → 有则纳入约束，无需用户重复说明
```

**出口（引导结束时）**：引导结束提醒后追加

```markdown
💡 治具建议（仅在引导过程中发现缺口时输出）：
- 发现 CLAUDE.md 缺少 {本次涉及的约定} → 建议补充
- 本次产出的 {方案/策略/决策} 有跨会话价值 → 建议摘要存入 Memory
- 不输出则跳过，不强制每次都建议
```

**各角色具体位置**：

| 角色 | 入口位置 | 出口位置 | 行数 |
|------|---------|---------|------|
| backend | B2 收集 7 项头部 | B7（交付物检查）后 | +5 |
| testing | T2 收集 7 项头部 | "引导结束输出"段落处 | +5 |
| product | P2 历史资产盘点头部 | P6（交付物检查）后 | +5 |
| frontend | F2 收集 8 项头部 | F7（交付物检查）后 | +5 |

**注意**：fullstack 角色的入口已在变更 2 中覆盖（Step 3.1 资料维度增强），出口在 Step 3.4 追加同样的治具建议模板（+3 行，计入变更 2 的 +4 行中）。

**行数**：+20

### 变更 5：evaluate/SKILL.md — 评分扩展 + 分层建议

**5a：评分子项扩展（保留角色差异）**

不做统一公式。在各角色**现有评分公式基础上**，增加以下通用子项：

```markdown
各角色上下文工程维度新增子项（在现有子项之后追加）：
  Memory 有项目上下文记录（技术方案/测试策略/PRD 决策等）：+10
  跨会话引用历史记录：+10
  Hooks 有配置（.claude/settings.json）：+5（现有 A2/C6 已含此项的不重复加）

各角色保留各自的特色子项不变：
  - A2（全栈）：快速命令/技术栈/架构约定/测试约定
  - B7（产品）：产品约定/docs 有组织
  - C6（后端）：构建命令/技术栈/测试约定
  - D6（测试）：保持现有
  - E6（前端）：保持现有
```

**原则**：角色特色 > 统一性。总分归一化到维度权重范围内（以各角色理论最高分为基数）。

**5b：改进建议分层**

Step 14 终端摘要的 TOP 3 改进建议生成逻辑增加分层规则：

```markdown
上下文工程维度改进建议生成规则：

< 40 分（L1 基础）：
  聚焦：补全 CLAUDE.md 4 关键段 + 安装 3 个核心 Skills
  话术："你的项目配置还比较基础，补全后 AI 能更准确理解你的项目"

40-70 分（L2 进阶）：
  聚焦：Memory 跨会话利用 + Hooks 自动化配置
  话术："基础配置不错。下一步利用 Memory 记录决策，配置 Hooks 自动化检查"

> 70 分（L3 专家）：
  聚焦：系统化治具审计 + 自定义约束
  话术："你已具备完整 AI 工作环境。了解 Harness Engineering 框架可帮你
        系统化维护和优化——治具质量决定 AI 产出上限"
```

**触发条件**：当上下文工程维度进入 TOP 3 最低分时，使用上述分层话术；否则按现有逻辑（"基于最低分维度的具体建议"）输出。

**关键**：只有 L3（>70 分）用户会看到 "Harness Engineering" 术语。

**行数**：+40（734→约 774）

## 膨胀预算

| 文件 | 当前 | 新增 | 占比 |
|------|------|------|------|
| 主 SKILL.md | 92 | +3 | 3.3% |
| fullstack | 234 | +4 | 1.7% |
| init | 121 | +29 | 24% |
| backend | 435 | +5 | 1.1% |
| testing | 526 | +5 | 1.0% |
| product | 407 | +5 | 1.2% |
| frontend | 585 | +5 | 0.9% |
| evaluate | 734 | +40 | 5.4% |
| enterprise | 93 | 0 | 0% |
| **合计** | **3227** | **+96** | **3.0%** |

## 不做的事

1. **不新增子 skill** — Harness 是横切关注点，不是角色
2. **不改核心叙事** — ai-coach 仍然是"AI 编程教练"
3. **不增加流程步骤** — 所有治具引导融入现有步骤
4. **不给各角色加熵管理段落** — 全局规则 2"新会话分离" + 出口"存 Memory"已覆盖
5. **不强制 Hooks 配置** — Hooks 只建议不阻塞，非首次用户才提

## 实施与验证

### 实施顺序

1. 修改 7 个 SKILL.md 文件（主/fullstack/init/backend/testing/product/frontend）
2. 修改 evaluate/SKILL.md
3. 评审并优化 tests/ 下的测试用例（更新现有 + 新增 Harness 相关用例）
4. 运行全量测试，修复发现的问题
5. 生成测试报告
6. git commit + tag v3.1.0-ai-coach
7. 用户手动上传到 GitLab 仓库，团队成员安装

### 验收标准

- [ ] 全局规则第 10 条存在且被各角色继承
- [ ] fullstack 原则 1 包含治具检查提示
- [ ] init Layer 1 检查 CLAUDE.md 4 关键段完整度
- [ ] init Layer 1 对非首次用户检查 Hooks 配置
- [ ] 4 个角色入口有治具引用行为规则
- [ ] 4 个角色出口有条件性治具建议
- [ ] evaluate 评分公式含静态上下文/动态上下文/工具链三子项
- [ ] evaluate 改进建议按 L1/L2/L3 分层输出
- [ ] L3 改进建议包含 "Harness Engineering" 术语
- [ ] L1/L2 改进建议不包含 "Harness Engineering" 术语
- [ ] 总增量 < 100 行
- [ ] 自动化测试 100% 通过
- [ ] 测试用例覆盖 Harness 相关场景
