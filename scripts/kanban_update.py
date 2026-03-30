#!/usr/bin/env python3
"""
看板更新脚本 - Kanban Update Script

用于更新 OpenClaw 看板系统中的任务状态、流转记录、实时进展和子任务详情。

使用方法:
    # 状态更新
    python3 scripts/kanban_update.py state <task-id> <state> "<说明>"

    # 流转记录
    python3 scripts/kanban_update.py flow <task-id> "<from>" "<to>" "<remark>"

    # 实时进展
    python3 scripts/kanban_update.py progress <task-id> "<当前在做什么>" "<计划>"

    # 子任务详情
    python3 scripts/kanban_update.py todo <task-id> <todo_id> "<title>" <status> --detail "<产出详情>"

状态说明:
    - Todo: 待办
    - Doing: 进行中
    - Done: 已完成
    - Blocked: 已阻塞
    - Rejected: 已驳回
    - Approved: 已批准

示例:
    python3 scripts/kanban_update.py state JJC-001 Doing "开始开发用户登录功能"
    python3 scripts/kanban_update.py flow JJC-001 "Engineering" "CTO" "代码开发完成，申请审查"
    python3 scripts/kanban_update.py progress JJC-001 "正在编写 API 接口" "需求分析✅|编码🔄|测试|发布"
    python3 scripts/kanban_update.py todo JJC-001 1 "用户登录接口" completed --detail "POST /api/login 已实现"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_kanban_path():
    """获取看板文件路径"""
    # 优先使用环境变量
    kanban_path = os.environ.get('OPENCLAW_KANBAN_PATH')
    if kanban_path:
        return Path(kanban_path)

    # 默认在当前目录下查找
    project_root = Path(__file__).parent.parent
    kanban_file = project_root / 'kanban.json'

    if kanban_file.exists():
        return kanban_file

    # 如果看板文件不存在，返回默认路径（会在首次写入时创建）
    return kanban_file


def load_kanban():
    """加载看板数据"""
    kanban_path = get_kanban_path()

    if not kanban_path.exists():
        # 初始化空看板
        return {
            "tasks": {},
            "flows": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }

    with open(kanban_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_kanban(data):
    """保存看板数据"""
    kanban_path = get_kanban_path()
    data["metadata"]["updated_at"] = datetime.now().isoformat()

    # 确保目录存在
    kanban_path.parent.mkdir(parents=True, exist_ok=True)

    with open(kanban_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 看板已更新：{kanban_path}")


def cmd_state(args):
    """更新任务状态"""
    kanban = load_kanban()

    task_id = args.task_id
    state = args.state
    description = args.description

    # 标准化状态
    state_map = {
        "todo": "Todo",
        "doing": "Doing",
        "done": "Done",
        "blocked": "Blocked",
        "rejected": "Rejected",
        "approved": "Approved"
    }
    normalized_state = state_map.get(state.lower(), state)

    # 创建或更新任务
    if task_id not in kanban["tasks"]:
        kanban["tasks"][task_id] = {
            "id": task_id,
            "created_at": datetime.now().isoformat(),
            "todos": []
        }

    task = kanban["tasks"][task_id]
    old_state = task.get("state", "Todo")
    task["state"] = normalized_state
    task["state_description"] = description
    task["updated_at"] = datetime.now().isoformat()

    # 记录状态变更
    flow_record = {
        "task_id": task_id,
        "type": "state_change",
        "from_state": old_state,
        "to_state": normalized_state,
        "description": description,
        "timestamp": datetime.now().isoformat()
    }
    kanban["flows"].append(flow_record)

    save_kanban(kanban)

    print(f"📋 任务 {task_id} 状态更新：{old_state} → {normalized_state}")
    print(f"   说明：{description}")


def cmd_flow(args):
    """记录任务流转"""
    kanban = load_kanban()

    task_id = args.task_id
    from_dept = args.from_dept
    to_dept = args.to_dept
    remark = args.remark

    # 创建或更新任务
    if task_id not in kanban["tasks"]:
        kanban["tasks"][task_id] = {
            "id": task_id,
            "created_at": datetime.now().isoformat(),
            "todos": []
        }

    task = kanban["tasks"][task_id]

    # 更新任务当前处理部门
    task["current_department"] = to_dept
    task["updated_at"] = datetime.now().isoformat()

    # 记录流转
    flow_record = {
        "task_id": task_id,
        "type": "handoff",
        "from": from_dept,
        "to": to_dept,
        "remark": remark,
        "timestamp": datetime.now().isoformat()
    }
    kanban["flows"].append(flow_record)

    # 更新任务的流转历史
    if "history" not in task:
        task["history"] = []
    task["history"].append(flow_record)

    save_kanban(kanban)

    print(f"🔄 任务 {task_id} 流转：{from_dept} → {to_dept}")
    print(f"   备注：{remark}")


def cmd_progress(args):
    """更新任务实时进展"""
    kanban = load_kanban()

    task_id = args.task_id
    current_work = args.current_work
    plan = args.plan

    # 创建或更新任务
    if task_id not in kanban["tasks"]:
        kanban["tasks"][task_id] = {
            "id": task_id,
            "created_at": datetime.now().isoformat(),
            "todos": []
        }

    task = kanban["tasks"][task_id]

    # 更新进展
    task["current_progress"] = {
        "current_work": current_work,
        "plan": plan,
        "updated_at": datetime.now().isoformat()
    }
    task["updated_at"] = datetime.now().isoformat()

    # 记录进展更新
    progress_record = {
        "task_id": task_id,
        "type": "progress",
        "current_work": current_work,
        "plan": plan,
        "timestamp": datetime.now().isoformat()
    }
    kanban["flows"].append(progress_record)

    save_kanban(kanban)

    print(f"📊 任务 {task_id} 进展更新")
    print(f"   当前工作：{current_work}")
    print(f"   计划：{plan}")


def cmd_todo(args):
    """更新子任务详情"""
    kanban = load_kanban()

    task_id = args.task_id
    todo_id = args.todo_id
    title = args.title
    status = args.status
    detail = args.detail

    # 创建或更新任务
    if task_id not in kanban["tasks"]:
        kanban["tasks"][task_id] = {
            "id": task_id,
            "created_at": datetime.now().isoformat(),
            "todos": []
        }

    task = kanban["tasks"][task_id]

    # 查找或创建子任务
    todo_item = None
    for todo in task["todos"]:
        if str(todo.get("todo_id")) == str(todo_id):
            todo_item = todo
            break

    if todo_item is None:
        # 创建新的子任务
        todo_item = {
            "todo_id": int(todo_id) if todo_id.isdigit() else todo_id,
            "title": title,
            "status": status,
            "created_at": datetime.now().isoformat()
        }
        task["todos"].append(todo_item)
    else:
        # 更新现有子任务
        todo_item["title"] = title
        todo_item["status"] = status

    # 更新详情
    if detail:
        todo_item["detail"] = detail

    todo_item["updated_at"] = datetime.now().isoformat()
    task["updated_at"] = datetime.now().isoformat()

    save_kanban(kanban)

    print(f"✅ 任务 {task_id} 子任务 #{todo_id} 更新")
    print(f"   标题：{title}")
    print(f"   状态：{status}")
    if detail:
        print(f"   详情：{detail}")


def cmd_list(args):
    """列出所有任务"""
    kanban = load_kanban()

    if not kanban["tasks"]:
        print("📋 当前没有任务")
        return

    print("📋 任务列表\n")
    print("=" * 80)

    for task_id, task in kanban["tasks"].items():
        state = task.get("state", "Todo")
        state_emoji = {
            "Todo": "⏳",
            "Doing": "🔄",
            "Done": "✅",
            "Blocked": "🚫",
            "Rejected": "❌",
            "Approved": "✔️"
        }.get(state, "📋")

        dept = task.get("current_department", "未分配")
        progress = task.get("current_progress", {})
        current_work = progress.get("current_work", "无进展")

        print(f"\n{state_emoji} {task_id}")
        print(f"   状态：{state} | 部门：{dept}")
        print(f"   进展：{current_work}")

        # 子任务
        todos = task.get("todos", [])
        if todos:
            print(f"   子任务 ({len(todos)}):")
            for todo in todos:
                todo_status = todo.get("status", "pending")
                todo_emoji = "✅" if todo_status == "completed" else "🔄"
                print(f"      {todo_emoji} #{todo['todo_id']}: {todo['title']}")

    print("\n" + "=" * 80)
    print(f"总任务数：{len(kanban['tasks'])}")


def cmd_show(args):
    """显示任务详情"""
    kanban = load_kanban()

    task_id = args.task_id

    if task_id not in kanban["tasks"]:
        print(f"❌ 任务 {task_id} 不存在")
        return

    task = kanban["tasks"][task_id]

    print(f"\n📋 任务详情：{task_id}")
    print("=" * 80)

    state = task.get("state", "Todo")
    state_emoji = {
        "Todo": "⏳",
        "Doing": "🔄",
        "Done": "✅",
        "Blocked": "🚫",
        "Rejected": "❌",
        "Approved": "✔️"
    }.get(state, "📋")

    print(f"\n{state_emoji} 状态：{state}")
    print(f"📍 当前部门：{task.get('current_department', '未分配')}")
    print(f"📅 创建时间：{task.get('created_at', '未知')}")
    print(f"📅 更新时间：{task.get('updated_at', '未知')}")

    # 当前进展
    progress = task.get("current_progress", {})
    if progress:
        print(f"\n📊 当前进展:")
        print(f"   工作：{progress.get('current_work', '无')}")
        print(f"   计划：{progress.get('plan', '无')}")

    # 子任务
    todos = task.get("todos", [])
    if todos:
        print(f"\n✅ 子任务 ({len(todos)}):")
        for todo in todos:
            todo_status = todo.get("status", "pending")
            todo_emoji = "✅" if todo_status == "completed" else "🔄"
            print(f"   {todo_emoji} #{todo['todo_id']}: {todo['title']}")
            if todo.get('detail'):
                print(f"       详情：{todo['detail']}")

    # 流转历史
    history = task.get("history", [])
    if history:
        print(f"\n🔄 流转历史:")
        for record in history[-5:]:  # 显示最近 5 条
            print(f"   {record['timestamp'][:16]}: {record['from']} → {record['to']}")
            print(f"      {record['remark']}")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='看板更新脚本 - 更新 OpenClaw 看板系统中的任务状态、流转记录、实时进展和子任务详情',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s state JJC-001 Doing "开始开发用户登录功能"
  %(prog)s flow JJC-001 "Engineering" "CTO" "代码开发完成，申请审查"
  %(prog)s progress JJC-001 "正在编写 API 接口" "需求分析✅|编码🔄|测试 | 发布"
  %(prog)s todo JJC-001 1 "用户登录接口" completed --detail "POST /api/login 已实现"
  %(prog)s list
  %(prog)s show JJC-001
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # state 命令
    state_parser = subparsers.add_parser('state', help='更新任务状态')
    state_parser.add_argument('task_id', help='任务 ID')
    state_parser.add_argument('state', help='新状态 (Todo/Doing/Done/Blocked/Rejected/Approved)')
    state_parser.add_argument('description', help='状态说明')
    state_parser.set_defaults(func=cmd_state)

    # flow 命令
    flow_parser = subparsers.add_parser('flow', help='记录任务流转')
    flow_parser.add_argument('task_id', help='任务 ID')
    flow_parser.add_argument('from_dept', help='源部门')
    flow_parser.add_argument('to_dept', help='目标部门')
    flow_parser.add_argument('remark', help='流转备注')
    flow_parser.set_defaults(func=cmd_flow)

    # progress 命令
    progress_parser = subparsers.add_parser('progress', help='更新实时进展')
    progress_parser.add_argument('task_id', help='任务 ID')
    progress_parser.add_argument('current_work', help='当前在做什么')
    progress_parser.add_argument('plan', help='计划列表 (用 | 分隔)')
    progress_parser.set_defaults(func=cmd_progress)

    # todo 命令
    todo_parser = subparsers.add_parser('todo', help='更新子任务详情')
    todo_parser.add_argument('task_id', help='任务 ID')
    todo_parser.add_argument('todo_id', help='子任务 ID')
    todo_parser.add_argument('title', help='子任务标题')
    todo_parser.add_argument('status', help='子任务状态 (pending/completed)')
    todo_parser.add_argument('--detail', help='子任务详情')
    todo_parser.set_defaults(func=cmd_todo)

    # list 命令
    list_parser = subparsers.add_parser('list', help='列出所有任务')
    list_parser.set_defaults(func=cmd_list)

    # show 命令
    show_parser = subparsers.add_parser('show', help='显示任务详情')
    show_parser.add_argument('task_id', help='任务 ID')
    show_parser.set_defaults(func=cmd_show)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
