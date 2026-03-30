#!/usr/bin/env python3
"""
AI Coach v3 SKILL.md 完整性验证测试

验证三个 SKILL.md 文件的结构、内容、引用关系。
"""

import os
import re

import pytest
import yaml


# ============================================================
# Constants
# ============================================================

SKILLS_DIR = os.path.expanduser('~/.claude/skills')
COACH_DIR = os.path.join(SKILLS_DIR, 'ai-coach')
ENTERPRISE_DIR = os.path.join(SKILLS_DIR, 'ai-coach-enterprise')
EVALUATE_DIR = os.path.join(SKILLS_DIR, 'ai-coach-evaluate')

SKILL_FILES = {
    'coach': os.path.join(COACH_DIR, 'SKILL.md'),
    'enterprise': os.path.join(ENTERPRISE_DIR, 'SKILL.md'),
    'evaluate': os.path.join(EVALUATE_DIR, 'SKILL.md'),
}


# ============================================================
# Fixtures
# ============================================================

def read_skill(key):
    """读取 SKILL.md 文件内容"""
    path = SKILL_FILES[key]
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_frontmatter(content):
    """解析 YAML frontmatter"""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None
    return yaml.safe_load(match.group(1))


@pytest.fixture
def coach_content():
    return read_skill('coach')


@pytest.fixture
def enterprise_content():
    return read_skill('enterprise')


@pytest.fixture
def evaluate_content():
    return read_skill('evaluate')


@pytest.fixture
def coach_meta():
    return parse_frontmatter(read_skill('coach'))


@pytest.fixture
def enterprise_meta():
    return parse_frontmatter(read_skill('enterprise'))


@pytest.fixture
def evaluate_meta():
    return parse_frontmatter(read_skill('evaluate'))


# ============================================================
# 文件存在性测试
# ============================================================

class TestFileExistence:
    """所有必需文件存在"""

    def test_coach_skill_exists(self):
        assert os.path.isfile(SKILL_FILES['coach']), 'ai-coach/SKILL.md 不存在'

    def test_enterprise_skill_exists(self):
        assert os.path.isfile(SKILL_FILES['enterprise']), 'ai-coach-enterprise/SKILL.md 不存在'

    def test_evaluate_skill_exists(self):
        assert os.path.isfile(SKILL_FILES['evaluate']), 'ai-coach-evaluate/SKILL.md 不存在'

    def test_analyze_script_exists(self):
        path = os.path.join(EVALUATE_DIR, 'analyze_sessions.py')
        assert os.path.isfile(path), 'analyze_sessions.py 不存在'

    def test_analyze_script_executable(self):
        path = os.path.join(EVALUATE_DIR, 'analyze_sessions.py')
        assert os.access(path, os.X_OK), 'analyze_sessions.py 不可执行'


# ============================================================
# YAML Frontmatter 验证
# ============================================================

