#!/usr/bin/env python3
"""
AI Coach v4.0 SKILL.md 完整性验证测试

验证所有 SKILL.md 文件的结构、内容、引用关系、红线合规。
"""

import os
import re

import pytest
import yaml


# ============================================================
# Constants
# ============================================================

# 支持两种路径：开发目录 和 安装目录
DEV_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.expanduser('~/.claude/skills/ai-coach')

# 优先使用开发目录，回退到安装目录
BASE_DIR = DEV_DIR if os.path.isfile(os.path.join(DEV_DIR, 'SKILL.md')) else INSTALL_DIR

ROLE_DIRS = ['backend', 'frontend', 'product', 'testing', 'fullstack']
ALL_SKILL_DIRS = ROLE_DIRS + ['evaluate', 'enterprise', 'init']

EXPECTED_VERSION = '4.0.0'


# ============================================================
# Helpers
# ============================================================

def read_file(relative_path):
    """读取相对于 BASE_DIR 的文件"""
    path = os.path.join(BASE_DIR, relative_path)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_frontmatter(content):
    """解析 YAML frontmatter"""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None
    return yaml.safe_load(match.group(1))


# ============================================================
# 1. 文件存在性
# ============================================================

class TestFileExistence:
    """所有必需文件和目录存在"""

    def test_main_skill_exists(self):
        assert os.path.isfile(os.path.join(BASE_DIR, 'SKILL.md'))

    @pytest.mark.parametrize('subdir', ALL_SKILL_DIRS)
    def test_role_skill_exists(self, subdir):
        path = os.path.join(BASE_DIR, subdir, 'SKILL.md')
        assert os.path.isfile(path), f'{subdir}/SKILL.md 不存在'

    def test_coach_template_exists(self):
        assert os.path.isfile(os.path.join(BASE_DIR, 'common', 'COACH_TEMPLATE.md'))

    def test_knowledge_index_exists(self):
        assert os.path.isfile(os.path.join(BASE_DIR, 'knowledge', 'INDEX.md'))

    def test_knowledge_has_files(self):
        knowledge_dir = os.path.join(BASE_DIR, 'knowledge')
        md_files = [f for f in os.listdir(knowledge_dir) if f.endswith('.md') and f != 'INDEX.md']
        assert len(md_files) >= 10, f'知识库文件不足: {len(md_files)} 个'

    def test_knowledge_masters_exists(self):
        masters_dir = os.path.join(BASE_DIR, 'knowledge', 'masters')
        assert os.path.isdir(masters_dir)
        md_files = [f for f in os.listdir(masters_dir) if f.endswith('.md')]
        assert len(md_files) >= 10, f'大师档案不足: {len(md_files)} 个'


# ============================================================
# 2. Frontmatter 验证
# ============================================================

class TestFrontmatter:
    """YAML frontmatter 格式和必需字段"""

    def test_main_has_frontmatter(self):
        content = read_file('SKILL.md')
        meta = parse_frontmatter(content)
        assert meta is not None
        assert meta['name'] == 'ai-coach'
        assert meta['version'] == EXPECTED_VERSION

    def test_template_has_frontmatter(self):
        content = read_file('common/COACH_TEMPLATE.md')
        meta = parse_frontmatter(content)
        assert meta is not None
        assert meta['version'] == EXPECTED_VERSION

    @pytest.mark.parametrize('subdir', ROLE_DIRS)
    def test_role_has_frontmatter(self, subdir):
        content = read_file(f'{subdir}/SKILL.md')
        meta = parse_frontmatter(content)
        assert meta is not None, f'{subdir} 缺少 frontmatter'
        assert 'name' in meta
        assert 'version' in meta
        assert 'description' in meta

    @pytest.mark.parametrize('subdir', ROLE_DIRS)
    def test_role_version_is_4(self, subdir):
        content = read_file(f'{subdir}/SKILL.md')
        meta = parse_frontmatter(content)
        assert meta['version'] == EXPECTED_VERSION, \
            f'{subdir} 版本号: {meta["version"]}，期望 {EXPECTED_VERSION}'

    def test_init_version_is_4(self):
        content = read_file('init/SKILL.md')
        meta = parse_frontmatter(content)
        assert meta['version'] == EXPECTED_VERSION


# ============================================================
# 3. 主入口 SKILL.md
# ============================================================

