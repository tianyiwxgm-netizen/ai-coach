# AI Coach v4.0 实施计划

> **基于**: REFACTOR_SPEC_v4.md（方案 B）
> **日期**: 2026-03-31
> **知识库**: 已就绪（28 文件 584KB）

---

## 任务总览

共 9 个任务，按依赖顺序排列。Task 1-2 无依赖可并行，其余串行。

```
T1 COACH_TEMPLATE ──┐
                    ├→ T3 主入口 → T4 fullstack → T5 backend → T6 frontend → T7 product → T8 testing → T9 init
T2 知识库INDEX适配 ─┘
```

---

## T1: 新建 common/COACH_TEMPLATE.md

**输入**: Spec 4.2 节
**产出**: `common/COACH_TEMPLATE.md`（~120 行）

内容要点：
1. Phase 1 理解（Round 1 任务快照 3 问，Round 2 复杂度判断）
2. Phase 2 诊断框架（每轮最多 3 问，退出条件）
3. Phase 3 方法论指导报告模板（固定格式）
4. 硬性约束红线（不给表/接口/代码）
5. 知识库引用规则（查 INDEX → 读文件 → 提取要点）

**验收**: 文件存在，格式可被角色 SKILL 引用。

---

## T2: 适配 knowledge/INDEX.md 的场景映射

**输入**: 现有 INDEX.md + Spec 4.3 节
**产出**: 更新 `knowledge/INDEX.md`

当前 INDEX.md 已创建且内容完整，本任务做微调：
1. 确保场景映射表覆盖所有角色的常见任务类型
2. 确认文件路径引用正确（使用实际的中文文件名）
3. 补充「教练使用指南」中的 Phase 对应说明

**验收**: INDEX.md 中所有引用的文件路径实际存在。

---

## T3: 重写 SKILL.md 主入口

**输入**: Spec 4.1 节 + 现有 SKILL.md（95 行）
**产出**: 新 `SKILL.md`（~150 行）

重写内容：
1. 版本号升级到 `4.0.0`
2. 3 个平行入口（AskUserQuestion 格式）
   - 问题/脑暴 → 自动角色匹配
   - 角色视角 → 角色选择
   - 总结评估 → evaluate
3. 精简全局规则（13 条 → 6 条核心）
4. 启动触发（init + Memory 检查）
5. 角色路由表保留（快捷匹配用）
6. 删除旧的 Step 0.1-0.4 复杂流程

**备份**: 重写前将现有文件备份为 `SKILL.md.v3.bak`

**验收**: `/ai-coach` 触发后展示 3 入口选择。

---

## T4: 重构 fullstack/SKILL.md（标杆）

**输入**: 现有 fullstack/SKILL.md（240 行）+ COACH_TEMPLATE
**产出**: 新 `fullstack/SKILL.md`（~200 行）

这是第一个重构的角色，作为其他角色的参照标杆。

重构要点：
1. 头部加 `## 遵循模板` 声明
2. 保留「教练内功心法」（五大核心原则 + 六个心智跃迁 + 复杂度阶梯）— 这些是全栈角色的核心价值
3. 删除 Step 0（经验检测）— 移入主入口或 COACH_TEMPLATE
4. 重写 Step 1-4 为 Phase 2 诊断问题池格式：
   - 从现有 Step 2 的诊断问题提取
   - 按简单/中等/复杂分级
5. 删除所有「直接方案输出」部分，替换为方法论映射表
6. 领域方法论映射：覆盖全栈场景到 knowledge/ 文件
7. 降级策略从现有内容提取

**验收**: 遵循模板结构，无直接方案输出。

---

## T5: 重构 backend/SKILL.md

**输入**: 现有 backend/SKILL.md（443 行）+ COACH_TEMPLATE + fullstack 标杆
**产出**: 新 `backend/SKILL.md`（~250 行）

重构要点：
1. 遵循模板声明
2. 角色定位保留（偏全栈，后台管理系统页面由后端负责）
3. Phase 2 诊断问题池：从现有 Step B2 的 7 项收集清单提取核心问题
   - 简单：代码位置 + 目标
   - 中等：+ PRD 状态 + 现有 API
   - 复杂：+ 数据量 + 历史方案 + 架构约束
4. 删除 Step B3 技术方案设计引导（直接给表结构的部分）
5. 删除 Step B4 编码引导（给代码模板的部分）
6. 保留 B-Bug / B-Emergency / B-Large 的场景识别关键词，但引导方式改为方法论推荐
7. 领域方法论映射 + 降级策略

**验收**: 无表结构/API 规格输出，只有方法论推荐。

---

## T6: 重构 frontend/SKILL.md

**输入**: 现有 frontend/SKILL.md（591 行）+ COACH_TEMPLATE + 标杆
**产出**: 新 `frontend/SKILL.md`（~300 行）

重构要点：
1. 遵循模板声明
2. Phase 2 诊断问题池：从现有收集清单提取
3. 保留前端特有的场景识别（Web/移动端/小程序/响应式）
4. 删除所有具体方案输出（组件结构、样式方案等）
5. 领域方法论映射（前端场景 → knowledge/ 文件）
6. 降级策略

**验收**: 同 T5 标准。

---

## T7: 重构 product/SKILL.md

**输入**: 现有 product/SKILL.md（417 行）+ COACH_TEMPLATE + 标杆
**产出**: 新 `product/SKILL.md`（~250 行）

重构要点：
1. 遵循模板声明
2. Phase 2 诊断问题池：从现有收集清单提取
3. 保留产品特有场景（PRD 写作、需求评审、竞品分析）
4. 删除直接 PRD 模板输出，改为推荐 `prd-development` skill + 方法论
5. 领域方法论映射（重点引用 `09-商业落地.md`）
6. 降级策略

**验收**: 同 T5 标准。

---

## T8: 重构 testing/SKILL.md

**输入**: 现有 testing/SKILL.md（530 行）+ COACH_TEMPLATE + 标杆
**产出**: 新 `testing/SKILL.md`（~280 行）

重构要点：
1. 遵循模板声明
2. Phase 2 诊断问题池：从现有收集清单提取
3. 保留测试特有场景（E2E/单元测试/性能测试/安全测试）
4. 删除直接测试方案输出（用例模板等），改为方法论推荐
5. 领域方法论映射（重点引用 `07-评估驱动开发.md`）
6. 降级策略

**验收**: 同 T5 标准。

---

## T9: 更新 init/SKILL.md + install.sh

**输入**: 现有 init/SKILL.md（135 行）+ Spec 4.5 节
**产出**: 更新后的 `init/SKILL.md` + `install.sh`

更新要点：
1. init: Layer 1 新增 Step 0 版本检查（静默，3秒超时）
2. init: 所有版本号更新到 4.0.0
3. install.sh: 确保复制 common/ 和 knowledge/ 目录

**验收**: 启动时静默检查版本，网络失败不报错。

---

## 执行方式

建议使用 `/subagent-driven-development` 并行执行：
- **Wave 1**（并行）: T1 + T2
- **Wave 2**: T3（依赖 T1）
- **Wave 3**（并行）: T4（标杆先行）
- **Wave 4**（并行）: T5 + T6 + T7 + T8（参照 T4 标杆）
- **Wave 5**: T9

每个 Task 完成后做 diff 检查，确保：
- [ ] 无直接方案输出（表/接口/代码）
- [ ] 引用 COACH_TEMPLATE
- [ ] 引用 knowledge/ 文件路径正确
- [ ] 版本号为 4.0.0
