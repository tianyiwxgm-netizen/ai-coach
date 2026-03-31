# Agent系统设计：从工作流到自主Agent的架构指南

> **核心洞见：Agent不是"更高级的提示词"，而是一种系统架构范式——LLM在循环中自主使用工具，通过观察-思考-行动的反馈闭环完成复杂任务。设计好的Agent系统，关键不在Agent本身，而在工具设计、状态管理和失败恢复机制。**

---

## 一、为什么有效——Agent的底层原理

### 1.1 Agent的本质定义

Anthropic在《Building Effective Agents》中给出了迄今最精确的定义：

> **Agent = LLM在循环中自主使用工具（LLMs autonomously using tools in a loop）**

拆解这个定义的每个关键词：

- **循环（Loop）**：不是一次性调用，而是反复执行"观察→思考→行动→观察"。循环赋予了Agent自我纠错能力——第一次做错了，看到错误反馈，下一轮可以修正。
- **自主（Autonomously）**：由LLM自己决定下一步做什么、调用什么工具、何时停止。人类设定目标和边界，LLM决定路径。
- **工具（Tools）**：搜索引擎、代码执行器、API调用、文件操作——这些是Agent与外部世界交互的接口。没有工具的LLM只能"想"，有了工具才能"做"。

用一个最简单的伪代码表达Agent的本质：

```python
while not task_completed:
    observation = get_current_state()      # 看到什么
    thought = llm.think(observation)        # 想做什么
    action = llm.choose_tool(thought)       # 选择工具
    result = execute(action)                # 执行动作
    task_completed = check_done(result)     # 检查是否完成
```

这就是全部了。所有复杂的Agent框架，本质上都是在这个循环上做文章。

### 1.2 Workflow vs Agent——一个关键区分

Anthropic明确区分了两个概念，这个区分决定了你的系统架构选择：

```
Workflow（工作流）：
  预定义的路径编排。人类设计好了"先做A，再做B，如果X则做C"。
  LLM是执行者，路径是固定的。
  类比：装配流水线——每个工位做什么是预设的。

Agent（自主Agent）：
  LLM动态决定过程和工具使用。人类只定义目标和可用工具。
  LLM既是执行者，也是决策者。
  类比：自由职业者——你给他目标，他自己决定怎么干。
```

**关键原则：从Workflow开始，只在必要时升级到Agent。** 大多数任务用Workflow就能很好解决，而且更可预测、更易调试。Anthropic原文强调："对于很多应用，优化单次LLM调用加上检索和上下文示例通常就够了。"

### 1.3 为什么Agent模式能带来质变

Andrew Ng的实验数据是最有力的证据：

```
HumanEval编码基准测试：
  GPT-3.5 零样本 .......... 48.1%
  GPT-4   零样本 .......... 67.0%
  GPT-3.5 + Agent工作流 ... 95.1%
```

一个"弱"模型（GPT-3.5）加上Agent工作流，超过了"强"模型（GPT-4）的裸跑。提升幅度从48%到95%——接近翻倍。

原理很直观：人类解决复杂问题也不是"想一次就得到答案"。我们会尝试、犯错、检查、修正、再尝试。Agent工作流赋予了LLM同样的能力——允许它犯错，但给它纠错的机会。

---

## 二、Andrew Ng的四大Agent设计模式

Andrew Ng在DeepLearning.AI的Agentic AI课程中提出了四种基本设计模式。这些不是互斥选择，而是可以组合使用的构建块。

### 2.1 反思（Reflection）

**原理：** LLM检查自己的输出，发现问题并改进。最简单但最被低估的模式。

```
基本反思流程：
  生成初始输出 → 让同一个LLM（或另一个）审查输出 →
  基于审查反馈修改 → 再次审查 → 直到满意

具体实现：
  1. 生成代码
  2. "请审查这段代码的bug、性能和可读性问题"
  3. 基于审查结果修改
  4. 重复1-2轮
```

**适用场景：** 代码审查、文案润色、方案论证、逻辑验证。任何"做完之后检查一遍会更好"的任务。