class TestMainSkill:
    """主入口 SKILL.md 结构验证"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.content = read_file('SKILL.md')

    def test_has_when_to_activate(self):
        assert 'When to Activate' in self.content

    def test_has_global_rules(self):
        assert '全局规则' in self.content

    def test_rule_no_execute(self):
        """全局规则包含'教练不执行'"""
        assert '教练不执行' in self.content

    def test_rule_no_direct_solution(self):
        """全局规则包含'不给具体方案'"""
        assert '不给具体方案' in self.content

    def test_has_three_entries(self):
        """3 个平行入口"""
        assert '我有个任务要做' in self.content
        assert '角色视角' in self.content or '用特定角色视角' in self.content
        assert '复盘' in self.content

    def test_has_role_routing_table(self):
        """角色路由表"""
        assert '角色路由表' in self.content
        for role in ['全栈', '产品', '后端', '测试', '前端']:
            assert role in self.content

    def test_references_sub_skills(self):
        """引用所有子 skill"""
        assert 'ai-coach-fullstack' in self.content
        assert 'ai-coach-backend' in self.content
        assert 'ai-coach-frontend' in self.content
        assert 'ai-coach-product' in self.content
        assert 'ai-coach-testing' in self.content
        assert 'ai-coach-evaluate' in self.content
        assert 'ai-coach-init' in self.content

    def test_references_template(self):
        """引用 COACH_TEMPLATE"""
        assert 'COACH_TEMPLATE' in self.content

    def test_references_knowledge(self):
        """引用知识库"""
        assert 'knowledge/' in self.content or 'INDEX.md' in self.content

    def test_superpowers_workflow(self):
        """包含 superpowers 标准流程"""
        assert 'brainstorming' in self.content
        assert 'writing-plans' in self.content
        assert 'verification' in self.content


# ============================================================
# 4. COACH_TEMPLATE 验证
# ============================================================

class TestCoachTemplate:
    """标准教练流程模板验证"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.content = read_file('common/COACH_TEMPLATE.md')

    def test_has_three_phases(self):
        assert 'Phase 1' in self.content
        assert 'Phase 2' in self.content
        assert 'Phase 3' in self.content

    def test_phase1_task_snapshot(self):
        """Phase 1 包含任务快照 3 问"""
        assert '你要做什么' in self.content
        assert '什么状态' in self.content or '现在是什么状态' in self.content
        assert '现成资料' in self.content or '有没有现成资料' in self.content

    def test_phase1_complexity_judgment(self):
        """Phase 1 包含复杂度判断"""
        assert '简单' in self.content
        assert '中等' in self.content
        assert '复杂' in self.content

    def test_phase2_adaptive(self):
        """Phase 2 自适应"""
        assert '退出条件' in self.content
        assert '最多 3 个问题' in self.content or '最多 3' in self.content

    def test_phase3_report_format(self):
        """Phase 3 包含报告模板"""
        assert '任务概要' in self.content
        assert '复杂度评估' in self.content
        assert '推荐方法论' in self.content
        assert '执行建议' in self.content
        assert '示范提示词' in self.content
        assert '待补充项' in self.content

    def test_has_red_lines(self):
        """硬性约束红线"""
        assert '不产出' in self.content
        assert '只推荐' in self.content

    def test_has_knowledge_reference_rules(self):
        """知识库引用规则"""
        assert 'INDEX.md' in self.content
        assert 'knowledge/' in self.content or '知识库' in self.content

    def test_has_role_integration_spec(self):
        """角色接入规范"""
        assert '角色 SKILL' in self.content
        assert '问题池' in self.content or '诊断问题池' in self.content


# ============================================================
# 5. 角色 SKILL 模板一致性
# ============================================================

class TestRoleSkillStructure:
    """所有角色 SKILL 遵循模板结构"""

    @pytest.mark.parametrize('subdir', ROLE_DIRS)
    def test_declares_template_compliance(self, subdir):
        """声明遵循模板"""
        content = read_file(f'{subdir}/SKILL.md')
        assert 'COACH_TEMPLATE' in content, f'{subdir} 未声明遵循模板'

    @pytest.mark.parametrize('subdir', ROLE_DIRS)
    def test_has_phase2_question_pool(self, subdir):
        """包含 Phase 2 诊断问题池"""
        content = read_file(f'{subdir}/SKILL.md')
        assert 'Phase 2' in content or '诊断问题池' in content, \
            f'{subdir} 缺少 Phase 2 诊断问题池'

    @pytest.mark.parametrize('subdir', ROLE_DIRS)
    def test_has_complexity_levels(self, subdir):
        """问题池按复杂度分级"""
        content = read_file(f'{subdir}/SKILL.md')
        assert '简单任务' in content or '简单' in content
        assert '中等任务' in content or '中等' in content
        assert '复杂任务' in content or '复杂' in content

    @pytest.mark.parametrize('subdir', ROLE_DIRS)
    def test_has_methodology_mapping(self, subdir):
        """包含领域方法论映射"""
        content = read_file(f'{subdir}/SKILL.md')
        assert '领域方法论映射' in content or '方法论映射' in content, \
            f'{subdir} 缺少领域方法论映射'

    @pytest.mark.parametrize('subdir', ROLE_DIRS)
    def test_methodology_references_knowledge(self, subdir):
        """方法论映射引用 knowledge/ 文件"""
        content = read_file(f'{subdir}/SKILL.md')
        assert 'knowledge/' in content or '.md' in content, \
            f'{subdir} 方法论映射未引用 knowledge/ 文件'

    @pytest.mark.parametrize('subdir', ROLE_DIRS)
    def test_has_degradation_strategy(self, subdir):
        """包含降级策略"""
        content = read_file(f'{subdir}/SKILL.md')
        assert '降级策略' in content or '降级' in content, \
            f'{subdir} 缺少降级策略'


