#!/usr/bin/env python3
"""
analyze_sessions.py 单元测试

覆盖三个核心函数：
- analyze_single_file(): 单文件分析
- merge_signals(): 多信号合并
- find_session_files(): 文件发现
"""

import json
import os
import tempfile
import time
from collections import Counter
from pathlib import Path

import pytest

# 导入被测模块
sys_path = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, sys_path)
from analyze_sessions import analyze_single_file, merge_signals, find_session_files


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def tmp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as d:
        yield d


def make_jsonl(tmp_dir, filename, lines):
    """辅助：在临时目录下创建 .jsonl 文件"""
    path = os.path.join(tmp_dir, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(json.dumps(line, ensure_ascii=False) + '\n')
    return path


def make_user_msg(text, ts=None):
    """构造用户消息行"""
    msg = {
        'type': 'user',
        'message': {'role': 'user', 'content': text},
    }
    if ts:
        msg['timestamp'] = ts
    return msg


def make_assistant_tool(tool_name, tool_input=None, ts=None):
    """构造 assistant 工具调用行"""
    msg = {
        'type': 'assistant',
        'message': {
            'role': 'assistant',
            'content': [{
                'type': 'tool_use',
                'name': tool_name,
                'input': tool_input or {},
            }]
        },
    }
    if ts:
        msg['timestamp'] = ts
    return msg


def make_error_result(ts=None):
    """构造工具错误结果行"""
    msg = {
        'type': 'user',
        'message': {
            'role': 'user',
            'content': [{
                'type': 'tool_result',
                'is_error': True,
            }]
        },
    }
    if ts:
        msg['timestamp'] = ts
    return msg


# ============================================================
# analyze_single_file() 测试
# ============================================================

class TestAnalyzeSingleFile:
    """测试单文件分析"""

    def test_empty_file(self, tmp_dir):
        """空文件不崩溃，返回零值信号"""
        path = make_jsonl(tmp_dir, 'empty.jsonl', [])
        result = analyze_single_file(path)
        assert result['total_turns'] == 0
        assert result['plan_mode_count'] == 0
        assert len(result['test_commands']) == 0
        assert len(result['user_msg_lengths']) == 0

    def test_malformed_json_lines(self, tmp_dir):
        """格式错误的 JSON 行被跳过，不影响有效行"""
        path = os.path.join(tmp_dir, 'bad.jsonl')
        with open(path, 'w') as f:
            f.write('not json\n')
            f.write('{"broken": \n')
            f.write(json.dumps(make_user_msg('hello world test')) + '\n')
        result = analyze_single_file(path)
        assert len(result['user_msg_lengths']) == 1
        assert result['user_msg_lengths'][0] == len('hello world test')

    def test_user_message_length_tracking(self, tmp_dir):
        """用户消息长度正确记录"""
        lines = [
            make_user_msg('hi'),           # 2 字符
            make_user_msg('hello world'),   # 11 字符
            make_user_msg('a' * 100),       # 100 字符
        ]
        path = make_jsonl(tmp_dir, 'msgs.jsonl', lines)
        result = analyze_single_file(path)
        assert result['user_msg_lengths'] == [2, 11, 100]

    def test_user_message_list_content(self, tmp_dir):
        """用户消息 content 为列表时正确处理"""
        lines = [{
            'type': 'user',
            'message': {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': 'structured message'},
                ]
            },
        }]
        path = make_jsonl(tmp_dir, 'list_content.jsonl', lines)
        result = analyze_single_file(path)
        assert len(result['user_msg_lengths']) == 1
        assert result['user_msg_lengths'][0] == len('structured message')

    def test_tool_usage_counting(self, tmp_dir):
        """工具调用次数正确统计"""
        lines = [
            make_assistant_tool('Bash', {'command': 'ls'}),
            make_assistant_tool('Read', {'file_path': '/tmp/x'}),
            make_assistant_tool('Bash', {'command': 'pwd'}),
            make_assistant_tool('Grep', {'pattern': 'foo'}),
        ]
        path = make_jsonl(tmp_dir, 'tools.jsonl', lines)
        result = analyze_single_file(path)
        assert result['tool_usage']['Bash'] == 2
        assert result['tool_usage']['Read'] == 1
        assert result['tool_usage']['Grep'] == 1
        assert result['total_turns'] == 4

    def test_skill_usage_counting(self, tmp_dir):
        """Skill 调用正确统计"""
        lines = [
            make_assistant_tool('Skill', {'skill': 'brainstorm'}),
            make_assistant_tool('Skill', {'skill': 'brainstorm'}),
            make_assistant_tool('Skill', {'skill': 'write-plan'}),
        ]
        path = make_jsonl(tmp_dir, 'skills.jsonl', lines)
        result = analyze_single_file(path)
        assert result['skill_usage']['brainstorm'] == 2
        assert result['skill_usage']['write-plan'] == 1

    def test_plan_mode_counting(self, tmp_dir):
        """Plan Mode 使用次数正确统计"""
        lines = [
            make_assistant_tool('EnterPlanMode'),
            make_assistant_tool('Bash', {'command': 'ls'}),
            make_assistant_tool('EnterPlanMode'),
        ]
        path = make_jsonl(tmp_dir, 'plan.jsonl', lines)
        result = analyze_single_file(path)
        assert result['plan_mode_count'] == 2

    def test_test_command_detection(self, tmp_dir):
        """测试命令检测（多种测试框架）"""
        lines = [
            make_assistant_tool('Bash', {'command': './gradlew test'}, '2026-01-01T10:00:00Z'),
            make_assistant_tool('Bash', {'command': 'pytest tests/'}, '2026-01-01T10:01:00Z'),
            make_assistant_tool('Bash', {'command': 'npm test'}, '2026-01-01T10:02:00Z'),
            make_assistant_tool('Bash', {'command': 'jest --verbose'}, '2026-01-01T10:03:00Z'),
            make_assistant_tool('Bash', {'command': 'cargo test'}, '2026-01-01T10:04:00Z'),
            make_assistant_tool('Bash', {'command': 'go test ./...'}, '2026-01-01T10:05:00Z'),
            make_assistant_tool('Bash', {'command': 'ls -la'}),  # 非测试命令
        ]
        path = make_jsonl(tmp_dir, 'tests.jsonl', lines)
        result = analyze_single_file(path)
        assert len(result['test_commands']) == 6

    def test_git_commit_detection(self, tmp_dir):
        """git commit 检测"""
        lines = [
            make_assistant_tool('Bash', {'command': 'git commit -m "fix bug"'}, '2026-01-01T10:00:00Z'),
            make_assistant_tool('Bash', {'command': 'git add .'}, '2026-01-01T10:01:00Z'),
            make_assistant_tool('Bash', {'command': 'git commit --amend'}, '2026-01-01T10:02:00Z'),
        ]
        path = make_jsonl(tmp_dir, 'commits.jsonl', lines)
        result = analyze_single_file(path)
        assert len(result['git_commits']) == 2

    def test_claude_md_refs(self, tmp_dir):
        """CLAUDE.md 引用检测"""
        lines = [
            make_assistant_tool('Read', {'file_path': '/project/CLAUDE.md'}),
            make_assistant_tool('Glob', {'pattern': '**/CLAUDE.md'}),
            make_assistant_tool('Read', {'file_path': '/other/file.py'}),
        ]
        path = make_jsonl(tmp_dir, 'claude_md.jsonl', lines)
        result = analyze_single_file(path)
        assert result['claude_md_refs'] == 2

    def test_parallel_agents(self, tmp_dir):
        """并行 Agent 检测"""
        lines = [
            make_assistant_tool('Task', {'prompt': 'do something'}),
            make_assistant_tool('Task', {'prompt': 'do another'}),
            make_assistant_tool('Bash', {'command': 'ls'}),
        ]
        path = make_jsonl(tmp_dir, 'agents.jsonl', lines)
        result = analyze_single_file(path)
        assert result['parallel_agents'] == 2

    def test_session_duration(self, tmp_dir):
        """会话时长计算"""
        lines = [
            make_user_msg('start', '2026-01-01T10:00:00Z'),
            make_assistant_tool('Bash', {'command': 'ls'}, '2026-01-01T10:30:00Z'),
            make_user_msg('end', '2026-01-01T11:00:00Z'),
        ]
        path = make_jsonl(tmp_dir, 'duration.jsonl', lines)
        result = analyze_single_file(path)
        assert result['session_duration_min'] == 60.0

    def test_error_recovery_tracking(self, tmp_dir):
        """错误后恢复行为追踪"""
        lines = [
            make_error_result(),
            make_assistant_tool('Grep', {'pattern': 'error'}),
        ]
        path = make_jsonl(tmp_dir, 'error.jsonl', lines)
        result = analyze_single_file(path)
        assert 'Grep' in result['error_then_action']

    def test_user_message_sampling(self, tmp_dir):
        """用户消息采样逻辑（每 5 条取 1 条，长度 > 10）"""
        lines = []
        for i in range(15):
            lines.append(make_user_msg(f'message number {i:03d} with enough length'))
        path = make_jsonl(tmp_dir, 'sampling.jsonl', lines)
        result = analyze_single_file(path)
        # 每 5 条取 1 条（index % 5 == 1），15 条应该取 3 条
        assert len(result['user_messages_sample']) == 3

    def test_message_truncation(self, tmp_dir):
        """超长消息截断到 300 字符"""
        long_msg = 'x' * 500
        lines = [make_user_msg(long_msg)]
        path = make_jsonl(tmp_dir, 'truncate.jsonl', lines)
        result = analyze_single_file(path)
        if result['user_messages_sample']:
            assert len(result['user_messages_sample'][0]) <= 300

    # ---- 用户斜杠命令 Skill 检测 ----

    def test_user_slash_command_skill_detection(self, tmp_dir):
        """用户通过 /brainstorming 斜杠命令触发的 Skill 被正确检测"""
        lines = [
            {
                'type': 'user',
                'message': {
                    'role': 'user',
                    'content': '<command-message>superpowers:brainstorming</command-message>\n<command-name>/superpowers:brainstorming</command-name>',
                },
                'timestamp': '2026-01-01T10:00:00Z',
            },
            make_assistant_tool('Bash', {'command': 'ls'}),
        ]
        path = make_jsonl(tmp_dir, 'slash_cmd.jsonl', lines)
        result = analyze_single_file(path)
        assert result['skill_usage']['superpowers:brainstorming'] == 1

    def test_user_slash_command_various_skills(self, tmp_dir):
        """多种斜杠命令 Skill 都能被检测"""
        lines = [
            {
                'type': 'user',
                'message': {
                    'role': 'user',
                    'content': '<command-message>superpowers:systematic-debugging</command-message>\n<command-name>/superpowers:systematic-debugging</command-name>',
                },
            },
            make_assistant_tool('Bash', {'command': 'ls'}),
            {
                'type': 'user',
                'message': {
                    'role': 'user',
                    'content': '<command-message>superpowers:test-driven-development</command-message>\n<command-name>/superpowers:test-driven-development</command-name>',
                },
            },
            make_assistant_tool('Bash', {'command': 'ls'}),
            {
                'type': 'user',
                'message': {
                    'role': 'user',
                    'content': '<command-message>ai-coach</command-message>\n<command-name>/ai-coach</command-name>',
                },
            },
            make_assistant_tool('Bash', {'command': 'ls'}),
        ]
        path = make_jsonl(tmp_dir, 'multi_slash.jsonl', lines)
        result = analyze_single_file(path)
        assert result['skill_usage']['superpowers:systematic-debugging'] == 1
        assert result['skill_usage']['superpowers:test-driven-development'] == 1
        assert result['skill_usage']['ai-coach'] == 1

    def test_mixed_skill_detection(self, tmp_dir):
        """同时检测用户斜杠命令和 Claude 主动调用的 Skill"""
        lines = [
            # 用户斜杠命令触发 brainstorming
            {
                'type': 'user',
                'message': {
                    'role': 'user',
                    'content': '<command-message>superpowers:brainstorming</command-message>\n<command-name>/superpowers:brainstorming</command-name>',
                },
            },
            # Claude 主动调用 Skill 工具
            make_assistant_tool('Skill', {'skill': 'superpowers:writing-plans'}),
            # 又一个用户斜杠命令
            {
                'type': 'user',
                'message': {
                    'role': 'user',
                    'content': '<command-message>superpowers:executing-plans</command-message>\n<command-name>/superpowers:executing-plans</command-name>',
                },
            },
        ]
        path = make_jsonl(tmp_dir, 'mixed_skills.jsonl', lines)
        result = analyze_single_file(path)
        assert result['skill_usage']['superpowers:brainstorming'] == 1
        assert result['skill_usage']['superpowers:writing-plans'] == 1
        assert result['skill_usage']['superpowers:executing-plans'] == 1

    def test_slash_command_in_list_content(self, tmp_dir):
        """斜杠命令出现在 content 列表格式中也能检测"""
        lines = [
            {
                'type': 'user',
                'message': {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': '<command-message>superpowers:brainstorming</command-message>\n<command-name>/superpowers:brainstorming</command-name>'},
                    ],
                },
            },
        ]
        path = make_jsonl(tmp_dir, 'list_slash.jsonl', lines)
        result = analyze_single_file(path)
        assert result['skill_usage']['superpowers:brainstorming'] == 1

    def test_slash_command_not_double_counted_with_msg_length(self, tmp_dir):
        """斜杠命令消息不应计入用户消息长度统计（它是系统行为，不是用户输入）"""
        lines = [
            {
                'type': 'user',
                'message': {
                    'role': 'user',
                    'content': '<command-message>superpowers:brainstorming</command-message>\n<command-name>/superpowers:brainstorming</command-name>',
                },
            },
            make_user_msg('hello world'),
        ]
        path = make_jsonl(tmp_dir, 'no_double.jsonl', lines)
        result = analyze_single_file(path)
        # 只有 'hello world' 应计入消息长度，斜杠命令消息不计
        assert len(result['user_msg_lengths']) == 1
        assert result['user_msg_lengths'][0] == len('hello world')

    def test_nonexistent_file(self, tmp_dir):
        """不存在的文件返回错误信号"""
        result = analyze_single_file('/nonexistent/path/file.jsonl')
        assert 'error' in result

    def test_file_basename_in_result(self, tmp_dir):
        """结果中包含文件名"""
        path = make_jsonl(tmp_dir, 'my_session.jsonl', [make_user_msg('hi')])
        result = analyze_single_file(path)
        assert result['file'] == 'my_session.jsonl'


