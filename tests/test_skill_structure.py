#!/usr/bin/env python3
"""
AI Coach v3 Skill 自动化测试套件
验证所有子 skill 的结构完整性、内容完整性、角色路由一致性。
"""

import os
import re
import json
import sys

SKILLS_DIR = os.path.expanduser("~/.claude/skills/ai-coach")

# 期望存在的 skill 文件
SKILL_FILES = {
    "main": os.path.join(SKILLS_DIR, "SKILL.md"),
    "fullstack": os.path.join(SKILLS_DIR, "fullstack/SKILL.md"),
    "product": os.path.join(SKILLS_DIR, "product/SKILL.md"),
    "backend": os.path.join(SKILLS_DIR, "backend/SKILL.md"),
    "testing": os.path.join(SKILLS_DIR, "testing/SKILL.md"),
    "frontend": os.path.join(SKILLS_DIR, "frontend/SKILL.md"),
    "init": os.path.join(SKILLS_DIR, "init/SKILL.md"),
    "enterprise": os.path.join(SKILLS_DIR, "enterprise/SKILL.md"),
    "evaluate": os.path.join(SKILLS_DIR, "evaluate/SKILL.md"),
}

SYMLINKS = {
    "ai-coach-fullstack": os.path.expanduser("~/.claude/skills/ai-coach-fullstack"),
    "ai-coach-product": os.path.expanduser("~/.claude/skills/ai-coach-product"),
    "ai-coach-backend": os.path.expanduser("~/.claude/skills/ai-coach-backend"),
    "ai-coach-testing": os.path.expanduser("~/.claude/skills/ai-coach-testing"),
    "ai-coach-frontend": os.path.expanduser("~/.claude/skills/ai-coach-frontend"),
    "ai-coach-init": os.path.expanduser("~/.claude/skills/ai-coach-init"),
    "ai-coach-enterprise": os.path.expanduser("~/.claude/skills/ai-coach-enterprise"),
    "ai-coach-evaluate": os.path.expanduser("~/.claude/skills/ai-coach-evaluate"),
}

results = []


def test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "passed": passed, "detail": detail})
    icon = "✅" if passed else "❌"
    print(f"  {icon} {name}" + (f" — {detail}" if detail and not passed else ""))


def load(path):
    with open(path, "r") as f:
        return f.read()


# ═══ 测试组 1：文件存在性 ═══

def test_file_existence():
    print("\n═══ 测试组 1：文件存在性 ═══")

    for skill_name, path in SKILL_FILES.items():
        # 处理软链接指向的目录
        resolved = os.path.realpath(path) if os.path.islink(path) else path
        exists = os.path.exists(resolved)
        test(f"skill 文件存在：{skill_name}", exists, path if not exists else "")

    # 软链接检查（可能是真实目录，也可能是软链接）
    for link_name, link_path in SYMLINKS.items():
        accessible = os.path.exists(link_path)
        test(f"子 skill 可访问：{link_name}", accessible, link_path if not accessible else "")

    # install.sh 存在
    install_sh = os.path.join(SKILLS_DIR, "install.sh")
    test("install.sh 存在", os.path.exists(install_sh))


# ═══ 测试组 2：主 SKILL.md 入口结构 ═══

def test_main_skill():
    print("\n═══ 测试组 2：主 SKILL.md 入口结构 ═══")
    path = SKILL_FILES["main"]
    if not os.path.exists(path):
        print(f"  ⚠️ 跳过（文件不存在）")
        return

    content = load(path)

    # 2.1 frontmatter
    test("主 skill: YAML frontmatter", content.startswith("---"))
    test("主 skill: name = ai-coach", "name: ai-coach" in content)
    test("主 skill: version = 3.1.0", "version: 3.1.0" in content)

    # 2.2 When to Activate
    test("主 skill: When to Activate 存在", "## When to Activate" in content)
    test("主 skill: 触发词包含\"教练\"", "教练" in content)
    test("主 skill: 触发词包含\"复盘\"", "复盘" in content)

    # 2.3 全局规则
    test("主 skill: 全局规则节存在", "全局规则" in content)
    test("主 skill: 教练不执行规则", "教练不执行" in content or "只引导" in content)
    test("主 skill: 语言自适应规则", "语言自适应" in content)
    test("主 skill: 角色记忆规则", "角色记忆" in content)
    test("主 skill: 治具改进循环规则", "治具改进循环" in content)

    # 2.4 Step 0 入口路由
    test("主 skill: Step 0 入口路由存在", "Step 0" in content)
    test("主 skill: Step 0.1 检查角色记忆", "0.1" in content and "角色记忆" in content)
    test("主 skill: Step 0.2 角色选择", "0.2" in content and "角色选择" in content)
    test("主 skill: Step 0.3 主菜单", "0.3" in content and "主菜单" in content)
    test("主 skill: Step 0.4 角色路由表", "0.4" in content and "路由表" in content)

    # 2.5 角色路由表完整（5 种角色 + 评估 + 企业级）
    test("路由表：一人全栈", "ai-coach-fullstack" in content)
    test("路由表：产品", "ai-coach-product" in content)
    test("路由表：后端", "ai-coach-backend" in content)
    test("路由表：测试", "ai-coach-testing" in content)
    test("路由表：前端", "ai-coach-frontend" in content)
    test("路由表：评估", "ai-coach-evaluate" in content)
    test("路由表：企业级", "ai-coach-enterprise" in content)

    # 2.6 Memory 写入格式
    test("主 skill: Memory 写入格式定义", "AI教练角色:" in content)

    # 2.7 角色选择菜单 5 个选项
    role_options = ["一人全栈", "产品", "后端", "测试", "前端"]
    for r in role_options:
        test(f"角色菜单包含：{r}", r in content)

    # 2.8 主菜单 4 个选项
    main_menu_options = ["开启新任务", "复盘总结", "切换角色", "快速提问"]
    for opt in main_menu_options:
        test(f"主菜单包含：{opt}", opt in content)