# ============================================================
# 6. 红线合规 — 不产出具体方案
# ============================================================

class TestRedLineCompliance:
    """验证所有角色 SKILL 不包含直接方案输出"""

    @pytest.mark.parametrize('subdir', ROLE_DIRS)
    def test_no_ddl(self, subdir):
        """不包含 DDL 语句"""
        content = read_file(f'{subdir}/SKILL.md')
        assert 'CREATE TABLE' not in content, f'{subdir} 包含 CREATE TABLE'
        assert 'ALTER TABLE' not in content, f'{subdir} 包含 ALTER TABLE'

    @pytest.mark.parametrize('subdir', ROLE_DIRS)
    def test_no_api_spec(self, subdir):
        """不包含具体 API 路径定义"""
        content = read_file(f'{subdir}/SKILL.md')
        # 检查典型的 API 路径模式（排除 knowledge/ 引用路径）
        api_patterns = re.findall(r'(?:GET|POST|PUT|DELETE)\s+/api/', content)
        assert len(api_patterns) == 0, f'{subdir} 包含 API 路径定义: {api_patterns}'

    @pytest.mark.parametrize('subdir', ROLE_DIRS)
    def test_no_code_blocks_with_implementation(self, subdir):
        """代码块不包含实际实现代码（允许流程伪代码和命令行示例）"""
        content = read_file(f'{subdir}/SKILL.md')
        # 检查常见的实现代码模式
        impl_patterns = [
            r'public class\s+\w+',
            r'def\s+\w+\(self',
            r'function\s+\w+\(',
            r'import\s+\{.*\}\s+from',
        ]
        for pattern in impl_patterns:
            matches = re.findall(pattern, content)
            assert len(matches) == 0, \
                f'{subdir} 包含实现代码: {pattern} -> {matches}'


# ============================================================
# 7. 知识库完整性
# ============================================================

class TestKnowledgeBase:
    """知识库文件和索引一致性"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.index_content = read_file('knowledge/INDEX.md')
        self.knowledge_dir = os.path.join(BASE_DIR, 'knowledge')

    def test_core_theory_files_exist(self):
        """核心理论文件（00-09）存在"""
        expected_prefixes = ['00-', '01-', '02-', '03-', '04-', '05-', '06-', '07-', '08-', '09-']
        files = os.listdir(self.knowledge_dir)
        for prefix in expected_prefixes:
            matching = [f for f in files if f.startswith(prefix)]
            assert len(matching) > 0, f'缺少 {prefix}* 文件'

    def test_functional_tool_files_exist(self):
        """功能工具文件（fm-*）存在"""
        files = os.listdir(self.knowledge_dir)
        fm_files = [f for f in files if f.startswith('fm-')]
        assert len(fm_files) >= 4, f'功能工具文件不足: {len(fm_files)} 个'

    def test_index_references_valid_files(self):
        """INDEX.md 引用的文件实际存在"""
        # 提取所有 `filename.md` 引用
        refs = re.findall(r'`([^`]*\.md)`', self.index_content)
        for ref in refs:
            # 跳过模板引用（common/）
            if ref.startswith('common/'):
                continue
            # 构造路径
            if ref.startswith('masters/'):
                path = os.path.join(self.knowledge_dir, ref)
            elif ref.startswith('knowledge/'):
                path = os.path.join(BASE_DIR, ref)
            else:
                path = os.path.join(self.knowledge_dir, ref)
            assert os.path.isfile(path), f'INDEX.md 引用的文件不存在: {ref}'


# ============================================================
# 8. Init 版本检查
# ============================================================

class TestInitVersionCheck:
    """init/SKILL.md 包含版本检查逻辑"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.content = read_file('init/SKILL.md')

    def test_has_version_check_layer(self):
        assert 'Layer 0' in self.content or '版本检查' in self.content

    def test_version_check_is_silent(self):
        assert '静默' in self.content

    def test_has_timeout(self):
        assert 'max-time' in self.content or '超时' in self.content or '3' in self.content

    def test_has_github_url(self):
        assert 'github' in self.content.lower() or 'raw.githubusercontent' in self.content


# ============================================================
# 9. 跨文件引用一致性
# ============================================================

class TestCrossReferences:
    """文件之间的引用一致性"""

    def test_main_references_all_roles(self):
        content = read_file('SKILL.md')
        for role in ROLE_DIRS:
            assert f'ai-coach-{role}' in content, f'主入口未引用 ai-coach-{role}'

    def test_roles_reference_template(self):
        for role in ROLE_DIRS:
            content = read_file(f'{role}/SKILL.md')
            assert 'COACH_TEMPLATE' in content, f'{role} 未引用 COACH_TEMPLATE'

    def test_roles_reference_knowledge_files(self):
        """每个角色至少引用 3 个 knowledge/ 文件"""
        for role in ROLE_DIRS:
            content = read_file(f'{role}/SKILL.md')
            refs = re.findall(r'`[\w-]+\.md`', content)
            assert len(refs) >= 3, f'{role} 引用 knowledge/ 文件不足: {len(refs)} 个'