**关键数据：** 仅靠反思这一个模式，代码生成的正确率就能提升15-30%。成本是多用了1-2次LLM调用，但效果显著。

### 2.2 工具使用（Tool Use）

**原理：** LLM自己不擅长的事情（精确计算、实时搜索、代码执行），交给专门的工具来做。

```
工具使用流程：
  用户请求 → LLM分析需求 → 决定调用什么工具 →
  调用工具 → 获取结果 → LLM基于结果生成回答

常见工具类型：
  - 搜索引擎（获取实时信息）
  - 代码执行器（精确计算、数据处理）
  - API调用（发邮件、查数据库、操作系统）
  - 文件操作（读写文件、处理文档）
  - 浏览器控制（访问网页、填写表单）
```

**重要洞见：** Anthropic在SWE-bench（软件工程基准）上的经验表明，他们花在工具优化上的时间超过了花在主提示词上的时间。工具的设计质量直接决定Agent的表现上限。

### 2.3 规划（Planning）

**原理：** 面对复杂任务，先制定多步骤计划，再按计划逐步执行。

```
规划流程：
  复杂任务 → LLM制定执行计划（分解为子任务）→
  按顺序执行每个子任务 → 执行中可动态调整计划

示例——"帮我写一个完整的用户认证模块"：
  计划：
  1. 设计数据模型（用户表、Session表）
  2. 实现注册接口
  3. 实现登录接口（JWT生成）
  4. 实现中间件（Token验证）
  5. 编写单元测试
  6. 编写API文档
  → 逐步执行，每步完成后验证
```

**注意点：** 规划能力是LLM的相对弱项。计划不宜过长（建议3-7步），每步应可独立验证。对于超复杂任务，分层规划（先粗后细）比一次性详细规划更可靠。

### 2.4 多Agent协作（Multi-Agent Collaboration）

**原理：** 多个Agent扮演不同角色，通过对话和协作完成任务。每个Agent有自己的专业领域和提示词。

```
多Agent协作模式：

模式A：辩论式（多角度验证）
  Agent-分析师：从数据角度分析
  Agent-批评者：找出论证中的漏洞
  Agent-综合者：整合各方观点得出结论

模式B：流水线式（分工协作）
  Agent-研究员：收集信息 →
  Agent-写手：撰写初稿 →
  Agent-编辑：审查修改 →
  Agent-排版：最终格式化

模式C：监督式（层级管理）
  Supervisor Agent：分配任务、审查结果
    ├── Worker Agent 1：处理子任务A
    ├── Worker Agent 2：处理子任务B
    └── Worker Agent 3：处理子任务C
```

**Andrew Ng的警告：** 多Agent系统在Demo中看起来很酷，但在生产环境中增加了大量复杂度。只有当单Agent确实无法胜任时才使用。每多一个Agent，调试难度和延迟都成倍增加。

---

## 三、Anthropic的五种工作流模式——怎么用

Anthropic在《Building Effective Agents》中提出了五种工作流模式，按复杂度递增排列。这是目前业界最实用的分类框架。

### 3.1 提示链（Prompt Chaining）

**本质：** 固定顺序串联多次LLM调用，前一步的输出是下一步的输入。

```
适用条件：
  - 任务可以分解为明确的、有固定顺序的子步骤
  - 每一步可以独立验证
  - 不需要动态调整路径

实现模式：
  Step1: 分析需求 → [输出: 需求规格]
  Step2: 基于需求规格设计方案 → [输出: 设计文档]
  Step3: 基于设计文档生成代码 → [输出: 代码]
  ↓ 每步之间可以加"门控"——检查上一步输出质量
```

**典型场景：** 长文档生成（先大纲再正文）、多语言翻译流水线、数据处理管道。

### 3.2 路由（Routing）

**本质：** 先分类输入，然后将不同类别分发到专门的处理器。

```
适用条件：
  - 输入类型多样，不同类型需要不同处理逻辑
  - 每种类型的最佳处理方式差异较大

实现模式：
  用户输入 → 分类器（LLM或规则）
    ├── 类型A → 专用提示词A处理
    ├── 类型B → 专用提示词B处理
    └── 类型C → 专用提示词C处理
```