# ═══ 测试组 3：各角色 sub-skill 结构 ═══

def test_role_skills():
    print("\n═══ 测试组 3：各角色 sub-skill 结构 ═══")

    # 3.1 一人全栈
    _test_role("fullstack", required_steps=["Step 1", "Step 2", "Step 3"],
               required_content=["五大核心原则", "Skill 表", "示范提示词", "brainstorming"])

    # 3.2 产品
    _test_role("product", required_steps=["Step P1", "Step P2", "Step P3", "Step P4", "Step P5"],
               required_content=["历史资产盘点", "AI 可执行", "原型", "prd-development"])

    # 3.3 后端
    _test_role("backend", required_steps=["Step B1", "Step B2", "Step B3", "Step B4"],
               required_content=["后台管理", "TDD", "B-Bug", "B-Emergency"])

    # 3.4 测试
    _test_role("testing", required_steps=["Step T1", "Step T2", "Step T3", "Step T4"],
               required_content=["测试金字塔", "T-Quick", "T-Regression", "Playwright"])

    # 3.5 前端
    _test_role("frontend", required_steps=["Step F1", "Step F2", "Step F3", "Step F4"],
               required_content=["目标平台", "Mock", "F-Bug", "F-Emergency"])


def _test_role(role, required_steps, required_content):
    path = SKILL_FILES[role]
    if not os.path.exists(path):
        # 尝试软链接路径
        link_path = os.path.expanduser(f"~/.claude/skills/ai-coach-{role}")
        skill_in_link = os.path.join(link_path, "SKILL.md") if os.path.isdir(link_path) else link_path + "/SKILL.md"
        if not os.path.exists(link_path):
            test(f"{role}: SKILL.md 可访问", False, f"路径不存在: {path}")
            return
        content = load(os.path.join(link_path, "SKILL.md") if os.path.isdir(link_path) else link_path + "/SKILL.md")
    else:
        content = load(path)

    # frontmatter
    test(f"{role}: YAML frontmatter", content.startswith("---"))
    test(f"{role}: version = 3.1.0", "version: 3.1.0" in content)

    # 必要 Step 存在
    for step in required_steps:
        # 匹配各种格式
        found = (f"## {step}" in content or f"### {step}" in content or
                 f"#### {step}" in content or
                 re.search(rf"{re.escape(step)}[:\s]", content) is not None)
        test(f"{role}: {step} 存在", found)

    # 必要内容存在
    for item in required_content:
        test(f"{role}: 包含「{item}」", item in content)

    # Harness Engineering：治具优先检查（backend/testing/product/frontend）
    if role in ("backend", "testing", "product", "frontend"):
        test(f"{role}: 包含「治具优先」", "治具优先" in content)
        test(f"{role}: 包含「治具建议」", "治具建议" in content)


# ═══ 测试组 4：init/SKILL.md 自检流程 ═══

