# AI-Coach v2.0.0 测试报告

**日期**: 2026-03-15
**版本**: ai-coach v2.0.0（三文件拆分架构）
**测试方法**: 对照 SKILL.md 静态验证 + 流程模拟
**测试用例总数**: 50

## 架构变更概述

v1 → v2 核心变化：
- 主 skill 从 1063 行精简到 263 行
- 评估模式拆分为 ai-coach-evaluate 子 skill（676 行）
- 企业级知识库拆分为 ai-coach-enterprise 子 skill（184 行）
- Step 2 从固定四类菜单改为开放式诊断
- Step 3-6 合并为通用 Step 3（四维诊断 + 方法论推荐 + 示范提示词）
- 评估从七维变八维（新增方法论内化度），等级从 L1-L3 变 L1-L5

## 总体结果

| 批次 | 总数 | PASS | PARTIAL | FAIL |
|------|------|------|---------|------|
| P0   | 17   | 15   | 2       | 0    |
| P1   | 23   | 18   | 5       | 0    |
| P2   | 10   | 9    | 1       | 0    |
| **合计** | **50** | **42** | **8** | **0** |

**总体通过率：84% PASS，16% PARTIAL，0% FAIL**

### 与 v1 对比

| 指标 | v1 | v2 | 变化 |
|------|----|----|------|
| PASS | 16 (32%) | 42 (84%) | +26 ↑↑ |
| PARTIAL | 26 (52%) | 8 (16%) | -18 ↓ |
| FAIL | 8 (16%) | 0 (0%) | -8 ↓↓ |

## P0 详细结果（17 个）

| Case | 标题 | v1→v2 | 核心发现 |
|------|------|-------|---------|
| 01 | 触发词"教练" | PARTIAL→PASS | Step 0 经验检测 + AskUserQuestion 在主会话可用 |
| 02 | 触发词"复盘" | FAIL→PASS | Step 1 快捷路由 → ai-coach-evaluate 子 skill |
| 03 | PRD 完整资料 | PASS→PASS | 通用四维诊断覆盖 PRD 场景 |
| 05 | 新功能后端 API | PARTIAL→PASS | 开放式诊断 + 三阶段工作流推荐 |
| 07 | Bug 修复完整复现 | PASS→PASS | Bug 修复铁律保留在 Step 3.2 |
| 10 | 超大型重构 | PARTIAL→PASS | 巨型级追加 + enterprise 子 skill |
| 16 | 评估今天会话 | PASS→PASS | 八维评分 + L1-L5 + 数据充分度判断 |
| 21 | PRD 零资料 | FAIL→PASS | 零资料降级策略完整覆盖 |
| 22 | Bug 模糊报告 | FAIL→PASS | 封闭式提问 + 最小可行上下文 |
| 31 | 评估零数据 | FAIL→PASS | Step 10.4 数据充分度判断 |
| 36 | 端到端完整周期 | PARTIAL→PASS | 通用 Step 3 + 复盘衔接建议 |
| 37 | Bug 修复→评估 | PARTIAL→PASS | Step 2→3 + ai-coach-evaluate 衔接 |
| 40 | 新人入职 | FAIL→PASS | Step 0 经验检测 + 术语速查 |
| 41 | KOS SCM 新功能 | PARTIAL→PASS | 开放式诊断替代固定菜单 |
| 42 | KOS OMS 退款 Bug | FAIL→PASS | Bug 分类表 + 修复铁律 |
| 46 | 紧急热修复 | FAIL→**PARTIAL** | 紧急修复铁律与 Bug 修复铁律存在张力 |
| 49 | 安全修复 SQL 注入 | FAIL→**PARTIAL** | 安全知识锁在 enterprise，标准级无法触达 |

## P1 详细结果（23 个）

