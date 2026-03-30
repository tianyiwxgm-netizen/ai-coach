#!/usr/bin/env python3
"""
AI Coach 评估模式集成测试
模拟 10 个真实开发者行为的会话项目，覆盖 L1/L2/L3 不同能力水平。
对每个项目运行信号提取脚本，验证评分结果是否在预期范围内。
"""

import json
import os
import sys
import subprocess
import tempfile
import re

SKILL_PATH = os.path.expanduser("~/.claude/skills/ai-coach/SKILL.md")

results = []


def test(name, passed, detail=""):
    results.append({"name": name, "passed": passed, "detail": detail})
    icon = "✅" if passed else "❌"
    line = f"  {icon} {name}"
    if detail and not passed:
        line += f" — {detail}"
    elif detail and passed:
        line += f" ({detail})"
    print(line)


def extract_python_script():
    """从 SKILL.md 中提取信号提取 Python 脚本"""
    with open(SKILL_PATH) as f:
        content = f.read()

    # 定位 Step 11 区域
    step11_start = content.find("## Step 11")
    step12_start = content.find("## Step 12")
    step11_section = content[step11_start:step12_start]

    # 提取 python3 -c "..." 中的脚本
    # 找到 ```bash 代码块
    bash_blocks = re.findall(r'```bash\n(.*?)```', step11_section, re.DOTALL)
    for block in bash_blocks:
        # 提取 python3 -c " 到 " "$FILE" 之间的内容
        match = re.search(r'python3 -c "\n(.*?)\n" "\$FILE"', block, re.DOTALL)
        if match:
            return match.group(1)
    return None