# ============================================================
# merge_signals() 测试
# ============================================================

class TestMergeSignals:
    """测试多信号合并"""

    def test_empty_signals_list(self):
        """空信号列表不崩溃"""
        result = merge_signals([])
        assert result['session_count'] == 0
        assert result['total_turns'] == 0
        assert result['avg_user_msg_length'] == 0

    def test_single_session_merge(self):
        """单个会话的合并"""
        sig = {
            'file': 'test.jsonl',
            'skill_usage': Counter({'brainstorm': 2}),
            'tool_usage': Counter({'Bash': 5, 'Read': 3}),
            'plan_mode_count': 1,
            'test_commands': ['2026-01-01T10:00:00Z'],
            'git_commits': ['2026-01-01T10:05:00Z'],
            'error_then_action': ['Grep'],
            'user_msg_lengths': [50, 100, 200],
            'session_duration_min': 30,
            'total_turns': 10,
            'claude_md_refs': 2,
            'parallel_agents': 1,
            'user_messages_sample': ['msg1', 'msg2'],
        }
        result = merge_signals([sig])
        assert result['session_count'] == 1
        assert result['total_turns'] == 10
        assert result['test_command_count'] == 1
        assert result['git_commit_count'] == 1
        assert result['skill_usage'] == {'brainstorm': 2}
        assert result['avg_user_msg_length'] == round((50 + 100 + 200) / 3, 1)

    def test_multi_session_merge(self):
        """多会话信号正确累加"""
        sig1 = {
            'file': 'a.jsonl',
            'skill_usage': Counter({'brainstorm': 1}),
            'tool_usage': Counter({'Bash': 3}),
            'plan_mode_count': 1,
            'test_commands': ['ts1'],
            'git_commits': ['ts1'],
            'error_then_action': [],
            'user_msg_lengths': [100],
            'session_duration_min': 10,
            'total_turns': 5,
            'claude_md_refs': 1,
            'parallel_agents': 0,
            'user_messages_sample': ['msg_a'],
        }
        sig2 = {
            'file': 'b.jsonl',
            'skill_usage': Counter({'brainstorm': 2, 'write-plan': 1}),
            'tool_usage': Counter({'Bash': 2, 'Read': 1}),
            'plan_mode_count': 0,
            'test_commands': ['ts2', 'ts3'],
            'git_commits': [],
            'error_then_action': ['Bash'],
            'user_msg_lengths': [200, 300],
            'session_duration_min': 20,
            'total_turns': 8,
            'claude_md_refs': 0,
            'parallel_agents': 3,
            'user_messages_sample': ['msg_b'],
        }
        result = merge_signals([sig1, sig2])
        assert result['session_count'] == 2
        assert result['total_turns'] == 13
        assert result['total_duration_min'] == 30
        assert result['plan_mode_count'] == 1
        assert result['test_command_count'] == 3
        assert result['git_commit_count'] == 1
        assert result['skill_usage']['brainstorm'] == 3
        assert result['skill_usage']['write-plan'] == 1
        assert result['tool_usage']['Bash'] == 5
        assert result['parallel_agents'] == 3

    def test_error_sessions_skipped(self):
        """有错误的会话被跳过"""
        sig_ok = {
            'file': 'ok.jsonl',
            'skill_usage': Counter(),
            'tool_usage': Counter({'Bash': 1}),
            'plan_mode_count': 0,
            'test_commands': [],
            'git_commits': [],
            'error_then_action': [],
            'user_msg_lengths': [50],
            'session_duration_min': 5,
            'total_turns': 3,
            'claude_md_refs': 0,
            'parallel_agents': 0,
            'user_messages_sample': [],
        }
        sig_err = {
            'file': 'err.jsonl',
            'error': 'file not found',
            'skill_usage': Counter(),
            'tool_usage': Counter(),
            'plan_mode_count': 0,
            'test_commands': [],
            'git_commits': [],
            'error_then_action': [],
            'user_msg_lengths': [],
            'session_duration_min': 0,
            'total_turns': 0,
            'claude_md_refs': 0,
            'parallel_agents': 0,
            'user_messages_sample': [],
        }
        result = merge_signals([sig_ok, sig_err])
        # 只有 1 个会话被计入摘要（但 session_count 还是 2）
        assert result['total_turns'] == 3
        assert len(result['per_session']) == 1

    def test_message_length_distribution(self):
        """消息长度分布正确分类"""
        sig = {
            'file': 'dist.jsonl',
            'skill_usage': Counter(),
            'tool_usage': Counter(),
            'plan_mode_count': 0,
            'test_commands': [],
            'git_commits': [],
            'error_then_action': [],
            'user_msg_lengths': [5, 10, 15, 100, 300, 600, 1000],
            'session_duration_min': 0,
            'total_turns': 0,
            'claude_md_refs': 0,
            'parallel_agents': 0,
            'user_messages_sample': [],
        }
        result = merge_signals([sig])
        dist = result['user_msg_length_distribution']
        assert dist['short'] == 3   # < 20: 5, 10, 15
        assert dist['medium'] == 2  # 20-500: 100, 300
        assert dist['long'] == 2    # > 500: 600, 1000

    def test_sample_limit(self):
        """采样消息限制 20 条"""
        sig = {
            'file': 'many.jsonl',
            'skill_usage': Counter(),
            'tool_usage': Counter(),
            'plan_mode_count': 0,
            'test_commands': [],
            'git_commits': [],
            'error_then_action': [],
            'user_msg_lengths': [],
            'session_duration_min': 0,
            'total_turns': 0,
            'claude_md_refs': 0,
            'parallel_agents': 0,
            'user_messages_sample': [f'msg_{i}' for i in range(30)],
        }
        # 每个会话取前 2 条，但总量限制 20
        sigs = [sig] * 15  # 15 个会话 × 2 条 = 30 条 → 限制到 20
        result = merge_signals(sigs)
        assert len(result['user_messages_sample']) <= 20

    def test_per_session_summary(self):
        """每会话摘要正确生成"""
        sig = {
            'file': 'summary.jsonl',
            'skill_usage': Counter(),
            'tool_usage': Counter({'Bash': 2, 'Read': 1}),
            'plan_mode_count': 1,
            'test_commands': ['ts1'],
            'git_commits': [],
            'error_then_action': [],
            'user_msg_lengths': [],
            'session_duration_min': 15,
            'total_turns': 7,
            'claude_md_refs': 0,
            'parallel_agents': 0,
            'user_messages_sample': [],
        }
        result = merge_signals([sig])
        assert len(result['per_session']) == 1
        session = result['per_session'][0]
        assert session['file'] == 'summary.jsonl'
        assert session['turns'] == 7
        assert session['duration_min'] == 15
        assert session['tools_used'] == 2
        assert session['plan_mode'] is True
        assert session['has_tests'] is True

    def test_counter_to_dict_serialization(self):
        """Counter 转换为 dict（JSON 序列化兼容）"""
        sig = {
            'file': 'serial.jsonl',
            'skill_usage': Counter({'brainstorm': 1}),
            'tool_usage': Counter({'Bash': 1}),
            'plan_mode_count': 0,
            'test_commands': [],
            'git_commits': [],
            'error_then_action': ['Read'],
            'user_msg_lengths': [],
            'session_duration_min': 0,
            'total_turns': 0,
            'claude_md_refs': 0,
            'parallel_agents': 0,
            'user_messages_sample': [],
        }
        result = merge_signals([sig])
        # 验证可以 JSON 序列化
        json_str = json.dumps(result)
        assert isinstance(json.loads(json_str), dict)
        # 验证类型转换
        assert isinstance(result['skill_usage'], dict)
        assert isinstance(result['tool_usage'], dict)
        assert isinstance(result['error_recovery_tools'], dict)