**典型场景：** 客服系统（技术问题/退款/咨询分流）、代码助手（bug修复/新功能/重构分流）。

### 3.3 并行化（Parallelization）

**本质：** 同时运行多个LLM调用，然后聚合结果。

```
适用条件：
  - 子任务之间没有依赖关系
  - 需要多角度分析或投票
  - 对延迟敏感，需要加速

两种子模式：

分片并行（Sectioning）：
  大任务 → 拆分为独立子任务
    ├── 子任务1 → 结果1 ─┐
    ├── 子任务2 → 结果2 ──┼─→ 聚合最终结果
    └── 子任务3 → 结果3 ─┘

投票并行（Voting）：
  同一任务 → 多次独立执行
    ├── 执行1 → 结果1 ─┐
    ├── 执行2 → 结果2 ──┼─→ 取最一致的结果
    └── 执行3 → 结果3 ─┘
```

**典型场景：** 代码审查（安全/性能/可读性并行审查）、内容审核（多维度同时评估）、可靠性要求高的决策（多次投票取共识）。

### 3.4 编排者-工人（Orchestrator-Workers）

**本质：** 一个中心Agent（编排者）动态分解任务，分配给专门的工人Agent执行。

```
适用条件：
  - 任务复杂，无法预先确定所有子任务
  - 需要根据中间结果动态调整计划
  - 子任务可能需要不同的工具和能力

实现模式：
  复杂任务 → 编排者Agent
    │ 分析任务，制定初步计划
    ├── 分配子任务1 → 工人Agent A → 结果1
    │   编排者检查结果1，调整计划
    ├── 分配子任务2 → 工人Agent B → 结果2
    │   编排者检查结果2，发现需要额外步骤
    ├── 分配子任务3 → 工人Agent C → 结果3
    └── 编排者综合所有结果 → 最终输出
```

**典型场景：** 跨多文件的代码重构、复杂研究报告生成、系统架构设计。

### 3.5 评估者-优化者（Evaluator-Optimizer）

**本质：** 一个Agent生成输出，另一个Agent评估并提供改进反馈，反复迭代直到质量达标。

```
适用条件：
  - 有明确的质量标准可以评估
  - 迭代改进能显著提升质量
  - 单次生成难以达到目标质量

实现模式：
  任务 → 生成者Agent → 初始输出
    → 评估者Agent → 反馈（通过/不通过 + 改进建议）
    → 如果不通过 → 生成者Agent → 改进输出
    → 评估者Agent → 反馈
    → ...直到通过或达到最大迭代次数
```

**典型场景：** 文学翻译（反复润色）、代码优化（性能测试+改进循环）、营销文案（A/B测试+迭代）。

### 模式选择决策表

| 你的情况 | 推荐模式 | 原因 |
|---------|---------|------|
| 任务步骤固定、线性 | 提示链 | 最简单、最可预测 |
| 输入类型多样 | 路由 | 不同类型用不同策略 |
| 可以同时做多件事 | 并行化 | 减少延迟、提高可靠性 |
| 无法预知所有子任务 | 编排者-工人 | 动态适应任务需求 |
| 需要迭代打磨质量 | 评估者-优化者 | 系统化的质量提升循环 |
| 以上都不确定 | 从提示链开始 | 先简单后复杂 |

---

## 四、Google的多Agent架构与三种执行模式

Google Cloud Architecture团队在其Agent设计模式文档中，从更系统的角度总结了8种多Agent架构，基于三种基本执行模式的组合。

### 4.1 三种执行模式

```
顺序执行（Sequential）：
  Agent A → Agent B → Agent C
  适合：有依赖关系的步骤

循环执行（Loop / Iterative）：
  Agent A → Agent B → 评估 → 不满意 → Agent A → ...
  适合：需要反复改进的任务

并行执行（Parallel）：
  Agent A ─┐
  Agent B ──┼─→ 聚合
  Agent C ─┘
  适合：独立子任务、多角度验证
```

### 4.2 多Agent系统的微服务类比

Google将多Agent系统（MAS）类比为微服务架构，这个类比对有后端经验的开发者极有价值：