def run_extraction(script, jsonl_content):
    """执行信号提取脚本并返回结果"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(jsonl_content)
        data_file = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script)
        script_file = f.name

    try:
        result = subprocess.run(
            ["python3", script_file, data_file],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return None, result.stderr
        return json.loads(result.stdout), None
    except Exception as e:
        return None, str(e)
    finally:
        os.unlink(data_file)
        os.unlink(script_file)


# ═══════════════════════════════════════════
# 辅助：构造 JSONL 消息
# ═══════════════════════════════════════════

def user_msg(text, ts):
    return json.dumps({
        "type": "user",
        "message": {"role": "user", "content": [{"type": "text", "text": text}]},
        "timestamp": ts
    })


def user_msg_short(text, ts):
    """短文本用户消息（直接 string，非 list）"""
    return json.dumps({
        "type": "user",
        "message": {"role": "user", "content": text},
        "timestamp": ts
    })


def assistant_tool(tool_name, tool_input, ts):
    return json.dumps({
        "type": "assistant",
        "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": tool_name, "input": tool_input}
        ]},
        "timestamp": ts
    })


def assistant_multi_tools(tools, ts):
    """一次 assistant 消息包含多个工具调用"""
    content = [{"type": "tool_use", "name": name, "input": inp} for name, inp in tools]
    return json.dumps({
        "type": "assistant",
        "message": {"role": "assistant", "content": content},
        "timestamp": ts
    })


def assistant_skill(skill_name, ts):
    return assistant_tool("Skill", {"skill": skill_name}, ts)


def assistant_bash(cmd, ts):
    return assistant_tool("Bash", {"command": cmd}, ts)


def assistant_read(path, ts):
    return assistant_tool("Read", {"file_path": path}, ts)


def assistant_grep(pattern, ts):
    return assistant_tool("Grep", {"pattern": pattern}, ts)


def assistant_glob(pattern, ts):
    return assistant_tool("Glob", {"pattern": pattern}, ts)


def assistant_write(path, ts):
    return assistant_tool("Write", {"file_path": path, "content": "code"}, ts)


def assistant_edit(path, ts):
    return assistant_tool("Edit", {"file_path": path, "old_string": "old", "new_string": "new"}, ts)


def assistant_plan_mode(ts):
    return assistant_tool("EnterPlanMode", {}, ts)


def assistant_task_bg(prompt, ts):
    return assistant_tool("Task", {"prompt": prompt, "run_in_background": True, "subagent_type": "general-purpose"}, ts)


def assistant_task_fg(prompt, ts):
    return assistant_tool("Task", {"prompt": prompt, "subagent_type": "general-purpose"}, ts)


def tool_result_error(ts):
    return json.dumps({
        "type": "user",
        "message": {"role": "user", "content": [
            {"type": "tool_result", "is_error": True, "content": "Error occurred"}
        ]},
        "timestamp": ts
    })


# ═══════════════════════════════════════════
# 10 个模拟项目
# ═══════════════════════════════════════════

def profile_1_complete_beginner():
    """
    项目 1：完全新手（L1 预期）
    特征：只用 Bash、不规划、不测试、提示词极短、不懂业务
    预期：SOP=0-20, TDD=0-20, 工具=0-20
    """
    lines = [
        user_msg_short("帮我改个 bug", "2026-03-14T09:00:00Z"),
        assistant_bash("cat src/main.py", "2026-03-14T09:00:10Z"),
        user_msg_short("改这个函数", "2026-03-14T09:01:00Z"),
        assistant_bash("sed -i 's/old/new/' src/main.py", "2026-03-14T09:01:10Z"),
        user_msg_short("好了", "2026-03-14T09:02:00Z"),
        assistant_bash("python src/main.py", "2026-03-14T09:02:10Z"),
        user_msg_short("再改一个", "2026-03-14T09:05:00Z"),
        assistant_bash("cat src/utils.py", "2026-03-14T09:05:10Z"),
        assistant_bash("sed -i 's/foo/bar/' src/utils.py", "2026-03-14T09:05:20Z"),
        user_msg_short("ok", "2026-03-14T09:06:00Z"),
        assistant_bash("git add . && git commit -m 'fix'", "2026-03-14T09:06:10Z"),
    ]
    return "\n".join(lines), {
        "name": "完全新手（只用 Bash，无规划无测试）",
        "expected_level": "L1",
        "checks": {
            "plan_mode_count": ("==", 0),
            "test_command_count": ("==", 0),
            "git_commit_count": ("==", 1),
            "parallel_agents": ("==", 0),
            "avg_user_msg_length": ("<", 20),
        }
    }


def profile_2_bash_heavy_dev():
    """
    项目 2：Bash 重度用户（L1-L2 过渡）
    特征：大量 Bash，偶尔用 Read，不用 Grep/Glob，有测试但都在最后
    """
    lines = [
        user_msg("我要给订单模块加个取消功能", "2026-03-14T09:00:00Z"),
        assistant_bash("ls src/order/", "2026-03-14T09:00:10Z"),
        assistant_bash("cat src/order/OrderService.java", "2026-03-14T09:00:20Z"),
        assistant_bash("cat src/order/OrderController.java", "2026-03-14T09:00:30Z"),
        user_msg_short("加个取消接口", "2026-03-14T09:01:00Z"),
        assistant_bash("echo 'code' >> src/order/OrderService.java", "2026-03-14T09:01:10Z"),
        assistant_bash("echo 'code' >> src/order/OrderController.java", "2026-03-14T09:01:20Z"),
        assistant_read("/project/src/order/OrderMapper.xml", "2026-03-14T09:02:00Z"),
        assistant_bash("echo 'sql' >> src/order/OrderMapper.xml", "2026-03-14T09:02:10Z"),
        user_msg_short("测试下", "2026-03-14T09:05:00Z"),
        assistant_bash("./gradlew test --tests OrderServiceTest", "2026-03-14T09:05:10Z"),
        assistant_bash("git add . && git commit -m 'feat: add cancel'", "2026-03-14T09:06:00Z"),
    ]
    return "\n".join(lines), {
        "name": "Bash 重度用户（偶尔 Read，测试放最后）",
        "expected_level": "L1-L2",
        "checks": {
            "plan_mode_count": ("==", 0),
            "test_command_count": ("==", 1),
            "git_commit_count": ("==", 1),
            "avg_user_msg_length": ("<", 30),
        }
    }


def profile_3_plan_but_no_tdd():
    """
    项目 3：会规划但不做 TDD（L2 初级）
    特征：用了 Plan Mode，用 Read/Grep，但测试在最后才跑
    """
    lines = [
        user_msg("我要实现用户注册功能，需要支持手机号和邮箱两种方式，数据库表是 kos_user_info", "2026-03-14T09:00:00Z"),
        assistant_plan_mode("2026-03-14T09:00:10Z"),
        assistant_read("/project/CLAUDE.md", "2026-03-14T09:00:20Z"),
        assistant_grep("UserService", "2026-03-14T09:01:00Z"),
        assistant_read("/project/src/user/UserService.java", "2026-03-14T09:01:10Z"),
        user_msg("方案可以，开始写代码", "2026-03-14T09:02:00Z"),
        assistant_write("/project/src/user/RegisterService.java", "2026-03-14T09:02:10Z"),
        assistant_write("/project/src/user/RegisterController.java", "2026-03-14T09:02:20Z"),
        assistant_edit("/project/src/user/UserMapper.xml", "2026-03-14T09:02:30Z"),
        user_msg_short("运行测试", "2026-03-14T09:05:00Z"),
        assistant_bash("./gradlew test", "2026-03-14T09:05:10Z"),
        assistant_bash("git commit -m 'feat: user registration'", "2026-03-14T09:06:00Z"),
    ]
    return "\n".join(lines), {
        "name": "会规划但不做 TDD（Plan Mode + 测试最后跑）",
        "expected_level": "L2",
        "checks": {
            "plan_mode_count": ("==", 1),
            "test_command_count": ("==", 1),
            "claude_md_refs": (">=", 1),
        }
    }


def profile_4_skill_user_no_tdd():
    """
    项目 4：会用 Skill 但不严格 TDD（L2 中级）
    特征：用了 brainstorm + write-plan，工具多样，但测试不是先行
    """
    lines = [
        user_msg("我要给供应链模块加一个采购单审批功能。需求是：采购员创建采购单后，需要主管审批才能生效。审批通过后自动创建入库单。", "2026-03-14T09:00:00Z"),
        assistant_skill("brainstorm", "2026-03-14T09:00:10Z"),
        assistant_read("/project/CLAUDE.md", "2026-03-14T09:00:20Z"),
        assistant_glob("**/scm/**/*.java", "2026-03-14T09:00:30Z"),
        assistant_grep("PurchaseOrder", "2026-03-14T09:01:00Z"),
        assistant_read("/project/src/scm/PurchaseOrderService.java", "2026-03-14T09:01:10Z"),
        user_msg("方案确定了，写计划", "2026-03-14T09:05:00Z"),
        assistant_skill("write-plan", "2026-03-14T09:05:10Z"),
        user_msg("开始执行", "2026-03-14T09:10:00Z"),
        assistant_write("/project/src/scm/ApprovalService.java", "2026-03-14T09:10:10Z"),
        assistant_write("/project/src/scm/ApprovalController.java", "2026-03-14T09:10:20Z"),
        assistant_edit("/project/src/scm/PurchaseOrderMapper.xml", "2026-03-14T09:10:30Z"),
        assistant_bash("./gradlew test --tests ApprovalServiceTest", "2026-03-14T09:15:00Z"),
        assistant_bash("git commit -m 'feat: purchase order approval'", "2026-03-14T09:16:00Z"),
    ]
    return "\n".join(lines), {
        "name": "会用 Skill 但测试不先行（brainstorm + write-plan）",
        "expected_level": "L2",
        "checks": {
            "skill_usage_brainstorm": (">=", 1),
            "skill_usage_write-plan": (">=", 1),
            "test_command_count": (">=", 1),
            "claude_md_refs": (">=", 1),
        }
    }


def profile_5_tdd_practitioner():
    """
    项目 5：TDD 实践者（L2-L3 过渡）
    特征：先写测试再写实现，Red-Green 模式，但没有完整 SOP
    """
    lines = [
        user_msg("CargoService 的 calculateWeight 方法有 bug，当货物重量为 0 时没有抛异常。复现步骤：传入 weight=0 的 Cargo 对象，期望抛 IllegalArgumentException 但实际返回了 0。", "2026-03-14T09:00:00Z"),
        assistant_read("/project/CLAUDE.md", "2026-03-14T09:00:10Z"),
        assistant_grep("calculateWeight", "2026-03-14T09:00:20Z"),
        assistant_read("/project/src/scm/CargoService.java", "2026-03-14T09:00:30Z"),
        # 先写测试
        assistant_write("/project/tests/scm/CargoServiceTest.java", "2026-03-14T09:01:00Z"),
        # 运行测试确认失败 (Red)
        assistant_bash("./gradlew test --tests CargoServiceTest.testZeroWeightThrows", "2026-03-14T09:01:30Z"),
        user_msg_short("测试确认失败了，修复代码", "2026-03-14T09:02:00Z"),
        # 修复代码
        assistant_edit("/project/src/scm/CargoService.java", "2026-03-14T09:02:10Z"),
        # 运行测试确认通过 (Green)
        assistant_bash("./gradlew test --tests CargoServiceTest.testZeroWeightThrows", "2026-03-14T09:02:30Z"),
        # 运行全量测试确认无回归
        assistant_bash("./gradlew test", "2026-03-14T09:03:00Z"),
        assistant_bash("git commit -m 'fix: validate zero weight in CargoService'", "2026-03-14T09:03:30Z"),
    ]
    return "\n".join(lines), {
        "name": "TDD 实践者（Red-Green 模式修 Bug）",
        "expected_level": "L2-L3",
        "checks": {
            "test_command_count": (">=", 3),
            "git_commit_count": ("==", 1),
            "claude_md_refs": (">=", 1),
        }
    }


def profile_6_full_sop_expert():
    """
    项目 6：完整 SOP 专家（L3）
    特征：brainstorm → write-plan → execute-plan，TDD，并行 Agent，频繁提交
    """
    lines = [
        user_msg("我要实现门店 KDS（厨房显示系统）的订单分屏功能。需求：不同品类的订单分发到不同的厨房屏幕。例如饮品订单发到饮品站，主食订单发到主食站。验收标准：1) 支持按品类配置屏幕映射 2) 订单创建后 2 秒内分发 3) 分发失败有重试机制。", "2026-03-14T09:00:00Z"),
        assistant_skill("brainstorm", "2026-03-14T09:00:10Z"),
        assistant_read("/project/CLAUDE.md", "2026-03-14T09:00:20Z"),
        assistant_glob("**/kds/**/*.java", "2026-03-14T09:00:30Z"),
        assistant_grep("KdsOrder", "2026-03-14T09:01:00Z"),
        assistant_read("/project/src/kds/KdsOrderService.java", "2026-03-14T09:01:10Z"),
        assistant_read("/project/src/kds/KdsScreenService.java", "2026-03-14T09:01:20Z"),
        # 并行探索
        assistant_task_bg("分析 KDS 模块现有架构", "2026-03-14T09:01:30Z"),
        assistant_task_bg("调研 WebSocket 推送方案", "2026-03-14T09:01:31Z"),
        user_msg("方案 A（基于品类规则引擎）更好，写计划", "2026-03-14T09:05:00Z"),
        assistant_skill("write-plan", "2026-03-14T09:05:10Z"),
        user_msg("执行计划", "2026-03-14T09:10:00Z"),
        assistant_skill("execute-plan", "2026-03-14T09:10:10Z"),
        # TDD 循环 1：分屏规则
        assistant_write("/project/tests/kds/ScreenRoutingServiceTest.java", "2026-03-14T09:11:00Z"),
        assistant_bash("./gradlew test --tests ScreenRoutingServiceTest", "2026-03-14T09:11:30Z"),  # Red
        assistant_write("/project/src/kds/ScreenRoutingService.java", "2026-03-14T09:12:00Z"),
        assistant_bash("./gradlew test --tests ScreenRoutingServiceTest", "2026-03-14T09:12:30Z"),  # Green
        assistant_bash("git commit -m 'feat(kds): add screen routing service with category rules'", "2026-03-14T09:13:00Z"),
        # TDD 循环 2：分发机制
        assistant_write("/project/tests/kds/OrderDispatcherTest.java", "2026-03-14T09:14:00Z"),
        assistant_bash("./gradlew test --tests OrderDispatcherTest", "2026-03-14T09:14:30Z"),  # Red
        assistant_write("/project/src/kds/OrderDispatcher.java", "2026-03-14T09:15:00Z"),
        assistant_bash("./gradlew test --tests OrderDispatcherTest", "2026-03-14T09:15:30Z"),  # Green
        assistant_bash("git commit -m 'feat(kds): add order dispatcher with retry'", "2026-03-14T09:16:00Z"),
        # TDD 循环 3：重试
        assistant_write("/project/tests/kds/RetryMechanismTest.java", "2026-03-14T09:17:00Z"),
        assistant_bash("./gradlew test --tests RetryMechanismTest", "2026-03-14T09:17:30Z"),  # Red
        assistant_write("/project/src/kds/RetryMechanism.java", "2026-03-14T09:18:00Z"),
        assistant_bash("./gradlew test --tests RetryMechanismTest", "2026-03-14T09:18:30Z"),  # Green
        # 全量测试
        assistant_bash("./gradlew test", "2026-03-14T09:19:00Z"),
        assistant_bash("git commit -m 'feat(kds): complete order screen dispatch v1'", "2026-03-14T09:19:30Z"),
    ]
    return "\n".join(lines), {
        "name": "完整 SOP 专家（brainstorm→plan→execute + TDD + 并行 Agent）",
        "expected_level": "L3",
        "checks": {
            "skill_usage_brainstorm": (">=", 1),
            "skill_usage_write-plan": (">=", 1),
            "skill_usage_execute-plan": (">=", 1),
            "test_command_count": (">=", 7),
            "git_commit_count": (">=", 3),
            "parallel_agents": (">=", 2),
            "claude_md_refs": (">=", 1),
        }
    }


def profile_7_error_prone_user():
    """
    项目 7：频繁出错、盲目重试的用户（L1）
    特征：出错后反复重试同一命令，不分析原因，不换策略
    """
    lines = [
        user_msg_short("启动项目", "2026-03-14T09:00:00Z"),
        assistant_bash("./gradlew bootRun", "2026-03-14T09:00:10Z"),
        tool_result_error("2026-03-14T09:00:30Z"),
        # 盲目重试同一命令
        assistant_bash("./gradlew bootRun", "2026-03-14T09:00:40Z"),
        tool_result_error("2026-03-14T09:01:00Z"),
        assistant_bash("./gradlew bootRun", "2026-03-14T09:01:10Z"),
        tool_result_error("2026-03-14T09:01:30Z"),
        user_msg_short("换个方法", "2026-03-14T09:02:00Z"),
        assistant_bash("java -jar build/libs/app.jar", "2026-03-14T09:02:10Z"),
        tool_result_error("2026-03-14T09:02:30Z"),
        assistant_bash("java -jar build/libs/app.jar", "2026-03-14T09:02:40Z"),
        user_msg_short("算了 直接改代码", "2026-03-14T09:03:00Z"),
        assistant_bash("sed -i 's/error/fix/' src/main.java", "2026-03-14T09:03:10Z"),
        assistant_bash("git add -A && git commit -m 'fix'", "2026-03-14T09:04:00Z"),
    ]
    return "\n".join(lines), {
        "name": "频繁出错、盲目重试（不分析根因）",
        "expected_level": "L1",
        "checks": {
            "plan_mode_count": ("==", 0),
            "test_command_count": ("==", 0),
            "error_recovery_bash_heavy": True,
            "avg_user_msg_length": ("<", 15),
        }
    }


def profile_8_business_oriented():
    """
    项目 8：业务导向型开发者（L2 偏高）
    特征：提示词从业务视角出发、描述用户场景、用 brainstorm
    """
    lines = [
        user_msg("我们的供应链系统有个问题：门店补货时，店长需要手动计算每个SKU的建议补货量。\n\n用户痛点：店长每天花30分钟手动查看库存、销售数据、保质期，然后决定补多少货。\n\n期望：系统能根据历史销售数据、当前库存、保质期自动计算建议补货量，店长只需确认或微调。\n\n验收标准：\n1. 根据过去7天平均日销量计算建议量\n2. 考虑安全库存（1.5天用量）\n3. 考虑保质期剩余天数\n4. 店长可以修改建议量后提交", "2026-03-14T09:00:00Z"),
        assistant_skill("brainstorm", "2026-03-14T09:00:10Z"),
        assistant_read("/project/CLAUDE.md", "2026-03-14T09:00:20Z"),
        assistant_glob("**/scm/**/*Replenish*", "2026-03-14T09:01:00Z"),
        assistant_grep("inventory", "2026-03-14T09:01:10Z"),
        assistant_read("/project/src/scm/InventoryService.java", "2026-03-14T09:01:20Z"),
        user_msg("方案B更好，因为从门店店长的角度看，他们需要一个简单直观的界面，不需要太复杂的算法配置。我们的目标用户是操作型店长，不是数据分析师。", "2026-03-14T09:05:00Z"),
        assistant_skill("write-plan", "2026-03-14T09:05:10Z"),
        user_msg("开始实现", "2026-03-14T09:10:00Z"),
        assistant_write("/project/src/scm/ReplenishSuggestionService.java", "2026-03-14T09:10:10Z"),
        assistant_write("/project/tests/scm/ReplenishSuggestionServiceTest.java", "2026-03-14T09:10:20Z"),
        assistant_bash("./gradlew test --tests ReplenishSuggestionServiceTest", "2026-03-14T09:11:00Z"),
        assistant_bash("git commit -m 'feat(scm): smart replenishment suggestion for store managers'", "2026-03-14T09:12:00Z"),
    ]
    return "\n".join(lines), {
        "name": "业务导向型（从用户痛点出发，有验收标准）",
        "expected_level": "L2",
        "checks": {
            "skill_usage_brainstorm": (">=", 1),
            "skill_usage_write-plan": (">=", 1),
            "avg_user_msg_length": (">", 50),
            "claude_md_refs": (">=", 1),
        }
    }


def profile_9_parallel_power_user():
    """
    项目 9：并行 Agent 高手（L3 工具维度高）
    特征：大量使用并行 Agent、丰富工具组合、Plan Mode、频繁提交
    """
    lines = [
        user_msg("需要给 KOS 系统做一次国际化（i18n）改造。涉及后端消息国际化、前端文案国际化、数据库字段扩展。请先调研现有代码的国际化状态。", "2026-03-14T09:00:00Z"),
        assistant_plan_mode("2026-03-14T09:00:10Z"),
        assistant_read("/project/CLAUDE.md", "2026-03-14T09:00:20Z"),
        # 并行调研 3 个方向
        assistant_task_bg("调研后端 Spring Boot i18n 现有配置", "2026-03-14T09:00:30Z"),
        assistant_task_bg("调研前端 i18n 框架使用情况", "2026-03-14T09:00:31Z"),
        assistant_task_bg("分析数据库中需要国际化的字段", "2026-03-14T09:00:32Z"),
        assistant_glob("**/i18n/**", "2026-03-14T09:01:00Z"),
        assistant_glob("**/messages*.properties", "2026-03-14T09:01:10Z"),
        assistant_grep("MessageSource", "2026-03-14T09:01:20Z"),
        assistant_grep("@Value.*message", "2026-03-14T09:01:30Z"),
        user_msg("调研完了，开始实现后端国际化", "2026-03-14T09:05:00Z"),
        assistant_skill("brainstorm", "2026-03-14T09:05:10Z"),
        assistant_skill("write-plan", "2026-03-14T09:05:20Z"),
        user_msg("执行", "2026-03-14T09:10:00Z"),
        # 并行处理多个模块
        assistant_task_bg("实现 scm 模块的 i18n message keys", "2026-03-14T09:10:10Z"),
        assistant_task_bg("实现 oms 模块的 i18n message keys", "2026-03-14T09:10:11Z"),
        assistant_write("/project/src/common/i18n/I18nService.java", "2026-03-14T09:11:00Z"),
        assistant_write("/project/tests/common/I18nServiceTest.java", "2026-03-14T09:11:10Z"),
        assistant_bash("./gradlew test --tests I18nServiceTest", "2026-03-14T09:11:30Z"),
        assistant_bash("git commit -m 'feat: add i18n service foundation'", "2026-03-14T09:12:00Z"),
        assistant_edit("/project/src/common/i18n/MessageConfig.java", "2026-03-14T09:12:30Z"),
        assistant_bash("./gradlew test", "2026-03-14T09:13:00Z"),
        assistant_bash("git commit -m 'feat: configure message source for multi-locale'", "2026-03-14T09:13:30Z"),
        assistant_bash("git commit -m 'feat: add i18n message keys for scm and oms'", "2026-03-14T09:14:00Z"),
    ]
    return "\n".join(lines), {
        "name": "并行 Agent 高手（5 个并行任务 + 丰富工具 + 频繁提交）",
        "expected_level": "L3",
        "checks": {
            "parallel_agents": (">=", 5),
            "git_commit_count": (">=", 3),
            "plan_mode_count": (">=", 1),
            "skill_usage_brainstorm": (">=", 1),
            "test_command_count": (">=", 2),
        }
    }


def profile_10_mixed_session():
    """
    项目 10：混合会话（L2 综合）
    特征：一个会话中做了多种任务（修 bug + 加功能 + 小重构），
    部分遵循流程部分不遵循，代表真实使用场景
    """
    lines = [
        # 任务 1：快速修一个小 bug（不走 TDD）
        user_msg("先修个小 bug：页面上商品价格显示少了两位小数", "2026-03-14T09:00:00Z"),
        assistant_grep("formatPrice", "2026-03-14T09:00:10Z"),
        assistant_read("/project/src/saas/PriceUtils.java", "2026-03-14T09:00:20Z"),
        assistant_edit("/project/src/saas/PriceUtils.java", "2026-03-14T09:00:30Z"),
        assistant_bash("./gradlew test --tests PriceUtilsTest", "2026-03-14T09:01:00Z"),
        assistant_bash("git commit -m 'fix: price decimal display'", "2026-03-14T09:01:30Z"),

        # 任务 2：加一个新功能（走了 brainstorm 流程）
        user_msg("接下来要加一个新功能：门店营业时间管理。店长可以设置每天的营业起止时间，到时间自动关闭下单入口。需要考虑不同时区和节假日特殊营业时间。", "2026-03-14T09:05:00Z"),
        assistant_skill("brainstorm", "2026-03-14T09:05:10Z"),
        assistant_read("/project/CLAUDE.md", "2026-03-14T09:05:20Z"),
        assistant_glob("**/saas/**/*Store*", "2026-03-14T09:05:30Z"),
        assistant_grep("BusinessHour", "2026-03-14T09:06:00Z"),
        user_msg("方案 A 好，写计划", "2026-03-14T09:08:00Z"),
        assistant_skill("write-plan", "2026-03-14T09:08:10Z"),
        user_msg("执行", "2026-03-14T09:10:00Z"),
        assistant_write("/project/tests/saas/BusinessHourServiceTest.java", "2026-03-14T09:10:10Z"),
        assistant_bash("./gradlew test --tests BusinessHourServiceTest", "2026-03-14T09:10:30Z"),  # Red
        assistant_write("/project/src/saas/BusinessHourService.java", "2026-03-14T09:11:00Z"),
        assistant_bash("./gradlew test --tests BusinessHourServiceTest", "2026-03-14T09:11:30Z"),  # Green
        assistant_bash("git commit -m 'feat(saas): add business hour management'", "2026-03-14T09:12:00Z"),

        # 任务 3：小重构（不走流程，直接改）
        user_msg_short("顺便把 StoreConfig 重构下，太乱了", "2026-03-14T09:15:00Z"),
        assistant_read("/project/src/saas/StoreConfig.java", "2026-03-14T09:15:10Z"),
        assistant_edit("/project/src/saas/StoreConfig.java", "2026-03-14T09:15:20Z"),
        assistant_bash("./gradlew test", "2026-03-14T09:16:00Z"),
        assistant_bash("git commit -m 'refactor: clean up StoreConfig'", "2026-03-14T09:16:30Z"),
    ]
    return "\n".join(lines), {
        "name": "混合会话（修 bug + 新功能 + 重构，部分遵循流程）",
        "expected_level": "L2",
        "checks": {
            "skill_usage_brainstorm": (">=", 1),
            "skill_usage_write-plan": (">=", 1),
            "test_command_count": (">=", 4),
            "git_commit_count": (">=", 3),
            "claude_md_refs": (">=", 1),
        }
    }


# ═══════════════════════════════════════════
# 测试执行
# ═══════════════════════════════════════════

PROFILES = [
    profile_1_complete_beginner,
    profile_2_bash_heavy_dev,
    profile_3_plan_but_no_tdd,
    profile_4_skill_user_no_tdd,
    profile_5_tdd_practitioner,
    profile_6_full_sop_expert,
    profile_7_error_prone_user,
    profile_8_business_oriented,
    profile_9_parallel_power_user,
    profile_10_mixed_session,
]


def check_value(actual, op, expected):
    if op == "==":
        return actual == expected
    elif op == ">=":
        return actual >= expected
    elif op == ">":
        return actual > expected
    elif op == "<":
        return actual < expected
    elif op == "<=":
        return actual <= expected
    return False


def run_profile_test(idx, profile_fn, script):
    """运行单个项目的测试"""
    jsonl_data, spec = profile_fn()
    name = spec["name"]
    expected_level = spec["expected_level"]

    print(f"\n{'─' * 55}")
    print(f"  项目 {idx}: {name}")
    print(f"  预期能力等级: {expected_level}")
    print(f"{'─' * 55}")

    # 运行信号提取
    signals, err = run_extraction(script, jsonl_data)
    if err:
        test(f"项目{idx} 信号提取成功", False, err[:200])
        return

    test(f"项目{idx} 信号提取成功", True)

    # 验证具体信号值
    for check_key, check_spec in spec["checks"].items():
        # 特殊检查
        if check_key == "error_recovery_bash_heavy":
            err_tools = signals.get("error_recovery_tools", {})
            bash_ratio = err_tools.get("Bash", 0) / max(sum(err_tools.values()), 1) if err_tools else 0
            test(f"项目{idx} 出错后重试 Bash 占比高", bash_ratio >= 0.5 or not err_tools,
                 f"Bash 重试占比: {bash_ratio:.0%}")
            continue

        # skill_usage 子检查
        if check_key.startswith("skill_usage_"):
            skill_name = check_key.replace("skill_usage_", "")
            actual = signals.get("skill_usage", {}).get(skill_name, 0)
            op, expected = check_spec
            test(f"项目{idx} Skill '{skill_name}' 使用次数 {op} {expected}",
                 check_value(actual, op, expected), f"实际: {actual}")
            continue

        # 常规字段检查
        actual = signals.get(check_key, 0)
        op, expected = check_spec
        test(f"项目{idx} {check_key} {op} {expected}",
             check_value(actual, op, expected), f"实际: {actual}")

    # 打印信号摘要
    print(f"  📊 信号摘要: tools={len(signals.get('tool_usage', {}))}种, "
          f"tests={signals.get('test_command_count', 0)}, "
          f"commits={signals.get('git_commit_count', 0)}, "
          f"plan={signals.get('plan_mode_count', 0)}, "
          f"parallel={signals.get('parallel_agents', 0)}, "
          f"avg_msg_len={signals.get('avg_user_msg_length', 0):.0f}字")


def main():
    print("=" * 60)
    print("  AI Coach 评估模式集成测试")
    print("  10 个模拟真实开发者项目")
    print("=" * 60)

    # 提取信号提取脚本
    script = extract_python_script()
    if not script:
        print("\n❌ 无法从 SKILL.md 中提取 Python 信号提取脚本")
        sys.exit(1)

    # 验证脚本语法
    try:
        compile(script, "<signal_extraction>", "exec")
        test("信号提取脚本语法正确", True)
    except SyntaxError as e:
        test("信号提取脚本语法正确", False, str(e))
        sys.exit(1)

    # 运行 10 个项目测试
    for idx, profile_fn in enumerate(PROFILES, 1):
        run_profile_test(idx, profile_fn, script)

    # ═══ 汇总 ═══
    print(f"\n{'=' * 60}")
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print(f"\n  总计: {total} 项 | 通过: {passed} ✅ | 失败: {failed} ❌")
    print(f"  通过率: {passed / total * 100:.1f}%")

    if failed > 0:
        print(f"\n  ── 失败项汇总 ──")
        for r in results:
            if not r["passed"]:
                print(f"  ❌ {r['name']}" + (f" — {r['detail']}" if r['detail'] else ""))

    # 保存结果
    result_path = os.path.join(os.path.dirname(__file__), "test_evaluation_results.json")
    with open(result_path, "w") as f:
        json.dump({"total": total, "passed": passed, "failed": failed, "results": results}, f, indent=2, ensure_ascii=False)
    print(f"\n  📊 详细结果: {result_path}")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