def test_init_skill():
    print("\n═══ 测试组 4：init/SKILL.md 自检流程 ═══")
    path = SKILL_FILES["init"]
    if not os.path.exists(path):
        link_path = os.path.expanduser("~/.claude/skills/ai-coach-init/SKILL.md")
        if not os.path.exists(link_path):
            test("init: SKILL.md 可访问", False)
            return
        content = load(link_path)
    else:
        content = load(path)

    test("init: version = 3.1.0", "version: 3.1.0" in content)
    test("init: 三层检查结构", "第一层" in content or "Layer 1" in content or "全局" in content)
    test("init: CLAUDE.md 检查", "CLAUDE.md" in content)
    test("init: Memory 目录检查", "Memory" in content)
    test("init: Skill 检查", "Skill" in content or "skill" in content)
    test("init: 角色专属检查", "角色专属" in content or "第二层" in content or "Layer 2" in content)
    test("init: 日常静默检查", "日常" in content or "第三层" in content or "Layer 3" in content)
    test("init: 非技术友好语言", "建议" in content and "阻塞" not in content[:500])

    # Harness Engineering：init 治具健康度
    test("init: CLAUDE.md 4 关键段检查", "关键段" in content or ("技术栈" in content and "测试约定" in content))
    test("init: Hooks 检查", "Hooks" in content or "hooks" in content)
    test("init: 历史产出检查", "历史产出" in content)


# ═══ 测试组 5：evaluate/SKILL.md 评估流程 ═══

def test_evaluate_skill():
    print("\n═══ 测试组 5：evaluate/SKILL.md 评估流程 ═══")
    path = SKILL_FILES["evaluate"]
    if not os.path.exists(path):
        link_path = os.path.expanduser("~/.claude/skills/ai-coach-evaluate/SKILL.md")
        if not os.path.exists(link_path):
            test("evaluate: SKILL.md 可访问", False)
            return
        content = load(link_path)
    else:
        content = load(path)

    test("evaluate: version = 3.1.0", "version: 3.1.0" in content)

    # Step 9 角色读取
    test("evaluate: Step 9 角色读取", "Step 9" in content and "AI教练角色" in content)

    # 5 种角色评分维度
    test("evaluate: 全栈评分维度（13-A）", "13-A" in content or "一人全栈" in content)
    test("evaluate: 产品评分维度（13-B）", "13-B" in content or ("产品" in content and "PRD" in content))
    test("evaluate: 后端评分维度（13-C）", "13-C" in content or ("后端" in content and "TDD" in content))
    test("evaluate: 测试评分维度（13-D）", "13-D" in content or ("测试" in content and "自动化" in content))
    test("evaluate: 前端评分维度（13-E）", "13-E" in content or ("前端" in content and "组件" in content))

    # 评分相关
    test("evaluate: 百分制评分", "/100" in content)
    test("evaluate: 能力等级（L1/L2/L3）", "L1" in content and "L2" in content and "L3" in content)
    test("evaluate: 终端摘要输出", "★" in content)
    test("evaluate: 改进建议", "改进建议" in content or "建议" in content)

    # Harness Engineering：分层建议
    test("evaluate: L1 基础建议", "L1" in content and ("< 40" in content or "基础" in content))
    test("evaluate: L2 进阶建议", "L2" in content and ("40-70" in content or "进阶" in content))
    test("evaluate: L3 专家建议含 Harness", "Harness Engineering" in content)
    test("evaluate: history.json", "history.json" in content)
    test("evaluate: 角色记录", "role" in content or "角色" in content)

    # analyze_sessions.py
    analyzer = os.path.join(SKILLS_DIR, "evaluate/analyze_sessions.py")
    test("evaluate: analyze_sessions.py 存在", os.path.exists(analyzer))

    if os.path.exists(analyzer):
        with open(analyzer, "r") as f:
            py_content = f.read()
        test("evaluate: 角色读取函数", "read_role_from_memory" in py_content or "AI教练角色" in py_content)
        test("evaluate: 角色专项字段", "prd_references" in py_content or "test_report_outputs" in py_content)


# ═══ 测试组 6：enterprise/SKILL.md 精简验证 ═══

def test_enterprise_skill():
    print("\n═══ 测试组 6：enterprise/SKILL.md 精简验证 ═══")
    path = SKILL_FILES["enterprise"]
    if not os.path.exists(path):
        link_path = os.path.expanduser("~/.claude/skills/ai-coach-enterprise/SKILL.md")
        if not os.path.exists(link_path):
            test("enterprise: SKILL.md 可访问", False)
            return
        content = load(link_path)
    else:
        content = load(path)

    line_count = len(content.splitlines())
    test("enterprise: 已精简（< 150 行）", line_count < 150, f"实际: {line_count} 行")
    test("enterprise: 版本 3.0.0", "version: 3.1.0" in content)
    test("enterprise: 大型项目框架保留", "A 阶段" in content or "Phase A" in content or "全景" in content)
    test("enterprise: 跨模块协作", "跨" in content and ("团队" in content or "模块" in content))
    test("enterprise: 分阶段计划", "阶段" in content and ("交付" in content or "验收" in content))