```
微服务架构           多Agent系统
─────────           ──────────
服务（Service）  ←→  Agent
API接口         ←→  Agent的工具定义和通信协议
服务发现         ←→  Agent注册和发现
负载均衡         ←→  任务分配
消息队列         ←→  Agent间消息传递
断路器           ←→  Agent失败处理和降级
监控告警         ←→  Agent行为可观测性
```

**核心启示：** 你在微服务架构中学到的所有经验——服务拆分粒度、接口设计、错误处理、可观测性——都直接适用于多Agent系统设计。不要把多Agent系统当成全新领域，它是你已有知识的延伸。

---

## 五、工具设计最佳实践——Agent系统的隐形支柱

Anthropic在《Writing Tools for Agents》中披露了一个反直觉的发现：在SWE-bench基准上，他们花在工具设计和优化上的时间，超过了花在主提示词上的时间。工具质量是Agent性能的决定性因素之一。

### 5.1 ACI = HCI

Anthropic提出了ACI（Agent-Computer Interface）的概念，类比HCI（Human-Computer Interface）：

> 你设计工具给Agent用，就像你设计UI给人用。同样需要考虑易用性、直觉性、错误处理。

**工具设计的核心原则：**

```
1. 名称即意图
   好：search_web(query)、create_file(path, content)
   差：do_action(type, params)、process(input)

2. 格式匹配自然文本
   LLM思考和生成都是自然语言。工具的输入输出格式
   越接近自然语言描述，LLM越容易正确使用。
   好："搜索最近7天关于AI Agent的新闻"
   差：{"timeRange": "7d", "category": "ai", "subcategory": "agent"}

3. 返回值包含足够上下文
   不只返回数据，还返回数据的含义和下一步建议。
   好："找到5篇相关文章。最相关的是[...]。建议进一步搜索[...]"
   差：[{"title": "...", "url": "..."}]

4. 错误信息要有行动指引
   好："文件不存在。可能的路径是：/src/、/lib/。请用list_directory确认"
   差："Error: FileNotFoundError"

5. 防止不可逆操作
   对删除、发送等不可逆操作，增加确认步骤或干运行模式。
```

### 5.2 工具设计模板

```python
# 好的工具定义示例
{
    "name": "search_codebase",
    "description": """在代码仓库中搜索匹配的代码片段。
    使用场景：当你需要了解某个函数/类的定义或用法时。
    注意：返回结果按相关度排序，最多返回10条。
    如果没有找到，尝试用不同的关键词或检查拼写。""",
    "parameters": {
        "query": {
            "type": "string",
            "description": "搜索关键词，如函数名、类名或代码片段"
        },
        "file_pattern": {
            "type": "string",
            "description": "文件名模式过滤，如 '*.py' 或 'src/**/*.ts'",
            "optional": True
        }
    }
}
```

关键要点：description不仅说明"是什么"，还说明"什么时候用"和"结果不理想怎么办"。

---

## 六、Agent通信协议——MCP、A2A与ACP

2025-2026年，Agent通信协议快速发展，三个主要协议各有定位。

### 6.1 MCP（Model Context Protocol）——Anthropic

**定位：** 模型与工具的标准化连接协议。

```
类比：USB接口标准
  以前：每个设备一个专用接口
  MCP之后：统一接口，即插即用

核心价值：
  - 一次实现工具，所有支持MCP的模型都能用
  - 标准化的工具描述、调用、结果返回格式
  - 内置认证、权限、错误处理

架构：
  LLM ←→ MCP Client ←→ MCP Server ←→ 外部工具/数据源
                            │
                            ├── 数据库
                            ├── API服务
                            ├── 文件系统
                            └── 第三方SaaS
```

### 6.2 A2A（Agent-to-Agent）——Google

**定位：** Agent与Agent之间的通信协议。MCP解决的是Agent与工具的连接，A2A解决的是Agent之间的协作。

```
类比：HTTP协议
  MCP = 让Agent能使用工具（就像浏览器能访问服务器）
  A2A = 让Agent能和Agent对话（就像服务器之间的API调用）

核心能力：
  - Agent发现：找到有特定能力的Agent
  - 任务委托：把子任务交给专业Agent
  - 状态同步：多Agent间共享执行状态
  - 流式通信：长任务的实时进度更新
```

