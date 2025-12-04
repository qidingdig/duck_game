#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库操作辅助脚本 - 提供常用的数据库操作示例
可以直接运行或导入使用
"""

from __future__ import annotations

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_manager import DatabaseManager


def example_add_student():
    """示例：添加学生"""
    manager = DatabaseManager()
    
    # 添加单个学生
    student = manager.add_student(
        student_id="2023011",
        name="唐小新",
        nickname="新新",
        photo_path="assets/images/students/student11.png",
    )
    print(f"✓ 添加学生: {student.student_id} - {student.name}")


def example_update_student():
    """示例：更新学生信息"""
    manager = DatabaseManager()
    
    # 更新学生姓名
    manager.update_student("2023011", name="唐小新（已改名）")
    
    # 更新多个字段
    manager.update_student(
        "2023011",
        nickname="新新新",
        cut_count=0,
        called_count=5,
    )
    print("✓ 更新完成")


def example_batch_update():
    """示例：批量更新学生"""
    manager = DatabaseManager()
    
    updates = [
        {'student_id': '2023001', 'cut_count': 0},  # 重置缺勤
        {'student_id': '2023002', 'called_count': 20},  # 更新被点名次数
        {'student_id': '2023003', 'nickname': '新昵称'},
    ]
    
    count = manager.batch_update_students(updates)
    print(f"✓ 批量更新了 {count} 名学生")


def example_search_students():
    """示例：搜索学生"""
    manager = DatabaseManager()
    
    # 按关键词搜索
    results = manager.search_students("唐小")
    print(f"找到 {len(results)} 名学生")
    for student in results:
        print(f"  {student.student_id} - {student.name}")


def example_reset_statistics():
    """示例：重置所有学生统计"""
    manager = DatabaseManager()
    
    students = manager.list_students()
    for student in students:
        manager.reset_student_statistics(student.student_id)
    
    print(f"✓ 重置了 {len(students)} 名学生的统计信息")


def example_add_leave():
    """示例：添加请假记录"""
    manager = DatabaseManager()
    
    leave_id = manager.add_leave(
        student_id="2023001",
        session_code="2024-11-25-AM",
        start_time="2024-11-25 08:00",
        end_time="2024-11-25 10:00",
        reason="病假",
    )
    print(f"✓ 添加请假记录: ID={leave_id}")


def example_view_statistics():
    """示例：查看统计信息"""
    manager = DatabaseManager()
    
    manager.print_students()
    manager.print_statistics()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "add_student":
            example_add_student()
        elif action == "update_student":
            example_update_student()
        elif action == "batch_update":
            example_batch_update()
        elif action == "search":
            keyword = sys.argv[2] if len(sys.argv) > 2 else "唐小"
            manager = DatabaseManager()
            results = manager.search_students(keyword)
            print(f"找到 {len(results)} 名学生")
            for student in results:
                print(f"  {student.student_id} - {student.name}")
        elif action == "reset_stats":
            example_reset_statistics()
        elif action == "stats":
            example_view_statistics()
        else:
            print("可用操作: add_student, update_student, batch_update, search, reset_stats, stats")
    else:
        print("数据库操作辅助工具")
        print("\n可用操作:")
        print("  python tools/db_helper.py add_student      # 添加学生示例")
        print("  python tools/db_helper.py update_student   # 更新学生示例")
        print("  python tools/db_helper.py batch_update     # 批量更新示例")
        print("  python tools/db_helper.py search <关键词>  # 搜索学生")
        print("  python tools/db_helper.py reset_stats      # 重置统计")
        print("  python tools/db_helper.py stats            # 查看统计")
        print("\n或使用命令行工具:")
        print("  python tools/db_manager.py student list     # 列出所有学生")
        print("  python tools/db_manager.py student add --id 2023011 --name 唐小新")