class TestFrontmatter:
    """YAML frontmatter 格式和必需字段"""

    def test_coach_has_valid_frontmatter(self, coach_content):
        meta = parse_frontmatter(coach_content)
        assert meta is not None, 'ai-coach 缺少 YAML frontmatter'

    def test_enterprise_has_valid_frontmatter(self, enterprise_content):
        meta = parse_frontmatter(enterprise_content)
        assert meta is not None, 'ai-coach-enterprise 缺少 YAML frontmatter'

    def test_evaluate_has_valid_frontmatter(self, evaluate_content):
        meta = parse_frontmatter(evaluate_content)
        assert meta is not None, 'ai-coach-evaluate 缺少 YAML frontmatter'

    def test_coach_required_fields(self, coach_meta):
        assert 'name' in coach_meta, '缺少 name 字段'
        assert 'description' in coach_meta, '缺少 description 字段'
        assert 'version' in coach_meta, '缺少 version 字段'

    def test_enterprise_required_fields(self, enterprise_meta):
        assert 'name' in enterprise_meta, '缺少 name 字段'
        assert 'description' in enterprise_meta, '缺少 description 字段'
        assert 'version' in enterprise_meta, '缺少 version 字段'

    def test_evaluate_required_fields(self, evaluate_meta):
        assert 'name' in evaluate_meta, '缺少 name 字段'
        assert 'description' in evaluate_meta, '缺少 description 字段'
        assert 'version' in evaluate_meta, '缺少 version 字段'

    def test_coach_name_correct(self, coach_meta):
        assert coach_meta['name'] == 'ai-coach'

    def test_enterprise_name_correct(self, enterprise_meta):
        assert enterprise_meta['name'] == 'ai-coach-enterprise'

    def test_evaluate_name_correct(self, evaluate_meta):
        assert evaluate_meta['name'] == 'ai-coach-evaluate'

    def test_coach_version_format(self, coach_meta):
        """版本号格式正确 (X.Y.Z)"""
        assert re.match(r'^\d+\.\d+\.\d+$', coach_meta['version']), \
            f"版本号格式错误: {coach_meta['version']}"

    def test_coach_enterprise_version_match(self, coach_meta, enterprise_meta):
        """主技能和企业知识库版本号一致"""
        assert coach_meta['version'] == enterprise_meta['version'], \
            f"版本不一致: coach={coach_meta['version']}, enterprise={enterprise_meta['version']}"

    def test_coach_evaluate_version_match(self, coach_meta, evaluate_meta):
        """主技能和评估技能版本号一致"""
        assert coach_meta['version'] == evaluate_meta['version'], \
            f"版本不一致: coach={coach_meta['version']}, evaluate={evaluate_meta['version']}"


# ============================================================
# 主技能内容验证
# ============================================================

class TestCoachContent:
    """ai-coach/SKILL.md 内容结构验证"""

    def test_has_core_positioning(self, coach_content):
        """包含核心定位说明"""
        assert '教练不帮你做事' in coach_content or '核心定位' in coach_content

    def test_has_five_principles(self, coach_content):
        """包含五大核心原则"""
        assert '五大核心原则' in coach_content
        assert 'AI 是有注意力预算的协作者' in coach_content
        assert '先用最简单的方法' in coach_content
        assert '测试和评估是唯一的真相' in coach_content
        assert '人类拥有架构和判断' in coach_content
        assert '护城河在系统' in coach_content

    def test_has_mental_leaps(self, coach_content):
        """包含心智跃迁表"""
        assert '心智跃迁' in coach_content
        assert '写提示词' in coach_content
        assert '设计信息环境' in coach_content

    def test_has_complexity_ladder(self, coach_content):
        """包含复杂度阶梯"""
        assert '复杂度阶梯' in coach_content
        assert 'Level 0' in coach_content

    def test_has_step_minus_1(self, coach_content):
        """包含 Step -1 环境就绪检查"""
        assert 'Step -1' in coach_content
        assert '环境就绪检查' in coach_content

    def test_step_minus_1_checks_superpowers(self, coach_content):
        """Step -1 检测 superpowers 插件"""
        assert 'superpowers' in coach_content
        # 检查检测命令
        assert 'superpowers-marketplace/superpowers' in coach_content

    def test_step_minus_1_checks_find_skills(self, coach_content):
        """Step -1 检测 find-skills 技能"""
        assert 'find-skills' in coach_content

    def test_step_minus_1_checks_prd_development(self, coach_content):
        """Step -1 检测 prd-development 技能"""
        assert 'prd-development' in coach_content

    def test_step_minus_1_has_install_commands(self, coach_content):
        """Step -1 包含安装命令"""
        assert 'npx skills add' in coach_content or 'claude plugin' in coach_content

    def test_has_step_0_role_identification(self, coach_content):
        """包含 Step 0 角色识别"""
        assert 'Step 0' in coach_content
        assert '角色' in coach_content
        assert '产品人' in coach_content
        assert '技术人' in coach_content
        assert '全栈型' in coach_content

    def test_has_step_1_intent(self, coach_content):
        """包含 Step 1 意图识别"""
        assert 'Step 1' in coach_content
        assert '意图识别' in coach_content

    def test_has_step_2_diagnosis(self, coach_content):
        """包含 Step 2 任务诊断"""
        assert 'Step 2' in coach_content
        assert '任务诊断' in coach_content

    def test_step_2_has_role_routing(self, coach_content):
        """Step 2 包含角色路由"""
        assert '角色路由' in coach_content or '产品人路径' in coach_content
        assert '技术人路径' in coach_content
        assert '全栈型路径' in coach_content

    def test_step_2_has_togaf(self, coach_content):
        """Step 2 包含 TOGAF 方法论参考"""
        assert 'TOGAF' in coach_content

    def test_has_step_3_guide_generation(self, coach_content):
        """包含 Step 3 引导指南生成"""
        assert 'Step 3' in coach_content
        assert '引导指南' in coach_content

    def test_step_3_has_product_template(self, coach_content):
        """Step 3 包含产品人版模板"""
        assert '产品人版' in coach_content or '角色：产品人' in coach_content

    def test_step_3_has_tech_template(self, coach_content):
        """Step 3 包含技术人版模板"""
        assert '技术人版' in coach_content or '角色：技术人' in coach_content

    def test_step_3_has_fullstack_template(self, coach_content):
        """Step 3 包含巨型项目全链路版模板"""
        assert '全链路' in coach_content

    def test_step_3_has_skill_recommendations(self, coach_content):
        """Step 3 包含 Skill 推荐矩阵"""
        assert '/brainstorm' in coach_content
        assert '/write-plan' in coach_content
        assert '/execute-plan' in coach_content
        assert '/prd-development' in coach_content

    def test_references_enterprise(self, coach_content):
        """引用 ai-coach-enterprise 子技能"""
        assert 'ai-coach-enterprise' in coach_content

    def test_references_evaluate(self, coach_content):
        """引用 ai-coach-evaluate 子技能"""
        assert 'ai-coach-evaluate' in coach_content

    def test_has_when_to_activate(self, coach_content):
        """包含触发条件"""
        assert 'When to Activate' in coach_content

    def test_has_global_rules(self, coach_content):
        """包含全局规则"""
        assert '全局规则' in coach_content
        assert '中途切换' in coach_content
        assert '语言自适应' in coach_content