### 6.3 ACP（Agent Communication Protocol）——IBM

**定位：** 企业级Agent治理协议，关注审计、合规、权限管控。

```
核心关注：
  - 谁授权这个Agent执行这个操作？
  - 操作的审计日志
  - Agent行为的合规性验证
  - 企业级的安全边界
```

### 协议选择指南

```
个人项目/小团队 → MCP足够（工具连接 + 简单Agent）
多Agent协作系统 → MCP + A2A（工具连接 + Agent间通信）
企业级生产环境 → MCP + A2A + ACP（加上治理和审计）
```

---

## 七、即用模板——三种常见Agent架构

### 模板1：ReAct Agent（最基础）

```python
# ReAct = Reasoning + Acting
# 最简单的Agent框架，适合大多数场景

SYSTEM_PROMPT = """你是一个任务执行Agent。
你有以下工具可用：
{tool_descriptions}

执行流程：
1. 思考（Thought）：分析当前状态，决定下一步
2. 行动（Action）：调用工具执行操作
3. 观察（Observation）：检查工具返回结果
4. 重复1-3直到任务完成
5. 最终回答（Final Answer）：给出最终结果

规则：
- 每次只执行一个动作
- 如果工具调用失败，分析原因并尝试替代方案
- 最多尝试10轮，超过后总结已有信息并告知用户
"""

# 执行循环
def run_agent(task, tools, max_iterations=10):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": task})

    for i in range(max_iterations):
        response = llm.call(messages, tools=tools)

        if response.has_tool_call:
            tool_result = execute_tool(response.tool_call)
            messages.append({"role": "tool", "content": tool_result})
        else:
            return response.content  # 最终回答

    return "达到最大迭代次数，任务未完成"
```

### 模板2：编排者-工人模式

```python
# 适合复杂任务的动态分解

ORCHESTRATOR_PROMPT = """你是任务编排者。
分析用户任务，将其分解为可执行的子任务。

输出格式：
{
  "subtasks": [
    {"id": 1, "description": "...", "worker_type": "researcher|coder|writer"},
    {"id": 2, "description": "...", "depends_on": [1]}
  ]
}

原则：
- 子任务粒度要适中，每个5-15分钟可完成
- 标注依赖关系，无依赖的可并行执行
- 每个子任务的描述要足够清晰，工人无需额外信息
"""

WORKER_PROMPTS = {
    "researcher": "你是信息研究员。根据任务描述搜索和整理信息...",
    "coder": "你是程序员。根据任务描述编写和测试代码...",
    "writer": "你是写作专家。根据任务描述撰写和润色文本..."
}

def run_orchestrated(task):
    # 1. 编排者分解任务
    plan = orchestrator.decompose(task)

    # 2. 按依赖关系执行（可并行无依赖任务）
    results = {}
    for subtask in topological_sort(plan.subtasks):
        context = gather_dependencies(subtask, results)
        worker = create_worker(subtask.worker_type)
        results[subtask.id] = worker.execute(subtask, context)

    # 3. 编排者综合结果
    return orchestrator.synthesize(task, results)
```

### 模板3：评估驱动迭代模式

```python
# 适合质量要求高的生成任务

GENERATOR_PROMPT = """根据任务要求生成输出。
如果收到改进反馈，在前一版基础上针对性修改。"""

EVALUATOR_PROMPT = """评估以下输出是否符合质量标准：
{criteria}

输出格式：
{
  "score": 1-10,
  "passed": true/false,
  "issues": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"]
}
"""

def run_eval_optimize(task, criteria, max_rounds=3):
    output = generator.generate(task)

    for round in range(max_rounds):
        evaluation = evaluator.evaluate(output, criteria)

        if evaluation.passed:
            return output

        # 带着评估反馈重新生成
        output = generator.improve(output, evaluation.suggestions)

    return output  # 达到最大轮数，返回最新版本
```

---

## 八、实际应用场景指南

### 8.1 客户支持

