#!/usr/bin/env python3
"""
AI Coach Evaluate - Session Analyzer
批量分析 Claude Code 会话文件(.jsonl)，提取行为信号用于八维评分。

用法:
  python3 analyze_sessions.py <file1.jsonl> [file2.jsonl ...]
  python3 analyze_sessions.py --dir <directory> [--days 7] [--max 30]

输出: JSON 格式的汇总信号数据（stdout）
"""

import json
import sys
import re
import os
import argparse
import glob as glob_module
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def read_role_from_memory():
    """
    扫描 ~/.claude/projects/*/memory/MEMORY.md 文件，
    查找 'AI教练角色: ' 开头的行，提取角色名。
    如果找不到，返回空字符串。
    """
    home = os.path.expanduser("~")
    pattern = os.path.join(home, ".claude", "projects", "*", "memory", "MEMORY.md")
    memory_files = glob_module.glob(pattern)

    for mf in memory_files:
        try:
            with open(mf, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('AI教练角色: ') or line.startswith('AI教练角色:'):
                        # 提取冒号后面的角色名
                        role = line.split(':', 1)[1].strip()
                        if role:
                            return role
        except (IOError, OSError):
            continue

    return ""


def analyze_single_file(filepath):
    """分析单个 .jsonl 文件，返回信号字典"""
    signals = {
        'file': os.path.basename(filepath),
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
        'user_messages_sample': [],  # 采样用户消息（用于定性评估）
        # 角色信号字段
        'prd_references': 0,
        'prototype_outputs': 0,
        'test_report_outputs': 0,
        'mock_api_usage': 0,
        'screenshot_count': 0,
        'device_test_count': 0,
        'verification_skill_usage': 0,
    }

    prev_was_error = False
    first_ts = None
    last_ts = None
    assistant_count = 0
    sample_interval = 5  # 每 5 条用户消息采样 1 条

    user_msg_index = 0

    # 用于检测用户斜杠命令触发的 Skill
    _command_msg_re = re.compile(r'<command-message>(.*?)</command-message>')

    # 角色信号关键词正则（预编译提升性能）
    _prd_re = re.compile(r'PRD|需求文档|产品需求', re.IGNORECASE)
    _prototype_re = re.compile(r'prototype|原型|html\s*原型', re.IGNORECASE)
    _test_report_re = re.compile(r'测试报告|test\s*report|TEST-REPORT', re.IGNORECASE)
    _mock_re = re.compile(r'mock|Mock|模拟数据')
    _screenshot_re = re.compile(r'screenshot|截图|take_screenshot', re.IGNORECASE)
    _device_test_re = re.compile(r'设备测试|device|兼容性测试', re.IGNORECASE)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue

                ts = obj.get('timestamp')
                if ts and not first_ts:
                    first_ts = ts
                if ts:
                    last_ts = ts

                msg = obj.get('message', {})
                content = msg.get('content', [])
                obj_type = obj.get('type', '')

                # 统计 assistant 消息轮次
                if obj_type == 'assistant':
                    assistant_count += 1

                # 用户消息分析
                if obj_type == 'user' and msg.get('role') == 'user':
                    # 收集所有文本片段，用于统一检测斜杠命令
                    _user_texts = []
                    if isinstance(content, str):
                        _user_texts.append(content)
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                if item.get('type') == 'text':
                                    _user_texts.append(item['text'])
                                elif item.get('type') == 'tool_result':
                                    if item.get('is_error'):
                                        prev_was_error = True

                    # 检测用户斜杠命令触发的 Skill（如 /brainstorming）
                    _is_slash_command = False
                    for _text in _user_texts:
                        _cmd_match = _command_msg_re.search(_text)
                        if _cmd_match:
                            skill_name = _cmd_match.group(1)
                            signals['skill_usage'][skill_name] += 1
                            _is_slash_command = True

                    # 斜杠命令消息不计入用户消息长度统计（系统行为，非用户输入）
                    if not _is_slash_command:
                        for _text in _user_texts:
                            signals['user_msg_lengths'].append(len(_text))
                            user_msg_index += 1
                            if user_msg_index % sample_interval == 1 and len(_text) > 10:
                                signals['user_messages_sample'].append(
                                    _text[:300]
                                )

                    # 用户消息中的角色信号关键词计数
                    for _text in _user_texts:
                        signals['prd_references'] += len(_prd_re.findall(_text))
                        signals['prototype_outputs'] += len(_prototype_re.findall(_text))
                        signals['test_report_outputs'] += len(_test_report_re.findall(_text))
                        signals['mock_api_usage'] += len(_mock_re.findall(_text))
                        signals['screenshot_count'] += len(_screenshot_re.findall(_text))
                        signals['device_test_count'] += len(_device_test_re.findall(_text))

                # Assistant 消息 - 工具使用分析
                elif obj_type == 'assistant':
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get('type') == 'tool_use':
                                tool_name = item.get('name', '')
                                signals['tool_usage'][tool_name] += 1

                                if tool_name == 'Skill':
                                    skill = item.get('input', {}).get('skill', '')
                                    signals['skill_usage'][skill] += 1
                                    # 检测 verification-before-completion 使用
                                    if 'verification-before-completion' in skill:
                                        signals['verification_skill_usage'] += 1

                                if tool_name == 'EnterPlanMode':
                                    signals['plan_mode_count'] += 1

                                if tool_name == 'Bash':
                                    cmd = item.get('input', {}).get('command', '')
                                    if re.search(r'(gradlew\s+test|pytest|npm\s+test|jest|cargo\s+test|go\s+test)', cmd):
                                        signals['test_commands'].append(ts)
                                    if 'git commit' in cmd:
                                        signals['git_commits'].append(ts)

                                if tool_name == 'Task':
                                    signals['parallel_agents'] += 1

                                if tool_name in ('Read', 'Glob', 'Grep'):
                                    inp = str(item.get('input', {}))
                                    if 'CLAUDE.md' in inp or 'claude.md' in inp.lower():
                                        signals['claude_md_refs'] += 1

                                # Assistant 消息中的角色信号计数（工具输入）
                                inp_str = json.dumps(item.get('input', {}), ensure_ascii=False)
                                signals['prototype_outputs'] += len(_prototype_re.findall(inp_str))
                                signals['test_report_outputs'] += len(_test_report_re.findall(inp_str))
                                signals['mock_api_usage'] += len(_mock_re.findall(inp_str))
                                signals['screenshot_count'] += len(_screenshot_re.findall(inp_str))
                                signals['device_test_count'] += len(_device_test_re.findall(inp_str))

                                # 截图工具直接计数
                                if tool_name in ('mcp__playwright__browser_take_screenshot',):
                                    signals['screenshot_count'] += 1

                                if prev_was_error:
                                    signals['error_then_action'].append(tool_name)
                                    prev_was_error = False

        signals['total_turns'] = assistant_count

        # 计算会话时长
        if first_ts and last_ts:
            try:
                t1 = datetime.fromisoformat(first_ts.replace('Z', '+00:00'))
                t2 = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
                signals['session_duration_min'] = max(0, round((t2 - t1).total_seconds() / 60, 1))
            except (ValueError, TypeError):
                pass

    except (IOError, OSError) as e:
        signals['error'] = str(e)

    return signals


def merge_signals(all_signals):
    """合并多个会话的信号为汇总数据"""
    merged = {
        'session_count': len(all_signals),
        'total_turns': 0,
        'total_duration_min': 0,
        'role': read_role_from_memory(),
        'skill_usage': Counter(),
        'tool_usage': Counter(),
        'plan_mode_count': 0,
        'test_command_count': 0,
        'git_commit_count': 0,
        'error_recovery_tools': Counter(),
        'avg_user_msg_length': 0,
        'user_msg_length_distribution': {'short': 0, 'medium': 0, 'long': 0},
        'claude_md_refs': 0,
        'parallel_agents': 0,
        'user_messages_sample': [],
        # 角色信号字段
        'prd_references': 0,
        'prototype_outputs': 0,
        'test_report_outputs': 0,
        'mock_api_usage': 0,
        'screenshot_count': 0,
        'device_test_count': 0,
        'verification_skill_usage': 0,
        'per_session': [],  # 保留每个会话的摘要
    }

    all_msg_lengths = []

    for sig in all_signals:
        if 'error' in sig:
            continue

        merged['total_turns'] += sig['total_turns']
        merged['total_duration_min'] += sig['session_duration_min']
        merged['plan_mode_count'] += sig['plan_mode_count']
        merged['test_command_count'] += len(sig['test_commands'])
        merged['git_commit_count'] += len(sig['git_commits'])
        merged['claude_md_refs'] += sig['claude_md_refs']
        merged['parallel_agents'] += sig['parallel_agents']

        # 合并角色信号字段
        merged['prd_references'] += sig['prd_references']
        merged['prototype_outputs'] += sig['prototype_outputs']
        merged['test_report_outputs'] += sig['test_report_outputs']
        merged['mock_api_usage'] += sig['mock_api_usage']
        merged['screenshot_count'] += sig['screenshot_count']
        merged['device_test_count'] += sig['device_test_count']
        merged['verification_skill_usage'] += sig['verification_skill_usage']

        for k, v in sig['skill_usage'].items():
            merged['skill_usage'][k] += v
        for k, v in sig['tool_usage'].items():
            merged['tool_usage'][k] += v
        for tool in sig['error_then_action']:
            merged['error_recovery_tools'][tool] += 1

        all_msg_lengths.extend(sig['user_msg_lengths'])

        # 采样用户消息（每个会话取前 2 条）
        merged['user_messages_sample'].extend(sig['user_messages_sample'][:2])

        # 每个会话的摘要
        merged['per_session'].append({
            'file': sig['file'],
            'turns': sig['total_turns'],
            'duration_min': sig['session_duration_min'],
            'tools_used': len(sig['tool_usage']),
            'plan_mode': sig['plan_mode_count'] > 0,
            'has_tests': len(sig['test_commands']) > 0,
        })

    # 计算消息长度分布
    if all_msg_lengths:
        merged['avg_user_msg_length'] = round(sum(all_msg_lengths) / len(all_msg_lengths), 1)
        for length in all_msg_lengths:
            if length < 20:
                merged['user_msg_length_distribution']['short'] += 1
            elif length <= 500:
                merged['user_msg_length_distribution']['medium'] += 1
            else:
                merged['user_msg_length_distribution']['long'] += 1

    # 限制采样消息数量
    merged['user_messages_sample'] = merged['user_messages_sample'][:20]

    # Counter 转为普通 dict 用于 JSON 序列化
    merged['skill_usage'] = dict(merged['skill_usage'])
    merged['tool_usage'] = dict(merged['tool_usage'])
    merged['error_recovery_tools'] = dict(merged['error_recovery_tools'])

    return merged


def find_session_files(directory, days=None, max_files=30):
    """在指定目录下查找 .jsonl 会话文件"""
    jsonl_files = []

    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.jsonl'):
                full_path = os.path.join(root, f)
                mtime = os.path.getmtime(full_path)
                jsonl_files.append((full_path, mtime))

    # 按修改时间排序（最新在前）
    jsonl_files.sort(key=lambda x: x[1], reverse=True)

    # 按天数过滤
    if days is not None:
        cutoff = datetime.now().timestamp() - days * 86400
        jsonl_files = [(f, t) for f, t in jsonl_files if t >= cutoff]

    # 限制文件数量
    if max_files and len(jsonl_files) > max_files:
        jsonl_files = jsonl_files[:max_files]

    return [f for f, _ in jsonl_files]


def main():
    parser = argparse.ArgumentParser(description='AI Coach Session Analyzer')
    parser.add_argument('files', nargs='*', help='JSONL files to analyze')
    parser.add_argument('--dir', help='Directory to scan for .jsonl files')
    parser.add_argument('--days', type=int, help='Only include files from last N days')
    parser.add_argument('--max', type=int, default=30, help='Max number of files to analyze (default: 30)')
    parser.add_argument('--compact', action='store_true', help='Compact JSON output (no indentation)')

    args = parser.parse_args()

    files = list(args.files) if args.files else []

    if args.dir:
        files.extend(find_session_files(args.dir, days=args.days, max_files=args.max))

    if not files:
        print(json.dumps({'error': 'No files to analyze', 'session_count': 0}))
        sys.exit(1)

    # 去重
    files = list(dict.fromkeys(files))

    # 进度输出到 stderr
    print(f"Analyzing {len(files)} session files...", file=sys.stderr)

    all_signals = []
    for i, filepath in enumerate(files):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{len(files)}", file=sys.stderr)
        sig = analyze_single_file(filepath)
        all_signals.append(sig)

    merged = merge_signals(all_signals)

    indent = None if args.compact else 2
    print(json.dumps(merged, indent=indent, ensure_ascii=False))


if __name__ == '__main__':
    main()