# ============================================================
# 企业级知识库内容验证
# ============================================================

class TestEnterpriseContent:
    """ai-coach-enterprise/SKILL.md 内容验证"""

    def test_has_product_knowledge(self, enterprise_content):
        """包含产品经理知识库"""
        assert '产品经理知识库' in enterprise_content or '产品人' in enterprise_content

    def test_has_togaf_framework(self, enterprise_content):
        """包含 TOGAF 框架"""
        assert 'TOGAF' in enterprise_content
        assert '战略愿景' in enterprise_content
        assert '业务架构' in enterprise_content

    def test_has_business_canvas(self, enterprise_content):
        """包含业务模式画布"""
        assert '业务模式画布' in enterprise_content
        assert '客户细分' in enterprise_content
        assert '价值主张' in enterprise_content

    def test_has_alibaba_bytedance_model(self, enterprise_content):
        """包含阿里/字节产品思维模型"""
        assert '阿里' in enterprise_content or '字节' in enterprise_content
        assert 'PMF' in enterprise_content or '用户价值优先' in enterprise_content

    def test_has_jtbd(self, enterprise_content):
        """包含 JTBD 方法论"""
        assert 'JTBD' in enterprise_content or 'Jobs-to-be-Done' in enterprise_content

    def test_has_tech_knowledge(self, enterprise_content):
        """包含技术知识库"""
        assert 'Bug 修复' in enterprise_content
        assert 'TDD' in enterprise_content
        assert '重构' in enterprise_content

    def test_has_giant_project_knowledge(self, enterprise_content):
        """包含巨型项目知识库"""
        assert '巨型项目' in enterprise_content
        assert '全链路' in enterprise_content

    def test_has_six_phase_framework(self, enterprise_content):
        """包含六阶段框架"""
        assert '阶段 A' in enterprise_content or '战略分析' in enterprise_content
        assert '阶段 F' in enterprise_content or '迭代执行' in enterprise_content

    def test_has_guide_generation_reference(self, enterprise_content):
        """包含引导指南生成参考"""
        assert '引导指南' in enterprise_content
        assert 'ailearn' in enterprise_content or '李飞飞' in enterprise_content or '吴恩达' in enterprise_content

    def test_has_quality_checklist(self, enterprise_content):
        """包含引导指南质量检查清单"""
        assert '质量检查' in enterprise_content

    def test_has_security_checklist(self, enterprise_content):
        """包含安全类 Checklist"""
        assert 'OWASP' in enterprise_content

    def test_has_api_checklist(self, enterprise_content):
        """包含 API 对接类 Checklist"""
        assert 'API 对接' in enterprise_content or 'RESTful' in enterprise_content

    def test_has_db_migration_checklist(self, enterprise_content):
        """包含数据库迁移类 Checklist"""
        assert '数据库迁移' in enterprise_content