```
推荐架构：路由 + ReAct Agent
流程：
  用户消息 → 路由分类（技术/退款/咨询/投诉）
    → 专用Agent处理
      → 对话获取信息
      → 调用工具（查订单、查知识库、执行退款）
      → 生成回复
      → 用户确认或继续对话（循环）

关键设计：
  - 敏感操作（退款、修改订单）需人工确认
  - 设置最大对话轮次，超过转人工
  - 记录完整对话日志用于质量审查
```

### 8.2 代码开发

```
推荐架构：ReAct Agent + 评估者-优化者
流程：
  需求描述 → Agent分析需求
    → 编写代码 → 运行测试
    → 测试失败？→ 分析错误 → 修改代码 → 重新测试（循环）
    → 测试通过 → 代码审查Agent检查质量
    → 审查通过 → 提交

关键优势：代码任务天然适合Agent模式，因为：
  1. 有明确的验证方式（测试是否通过）
  2. 错误信息提供了精确的反馈
  3. 迭代修复是开发的自然过程
```

### 8.3 研究分析

```
推荐架构：编排者-工人 + 并行化
流程：
  研究问题 → 编排者分解为子问题
    → 多个研究Agent并行搜索不同来源
    → 每个Agent整理各自发现
    → 综合Agent交叉验证并整合
    → 生成研究报告

关键设计：
  - 多来源交叉验证减少幻觉
  - 要求每个发现标注来源
  - 综合阶段明确标注不同来源的一致性和冲突
```

### 8.4 内容生产

```
推荐架构：提示链 + 评估者-优化者
流程：
  选题 → 大纲生成 → 人工审核大纲
    → 逐节生成内容 → 质量评估Agent审查
    → 不达标则反馈修改（循环）
    → 全文整合 → 最终润色

关键设计：
  - 大纲阶段必须人工介入（方向性决策）
  - 内容生成可以并行（各节独立）
  - 评估标准要具体量化（不是"写得好"，而是"每节500-800字、包含至少1个具体案例"）
```

---

## 九、刻意练习方案

### 练习1：构建最小Agent（1小时）

```
目标：用任何语言实现一个最简单的ReAct Agent
要求：
  1. 给Agent 2-3个工具（如搜索、计算器、文件读写）
  2. 实现观察-思考-行动循环
  3. 设置最大迭代次数
  4. 处理工具调用失败的情况

验收标准：
  - Agent能完成"查找某个话题的最新信息并总结"的任务
  - Agent在工具失败时能自动尝试替代方案
  - 运行日志清晰展示每一步的思考和行动
```

### 练习2：工具设计比较实验（2小时）

```
目标：对同一个任务，设计"好工具"和"差工具"，对比Agent表现
步骤：
  1. 选一个任务（如"分析一个GitHub仓库的代码质量"）
  2. 设计V1工具：名称模糊、描述不清、错误信息不友好
  3. 设计V2工具：名称精确、描述详尽、错误信息有行动指引
  4. 用同一个Agent分别跑两组工具
  5. 对比：成功率、迭代次数、最终输出质量

预期发现：V2工具的Agent成功率显著更高，所需迭代次数更少。
```

### 练习3：从Workflow升级到Agent（3小时）

```
目标：将一个固定工作流逐步升级为自主Agent，观察每步的收益和代价
步骤：
  1. 先实现一个3步提示链（固定工作流）
  2. 加入条件路由（基于中间结果决定下一步）
  3. 加入反思循环（每步完成后自检，不满意则重做）
  4. 最终升级为完全自主Agent（LLM决定所有步骤）

记录每一步的：
  - 实现复杂度（代码量、调试时间）
  - 输出质量（人工评分1-10）
  - 可预测性（相同输入是否给出一致输出）
  - 运行成本（API调用次数、token消耗）
```

### 练习4：多Agent系统设计（半天）

```
目标：实现一个"编排者 + 2个工人"的多Agent系统
推荐任务：代码审查系统
  - 编排者：接收PR描述，分配审查任务
  - 安全审查Agent：检查安全漏洞
  - 质量审查Agent：检查代码质量和可维护性
  - 编排者综合两个审查结果

挑战练习：
  - 让两个Agent的审查结果能相互参考
  - 处理Agent之间意见冲突的情况
  - 实现"不确定"时升级到人工审查的机制
```