| Case | 标题 | v1→v2 | 核心发现 |
|------|------|-------|---------|
| 04 | PRD 部分资料 | PASS→PASS | 零资料降级策略精确匹配 |
| 06 | 新功能前端页面 | PASS→PASS | 通用框架 + 前端定制扩展 |
| 08 | Bug 只有截图 | PASS→PASS | 四维诊断对非技术用户友好 |
| 09 | 重构性能优化 | PASS→PASS | 重构铁律 + 分析性工作流 |
| 11 | 新功能全栈 | PASS→PASS | 全栈工作流模板缺失但不影响核心 |
| 13 | Bug 性能问题 | PASS→PASS | 复合任务工作流组合依赖 AI 判断 |
| 14 | Bug 间歇性 | PASS→PASS | 通用引导比专项引导更灵活 |
| 17 | 评估最近一周 | PARTIAL→PASS | 百分制统一 + 八维评分 |
| 18 | 评估全部历史 | PARTIAL→PASS | 数据充分度判断 + 首次评估对比 |
| 23 | 新功能口头需求 | PARTIAL→PASS | 智能精简规则 + 零资料降级 |
| 24 | 重构目标模糊 | PARTIAL→PASS | 封闭式提问机制 |
| 25 | 中途切换流程 | PARTIAL→PASS | 全局规则：流程中断与切换 |
| 26 | 跳过所有检查项 | PARTIAL→PASS | 智能精简 + 零资料降级 |
| 28 | 极短输入 | PARTIAL→PASS | 快捷路由 + 极简输入规则 |
| 29 | 超长日志输入 | PARTIAL→PASS | 注意力预算原则 + Bug 修复铁律 |
| 33 | 评估无 CLAUDE.md | PASS→PASS | 八维独立评分 + 置信度标注 |
| 38 | 成长追踪 | PARTIAL→PASS | 四级状态标记（↑↑/↑/—/↓） |
| 39 | 超大型重构路线图 | PASS→PASS | enterprise 子 skill 按需加载 |
| 43 | KDS 厨显性能 | PARTIAL→**PARTIAL** | enterprise 前端性能提醒改善，Vue 特定优化缺失 |
| 44 | 用户登录升级 | PARTIAL→**PARTIAL** | 安全敏感类提醒改善，密码迁移策略缺失 |
| 47 | API 外部对接 | PARTIAL→**PARTIAL** | API 对接类提醒改善，OpenAPI 格式缺失 |
| 48 | 数据库迁移 | PARTIAL→**PARTIAL** | 数据库迁移类提醒改善，分步迁移模板缺失 |
| 50 | 跨模块自动补货 | PARTIAL→**PARTIAL** | 复杂架构决策深度引导仍不足 |

## P2 详细结果（10 个）

| Case | 标题 | v1→v2 | 核心发现 |
|------|------|-------|---------|
| 12 | 简单配置项 | PASS→PASS | Step 0 + 智能精简完美适配 |
| 15 | 可读性重构 | PASS→PASS | 重构铁律强制嵌入 |
| 19 | PRD 技术产品 | PARTIAL→**PARTIAL** | 通用引导缺 PRD 深度（量化痛点/ROI） |
| 20 | 评估极少数据 | PARTIAL→PASS | 数据充分度 + 置信度标注 |
| 27 | 无关问题 | PARTIAL→PASS | 全局规则显式定义 |
| 30 | 英文输入 | PARTIAL→PASS | 语言自适应规则 |
| 32 | 评估 1 个短会话 | PARTIAL→PASS | 数据充分度判断 |
| 34 | 中英混合+代码 | PASS→PASS | 语言自适应 + 开放式诊断 |
| 35 | 连续选其他 | PARTIAL→PASS | 重试上限 + 自由对话模式 |
| 45 | KOS 菜单重构 | PASS→PASS | 通用 Step 3 + 重构铁律 |

## 8 个 PARTIAL 的问题分类

### 问题 1: 紧急/安全场景与标准流程的张力（P0）
- **影响**: case-46, case-49
- **根因**: Bug 修复铁律"绝对不能直接改代码"与紧急修复"直接定位→最小修复"矛盾；安全修复知识在 enterprise 子 skill 中，标准级安全 Bug 不触发
- **建议**: 主 skill Step 3.2 增加紧急/安全例外条款；安全核心原则提升到主 skill

### 问题 2: 领域深度知识不足（P1）
- **影响**: case-43, 44, 47, 48, 50
- **根因**: enterprise 知识库"领域专项提醒"只有一行提示，缺具体 checklist
- **建议**: enterprise 各领域补充具体 checklist 和模板

### 问题 3: PRD 专项深度退化（P2）
- **影响**: case-19
- **根因**: 通用四维诊断对技术产品 PRD 缺量化痛点/ROI 引导
- **建议**: 降低 enterprise 调用门槛或主 skill 增加 PRD 提示

## 残留问题优先级

| # | 问题 | 优先级 | 影响 | 建议 |
|---|------|--------|------|------|
| 1 | 紧急修复与 Bug 铁律张力 | P0 | 46 | 主 skill 增加紧急例外 |
| 2 | 安全知识标准级不可达 | P0 | 49 | 安全核心原则提升到主 skill |
| 3 | enterprise 领域 checklist 不具体 | P1 | 43,44,47,48,50 | 补充具体 checklist |
| 4 | PRD 专项深度退化 | P2 | 19 | 降低 enterprise 调用门槛 |
| 5 | 信号提取脚本遗留 Bug | P2 | 16 | 修复 session_duration 等 |
| 6 | 全栈工作流模板缺失 | P3 | 11 | enterprise 增加指引 |
| 7 | 复合任务工作流未定义 | P3 | 13 | 主 skill 增加说明 |

> 报告由 ai-coach v2.0.0 测试流程生成
> 对比基线：v1（16 PASS / 26 PARTIAL / 8 FAIL）