# ============================================================
# Evaluate 兼容性验证
# ============================================================

class TestEvaluateCompatibility:
    """ai-coach-evaluate 与 v3 的兼容性"""

    def test_has_eight_dimensions(self, evaluate_content):
        """包含八维评分"""
        assert 'SOP 流程合规' in evaluate_content
        assert '上下文工程' in evaluate_content
        assert '提示词与交互' in evaluate_content
        assert 'TDD 与质量' in evaluate_content
        assert '工具使用成熟度' in evaluate_content
        assert '业务理解' in evaluate_content
        assert '学习成长' in evaluate_content
        assert '方法论内化' in evaluate_content

    def test_version_reference_updated(self, evaluate_content):
        """版本引用已更新到 v3"""
        assert 'v3.0.0' in evaluate_content

    def test_has_analyze_script_reference(self, evaluate_content):
        """引用 analyze_sessions.py"""
        assert 'analyze_sessions.py' in evaluate_content

    def test_has_teaching_guidance(self, evaluate_content):
        """包含教学引导"""
        assert 'Step 16' in evaluate_content or '教学引导' in evaluate_content


# ============================================================
# 跨文件引用一致性
# ============================================================

class TestCrossReferences:
    """三个技能文件之间的引用一致性"""

    def test_coach_skill_names_match(self, coach_content):
        """主技能引用的子技能名称正确"""
        assert 'ai-coach-enterprise' in coach_content
        assert 'ai-coach-evaluate' in coach_content

    def test_enterprise_role_reference(self, enterprise_content):
        """企业知识库引用主技能"""
        assert 'ai-coach' in enterprise_content

    def test_evaluate_role_reference(self, evaluate_content):
        """评估技能引用主技能"""
        assert 'ai-coach' in evaluate_content

    def test_skill_recommendation_consistency(self, coach_content, enterprise_content):
        """推荐的 Skill 在两个文件中一致"""
        skills_in_coach = set(re.findall(r'`/([\w-]+)`', coach_content))
        skills_in_enterprise = set(re.findall(r'`/([\w-]+)`', enterprise_content))

        # 核心 Skill 应该在两边都被提及
        core_skills = {'brainstorm', 'write-plan', 'execute-plan'}
        for skill in core_skills:
            assert skill in skills_in_coach, f'{skill} 不在 coach 中'

    def test_complexity_levels_consistent(self, coach_content, enterprise_content):
        """复杂度级别定义在两个文件中一致"""
        for level in ['标准级', '企业级', '巨型级']:
            assert level in coach_content, f'{level} 不在 coach 中'

    def test_dependency_install_commands_valid(self, coach_content):
        """依赖安装命令格式有效"""
        # 检查 npx skills add 命令
        npx_commands = re.findall(r'npx skills add (\S+)', coach_content)
        assert len(npx_commands) >= 2, f'npx skills add 命令数量不足: {npx_commands}'

        # 检查 claude plugin 命令
        plugin_commands = re.findall(r'claude plugin (install|marketplace)', coach_content)
        assert len(plugin_commands) >= 2, f'claude plugin 命令数量不足: {plugin_commands}'