---

## 十、反模式——这样做会失败

### 反模式1：过早引入Agent

**症状：** 直接上多Agent系统解决一个提示链就能搞定的问题。

**后果：** 调试困难、延迟高、成本高、结果不稳定。单次LLM调用3秒能搞定的事，多Agent系统可能要30秒且结果反而更差。

**正确做法：** 严格遵循复杂度阶梯。先用最简单的方案，只在明确失败时升级。Anthropic原文："很多应用优化单次LLM调用就够了。"

### 反模式2：工具设计粗糙

**症状：** 工具名称模糊（如`do_stuff`）、描述不清、错误信息是原始异常栈。

**后果：** Agent频繁调用错误的工具、传入错误的参数、无法从错误中恢复。Anthropic在SWE-bench上的经验：工具设计质量直接决定Agent成功率。

**正确做法：** 把工具设计当作给同事写API文档。名称自解释、描述包含使用场景和注意事项、错误信息包含修复建议。

### 反模式3：无限循环无防护

**症状：** Agent循环没有最大迭代次数、没有超时、没有成本上限。

**后果：** Agent陷入死循环，消耗大量token和时间。生产环境中可能导致巨额账单。

**正确做法：** 三重防护——最大迭代次数（如10次）、最大运行时间（如5分钟）、最大token消耗（如50K tokens）。任何一个触发就优雅终止并返回中间结果。

### 反模式4：状态管理混乱

**症状：** Agent的历史对话无节制增长，或者关键上下文在传递中丢失。

**后果：** 上下文窗口溢出导致早期信息被截断，或模型因上下文过长而注意力稀释，质量下降。

**正确做法：** 主动管理Agent的上下文。定期压缩历史（保留摘要而非原文）、使用结构化状态而非纯文本传递、关键信息在每轮显式注入。

### 反模式5：缺乏可观测性

**症状：** Agent是黑盒——出了问题不知道哪一步出错、哪个工具返回了异常、LLM做了什么判断。

**后果：** 无法调试、无法改进、无法在生产环境中监控。

**正确做法：** 每一步记录：LLM的思考过程、选择的工具、工具的输入输出、花费的时间和token。使用Langfuse、LangSmith等可观测性工具。日志不是可选项，是必需品。

### 反模式6：让Agent做所有决策

**症状：** 完全信任Agent的判断，包括涉及金钱、安全、不可逆操作的决策。

**后果：** Agent幻觉或判断失误导致真实损失。删除了不该删的文件、发送了不该发的邮件、执行了不该执行的数据库操作。

**正确做法：** 对不可逆操作设置人工确认门控。Anthropic的建议：高风险操作永远需要人类批准。Agent可以建议，但不应独立执行关键决策。

---

## 十一、专家怎么说

### Anthropic（《Building Effective Agents》）

> "The most successful implementations we've seen weren't the most complex — they were the ones that matched the right level of complexity to the problem."
> （我们见过的最成功的实现，不是最复杂的——而是那些为问题匹配了恰当复杂度的。）

这是Anthropic反复强调的核心信条。不是技术越先进越好，而是匹配度越高越好。

### Andrew Ng

> "The ability to drive rigorous eval and error analysis is the single strongest predictor of whether someone will succeed with agent systems."
> （驱动严格的eval和error analysis的能力，是预测一个人能否做好Agent系统的最强单一指标。）

Ng与众多团队合作后的结论：区分Agent系统高手和新手的，不是架构设计能力，而是评估和迭代能力。

### Andrej Karpathy

> "Software 3.0 is English. The code is the prompt, the spec is the prompt, the test is whether the LLM does what you wanted."
> （Software 3.0是英语。代码是提示词，规格说明是提示词，测试是看LLM是否做了你要的事。）

Karpathy指出Agent系统的代码很大程度上就是提示词和工具定义。编写这些"代码"需要的不是传统编程技能，而是清晰的思维和精确的表达。

### Google Cloud Architecture Team