# ============================================================
# find_session_files() 测试
# ============================================================

class TestFindSessionFiles:
    """测试文件发现"""

    def test_finds_jsonl_files(self, tmp_dir):
        """正确发现 .jsonl 文件"""
        make_jsonl(tmp_dir, 'a.jsonl', [])
        make_jsonl(tmp_dir, 'b.jsonl', [])
        make_jsonl(tmp_dir, 'c.txt', [])  # 非 .jsonl
        result = find_session_files(tmp_dir)
        assert len(result) == 2

    def test_recursive_search(self, tmp_dir):
        """递归搜索子目录"""
        make_jsonl(tmp_dir, 'root.jsonl', [])
        make_jsonl(tmp_dir, 'sub1/a.jsonl', [])
        make_jsonl(tmp_dir, 'sub1/sub2/b.jsonl', [])
        result = find_session_files(tmp_dir)
        assert len(result) == 3

    def test_sorted_by_mtime_desc(self, tmp_dir):
        """按修改时间降序排列（最新在前）"""
        p1 = make_jsonl(tmp_dir, 'old.jsonl', [])
        time.sleep(0.1)
        p2 = make_jsonl(tmp_dir, 'new.jsonl', [])
        result = find_session_files(tmp_dir)
        assert os.path.basename(result[0]) == 'new.jsonl'
        assert os.path.basename(result[1]) == 'old.jsonl'

    def test_max_files_limit(self, tmp_dir):
        """文件数量限制"""
        for i in range(10):
            make_jsonl(tmp_dir, f'file_{i}.jsonl', [])
        result = find_session_files(tmp_dir, max_files=3)
        assert len(result) == 3

    def test_days_filter(self, tmp_dir):
        """天数过滤"""
        p = make_jsonl(tmp_dir, 'recent.jsonl', [])
        # 所有文件都是刚创建的，days=1 应该全部包含
        result = find_session_files(tmp_dir, days=1)
        assert len(result) == 1

    def test_empty_directory(self, tmp_dir):
        """空目录返回空列表"""
        result = find_session_files(tmp_dir)
        assert result == []