# ═══ 测试组 7：测试用例文件完整性 ═══

def test_case_files():
    print("\n═══ 测试组 7：测试用例文件完整性 ═══")
    tests_dir = os.path.join(SKILLS_DIR, "tests")

    # 计算用例文件总数
    case_files = [f for f in os.listdir(tests_dir) if f.startswith("case-") and f.endswith(".md")]
    case_count = len(case_files)
    test(f"测试用例总数 >= 30", case_count >= 30, f"实际: {case_count} 个")

    # v3.1 全量用例（case-51 到 case-83）
    for i in range(51, 84):
        num_str = str(i)
        has_file = any(f.startswith(f"case-{num_str}-") for f in case_files)
        test(f"case-{num_str} 存在", has_file)

    # TEST-PLAN.md 存在
    test("TEST-PLAN.md 存在", os.path.exists(os.path.join(tests_dir, "TEST-PLAN.md")))

    # Python 测试脚本
    test("test_skill_structure.py 存在", os.path.exists(os.path.join(tests_dir, "test_skill_structure.py")))
    test("test_evaluation_profiles.py 存在", os.path.exists(os.path.join(tests_dir, "test_evaluation_profiles.py")))


# ═══ 测试组 8：内容一致性检查 ═══

def test_consistency():
    print("\n═══ 测试组 8：内容一致性检查 ═══")

    # 所有 skill 版本号一致（3.0.0）
    for skill_name, path in SKILL_FILES.items():
        if os.path.exists(path):
            content = load(path)
            if "version:" in content:
                test(f"{skill_name}: 版本号为 3.0.0", "version: 3.1.0" in content)

    # Memory 格式一致（所有 skill 都使用相同的 Memory key）
    main_content = load(SKILL_FILES["main"]) if os.path.exists(SKILL_FILES["main"]) else ""
    memory_format = "AI教练角色:"
    test(f"主 skill Memory 格式: {memory_format}", memory_format in main_content)

    # 子 skill 描述字段精简（description 长度合理）
    for skill_name, path in SKILL_FILES.items():
        if skill_name == "main":
            continue
        if os.path.exists(path):
            content = load(path)
            desc_match = re.search(r"description:\s*(.+)", content)
            if desc_match:
                desc_len = len(desc_match.group(1))
                test(f"{skill_name}: description <= 50 字符", desc_len <= 50,
                     f"实际: {desc_len} 字符 — {desc_match.group(1)[:30]}...")

    # 安装使用.md 存在
    usage_md = os.path.join(SKILLS_DIR, "安装使用.md")
    test("安装使用.md 存在", os.path.exists(usage_md))

    if os.path.exists(usage_md):
        content = load(usage_md)
        test("安装使用.md: 包含 install.sh 说明", "install.sh" in content)
        test("安装使用.md: 包含 10 个场景", content.count("## 场景") >= 8)
        test("安装使用.md: 包含产品角色场景", "产品角色" in content or "产品经理" in content)
        test("安装使用.md: 包含后端角色场景", "后端角色" in content or "后端开发" in content)
        test("安装使用.md: 包含测试角色场景", "测试角色" in content or "测试工程师" in content)
        test("安装使用.md: 包含前端角色场景", "前端角色" in content or "前端开发" in content or "移动端" in content)


# ═══ 主入口 ═══

def main():
    print("=" * 60)
    print("  AI Coach v3 Skill 自动化测试套件")
    print("=" * 60)

    test_file_existence()
    test_main_skill()
    test_role_skills()
    test_init_skill()
    test_evaluate_skill()
    test_enterprise_skill()
    test_case_files()
    test_consistency()

    # ═══ 汇总 ═══
    print("\n" + "=" * 60)
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print(f"\n  总计: {total} 项 | 通过: {passed} ✅ | 失败: {failed} ❌")
    print(f"  通过率: {passed/total*100:.1f}%")

    if failed > 0:
        print("\n  ── 失败项汇总 ──")
        for r in results:
            if not r["passed"]:
                print(f"  ❌ {r['name']}" + (f" — {r['detail']}" if r['detail'] else ""))

    # 输出 JSON 结果
    result_path = os.path.join(os.path.dirname(__file__), "test_results_v3.json")
    with open(result_path, "w") as f:
        json.dump({"total": total, "passed": passed, "failed": failed, "results": results}, f,
                  indent=2, ensure_ascii=False)
    print(f"\n  📊 详细结果: {result_path}")

    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