> "Agents can be treated as individual 'microservices', where each agent can be independently developed, tested, and deployed."
> （Agent可以被视为独立的"微服务"，每个Agent可以独立开发、测试和部署。）

Google把多Agent系统设计回归到了软件工程师熟悉的领域。你不需要学习全新的设计范式——微服务架构的所有原则（单一职责、接口清晰、独立部署、故障隔离）都直接适用。

### Gartner预测

> "到2026年，40%的企业应用将嵌入AI Agent。"

这不是遥远的未来，而是正在发生的现实。Agent从概念到生产的转化速度，远超过去任何AI技术。

### Anthropic的开发者使用数据

> "开发者在约60%的工作中使用AI，但报告说只有0-20%的任务能完全委托。"

这个数据揭示了Agent系统的真实边界：AI是强大的协作者，但不是无限能力的替代品。最好的Agent系统设计，是让AI做它擅长的（执行、搜索、生成），人做人擅长的（判断、品味、决策）。

---

## 十二、框架选型参考

当前主流Agent开发框架的定位和适用场景：

| 框架 | 定位 | 适合 | 学习曲线 |
|------|------|------|---------|
| **LangGraph** | 图结构工作流引擎 | 复杂多步骤流程、需要精细状态管理 | 中等 |
| **CrewAI** | 多Agent协作框架 | 多角色协作、团队模拟 | 低 |
| **Google ADK** | Google生态Agent开发 | Gemini模型、Google Cloud集成 | 中等 |
| **Claude Agent SDK** | Anthropic原生Agent | Claude模型、MCP集成 | 低 |
| **OpenAI Agents SDK** | OpenAI原生Agent | GPT模型、OpenAI生态 | 低 |
| **自定义实现** | 完全控制 | 特殊需求、极致优化 | 高 |

**选型建议：** 如果你刚开始，用Claude Agent SDK或OpenAI Agents SDK——官方SDK最简单、文档最好、维护最可靠。需要复杂工作流时升级到LangGraph。多Agent协作场景考虑CrewAI。不确定就自己写——一个ReAct循环只需要50行代码。

---

## 参考来源

### 核心文档
- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — Agent定义、Workflow vs Agent区分、五种工作流模式
- [Anthropic: Writing Tools for Agents](https://www.anthropic.com/engineering/writing-tools-for-agents) — ACI概念、工具设计最佳实践
- [Google Cloud: Choose AI Agent Design Patterns](https://cloud.google.com/discover/what-is-ai-agent-architecture) — 8种多Agent架构、三种执行模式

### 设计模式与方法论
- [Andrew Ng: Agentic AI Design Patterns (DeepLearning.AI)](https://www.deeplearning.ai/courses/agentic-ai/) — 四大设计模式、GPT-3.5到95%的实验数据
- [Andrew Ng: AI Agentic Workflows (Sequoia Talk)](https://www.youtube.com/watch?v=sal78ACtGTc) — 反思、工具使用、规划、多Agent协作
- [Google: Multi-Agent Design Patterns (InfoQ)](https://www.infoq.com/news/2026/01/multi-agent-design-patterns/) — 顺序/循环/并行执行模式

### 通信协议
- [Anthropic: Model Context Protocol (MCP)](https://modelcontextprotocol.io/) — MCP规范与实现
- [Google: Agent-to-Agent Protocol (A2A)](https://developers.google.com/a2a) — A2A协议规范
- [IBM: Agent Communication Protocol (ACP)](https://github.com/ibm/agent-communication-protocol) — 企业级Agent治理

### 框架与工具
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) — 图结构Agent框架
- [CrewAI Documentation](https://docs.crewai.com/) — 多Agent协作框架
- [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) — Google Agent开发框架
- [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents/claude-agent-sdk) — Anthropic原生Agent SDK

### 行业数据与预测
- [Anthropic: 2026 Agentic Coding Trends Report](https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf) — 开发者60%工作用AI，0-20%可完全委托
- [Gartner: AI Agent Predictions 2026](https://www.gartner.com/en/topics/ai-agents) — 40%企业应用将嵌入AI Agent

*最后更新：2026-03-14*