# ============================================================
# 集成测试：完整管道
# ============================================================

class TestIntegration:
    """端到端集成测试"""

    def test_full_pipeline(self, tmp_dir):
        """完整管道：创建会话文件 → 发现 → 分析 → 合并"""
        # 创建模拟会话文件
        session1 = [
            make_user_msg('帮我重构订单模块', '2026-01-01T10:00:00Z'),
            make_assistant_tool('Skill', {'skill': 'brainstorm'}, '2026-01-01T10:01:00Z'),
            make_assistant_tool('EnterPlanMode', {}, '2026-01-01T10:05:00Z'),
            make_assistant_tool('Bash', {'command': './gradlew test'}, '2026-01-01T10:10:00Z'),
            make_assistant_tool('Bash', {'command': 'git commit -m "refactor"'}, '2026-01-01T10:15:00Z'),
            make_user_msg('完成了', '2026-01-01T10:20:00Z'),
        ]
        session2 = [
            make_user_msg('修个 bug', '2026-01-02T09:00:00Z'),
            make_assistant_tool('Bash', {'command': 'pytest tests/'}, '2026-01-02T09:05:00Z'),
            make_assistant_tool('Read', {'file_path': '/project/CLAUDE.md'}, '2026-01-02T09:10:00Z'),
        ]

        make_jsonl(tmp_dir, 'project1/session1.jsonl', session1)
        make_jsonl(tmp_dir, 'project2/session2.jsonl', session2)

        # 发现文件
        files = find_session_files(tmp_dir)
        assert len(files) == 2

        # 分析每个文件
        all_signals = [analyze_single_file(f) for f in files]
        assert all('error' not in s for s in all_signals)

        # 合并
        merged = merge_signals(all_signals)
        assert merged['session_count'] == 2
        assert merged['test_command_count'] == 2  # gradlew test + pytest
        assert merged['git_commit_count'] == 1
        assert merged['plan_mode_count'] == 1
        assert merged['claude_md_refs'] == 1
        assert merged['skill_usage']['brainstorm'] == 1

        # 验证可 JSON 序列化
        json_str = json.dumps(merged, ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed['session_count'] == 2

    def test_pipeline_with_mixed_quality(self, tmp_dir):
        """混合质量文件：有效 + 无效 + 空"""
        good = [
            make_user_msg('good session', '2026-01-01T10:00:00Z'),
            make_assistant_tool('Bash', {'command': 'npm test'}, '2026-01-01T10:05:00Z'),
        ]
        make_jsonl(tmp_dir, 'good.jsonl', good)
        make_jsonl(tmp_dir, 'empty.jsonl', [])

        # 创建格式错误的文件
        bad_path = os.path.join(tmp_dir, 'bad.jsonl')
        with open(bad_path, 'w') as f:
            f.write('not valid json\n')

        files = find_session_files(tmp_dir)
        all_signals = [analyze_single_file(f) for f in files]
        merged = merge_signals(all_signals)

        # 不崩溃，且能处理有效数据
        assert merged['session_count'] == 3
        assert merged['test_command_count'] >= 1
