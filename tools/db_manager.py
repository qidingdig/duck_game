#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库管理工具 - 提供便捷的数据库操作接口
支持命令行和编程两种使用方式
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sqlite_database import SQLiteDatabase
from data.repositories import (
    SQLiteStudentRepository,
    SQLiteStudentLeaveRepository,
    SQLiteRollCallRepository,
    SQLiteRollCallRecordRepository,
)
from data.models import Student, StudentLeave, RollCall, RollCallRecord


class DatabaseManager:
    """数据库管理工具类 - 提供便捷的CRUD操作"""
    
    def __init__(self, db_path: str = "data/roll_call.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db = SQLiteDatabase(db_path)
        self.student_repo = SQLiteStudentRepository(self.db)
        self.leave_repo = SQLiteStudentLeaveRepository(self.db)
        self.roll_call_repo = SQLiteRollCallRepository(self.db)
        self.record_repo = SQLiteRollCallRecordRepository(self.db)
    
    # ======================================================================
    # 学生管理
    # ======================================================================
    
    def list_students(self) -> List[Student]:
        """列出所有学生"""
        return self.student_repo.find_all()
    
    def get_student(self, student_id: str) -> Optional[Student]:
        """获取学生信息"""
        return self.student_repo.find_by_id(student_id)
    
    def add_student(
        self,
        student_id: str,
        name: str,
        nickname: Optional[str] = None,
        photo_path: Optional[str] = None,
        cut_count: int = 0,
        called_count: int = 0,
    ) -> Student:
        """添加学生"""
        student = Student(
            student_id=student_id,
            name=name,
            nickname=nickname,
            photo_path=photo_path,
            cut_count=cut_count,
            called_count=called_count,
        )
        self.student_repo.save(student)
        return student
    
    def update_student(
        self,
        student_id: str,
        name: Optional[str] = None,
        nickname: Optional[str] = None,
        photo_path: Optional[str] = None,
        cut_count: Optional[int] = None,
        called_count: Optional[int] = None,
    ) -> bool:
        """更新学生信息"""
        student = self.student_repo.find_by_id(student_id)
        if not student:
            return False
        
        if name is not None:
            student.name = name
        if nickname is not None:
            student.nickname = nickname
        if photo_path is not None:
            student.photo_path = photo_path
        if cut_count is not None:
            student.cut_count = cut_count
        if called_count is not None:
            student.called_count = called_count
        
        self.student_repo.save(student)
        return True
    
    def delete_student(self, student_id: str) -> bool:
        """删除学生"""
        student = self.student_repo.find_by_id(student_id)
        if not student:
            return False
        self.student_repo.delete(student_id)
        return True
    
    def reset_student_statistics(self, student_id: str) -> bool:
        """重置学生统计信息"""
        student = self.student_repo.find_by_id(student_id)
        if not student:
            return False
        student.cut_count = 0
        student.called_count = 0
        self.student_repo.save(student)
        return True
    
    def batch_update_students(self, updates: List[Dict[str, Any]]) -> int:
        """
        批量更新学生
        
        Args:
            updates: 更新列表，每个元素包含student_id和要更新的字段
        
        Returns:
            成功更新的数量
        """
        count = 0
        for update_data in updates:
            student_id = update_data.pop('student_id')
            if self.update_student(student_id, **update_data):
                count += 1
        return count
    
    # ======================================================================
    # 请假管理
    # ======================================================================
    
    def add_leave(
        self,
        student_id: str,
        session_code: str,
        start_time: str,
        end_time: str,
        reason: Optional[str] = None,
    ) -> int:
        """添加请假记录"""
        leave = StudentLeave(
            student_id=student_id,
            session_code=session_code,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
        )
        return self.leave_repo.save(leave)
    
    def has_leave(self, student_id: str, session_code: str) -> bool:
        """检查是否有请假"""
        return self.leave_repo.has_leave(student_id, session_code)
    
    def delete_leave(self, leave_id: int) -> bool:
        """删除请假记录（通过直接SQL）"""
        affected = self.db.execute("DELETE FROM student_leaves WHERE id = ?", (leave_id,))
        return affected > 0
    
    def list_leaves(self, student_id: Optional[str] = None) -> List[Dict]:
        """列出请假记录"""
        if student_id:
            query = """
                SELECT id, student_id, session_code, start_time, end_time, reason
                FROM student_leaves
                WHERE student_id = ?
                ORDER BY start_time DESC
            """
            rows = self.db.fetch_all(query, (student_id,))
        else:
            query = """
                SELECT id, student_id, session_code, start_time, end_time, reason
                FROM student_leaves
                ORDER BY start_time DESC
            """
            rows = self.db.fetch_all(query)
        
        return [
            {
                'id': row[0],
                'student_id': row[1],
                'session_code': row[2],
                'start_time': row[3],
                'end_time': row[4],
                'reason': row[5],
            }
            for row in rows
        ]
    
    # ======================================================================
    # 点名记录管理
    # ======================================================================
    
    def list_roll_calls(self) -> List[RollCall]:
        """列出所有点名会话"""
        query = """
            SELECT id, session_code, mode, strategy, selected_count, started_at
            FROM roll_calls
            ORDER BY started_at DESC
        """
        rows = self.db.fetch_all(query)
        return [RollCall.from_row(row) for row in rows]
    
    def get_roll_call_records(self, roll_call_id: int) -> List[RollCallRecord]:
        """获取点名会话的所有记录"""
        return self.record_repo.find_by_roll_call_id(roll_call_id)
    
    def update_record_status(self, record_id: int, new_status: str) -> bool:
        """更新记录状态"""
        import time
        updated_time = time.strftime("%Y-%m-%d %H:%M:%S")
        return self.record_repo.update_status(record_id, new_status, updated_time)
    
    def delete_roll_call(self, roll_call_id: int) -> bool:
        """删除点名会话及其所有记录"""
        # 先删除记录
        self.db.execute("DELETE FROM roll_call_records WHERE roll_call_id = ?", (roll_call_id,))
        # 再删除会话
        affected = self.db.execute("DELETE FROM roll_calls WHERE id = ?", (roll_call_id,))
        return affected > 0
    
    # ======================================================================
    # 统计和查询
    # ======================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_students = len(self.student_repo.find_all())
        
        total_cut = self.db.fetch_one("SELECT SUM(cut_count) FROM students")[0] or 0
        total_called = self.db.fetch_one("SELECT SUM(called_count) FROM students")[0] or 0
        
        total_roll_calls = self.db.fetch_one("SELECT COUNT(*) FROM roll_calls")[0] or 0
        total_records = self.db.fetch_one("SELECT COUNT(*) FROM roll_call_records")[0] or 0
        
        return {
            'total_students': total_students,
            'total_cut_count': total_cut,
            'total_called_count': total_called,
            'total_roll_calls': total_roll_calls,
            'total_records': total_records,
        }
    
    def search_students(self, keyword: str) -> List[Student]:
        """搜索学生（按姓名或学号）"""
        query = """
            SELECT student_id, name, nickname, photo_path, cut_count, called_count
            FROM students
            WHERE student_id LIKE ? OR name LIKE ? OR nickname LIKE ?
            ORDER BY student_id
        """
        pattern = f"%{keyword}%"
        rows = self.db.fetch_all(query, (pattern, pattern, pattern))
        return [Student.from_row(row) for row in rows]
    
    # ======================================================================
    # 便捷方法
    # ======================================================================
    
    def print_students(self) -> None:
        """打印所有学生"""
        students = self.list_students()
        print(f"\n共 {len(students)} 名学生：")
        print("-" * 80)
        print(f"{'学号':<12} {'姓名':<10} {'昵称':<10} {'缺勤':<6} {'被点名':<6}")
        print("-" * 80)
        for s in students:
            print(f"{s.student_id:<12} {s.name:<10} {s.nickname or '-':<10} {s.cut_count:<6} {s.called_count:<6}")
        print("-" * 80)
    
    def print_statistics(self) -> None:
        """打印统计信息"""
        stats = self.get_statistics()
        print("\n数据库统计信息：")
        print("-" * 40)
        print(f"学生总数: {stats['total_students']}")
        print(f"总缺勤次数: {stats['total_cut_count']}")
        print(f"总被点名次数: {stats['total_called_count']}")
        print(f"点名会话数: {stats['total_roll_calls']}")
        print(f"点名记录数: {stats['total_records']}")
        print("-" * 40)


def main():
    """命令行交互界面"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库管理工具")
    parser.add_argument("--db", default="data/roll_call.db", help="数据库文件路径")
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 学生相关命令
    student_parser = subparsers.add_parser("student", help="学生管理")
    student_subparsers = student_parser.add_subparsers(dest="student_action")
    
    student_subparsers.add_parser("list", help="列出所有学生")
    student_subparsers.add_parser("stats", help="显示统计信息")
    
    add_student_parser = student_subparsers.add_parser("add", help="添加学生")
    add_student_parser.add_argument("--id", required=True, help="学号")
    add_student_parser.add_argument("--name", required=True, help="姓名")
    add_student_parser.add_argument("--nickname", help="昵称")
    add_student_parser.add_argument("--photo", help="照片路径")
    
    update_student_parser = student_subparsers.add_parser("update", help="更新学生")
    update_student_parser.add_argument("--id", required=True, help="学号")
    update_student_parser.add_argument("--name", help="姓名")
    update_student_parser.add_argument("--nickname", help="昵称")
    update_student_parser.add_argument("--photo", help="照片路径")
    update_student_parser.add_argument("--cut", type=int, help="缺勤次数")
    update_student_parser.add_argument("--called", type=int, help="被点名次数")
    
    delete_student_parser = student_subparsers.add_parser("delete", help="删除学生")
    delete_student_parser.add_argument("--id", required=True, help="学号")
    
    reset_student_parser = student_subparsers.add_parser("reset", help="重置学生统计")
    reset_student_parser.add_argument("--id", required=True, help="学号")
    
    search_student_parser = student_subparsers.add_parser("search", help="搜索学生")
    search_student_parser.add_argument("keyword", help="搜索关键词")
    
    # 请假相关命令
    leave_parser = subparsers.add_parser("leave", help="请假管理")
    leave_subparsers = leave_parser.add_subparsers(dest="leave_action")
    
    leave_subparsers.add_parser("list", help="列出所有请假")
    
    add_leave_parser = leave_subparsers.add_parser("add", help="添加请假")
    add_leave_parser.add_argument("--student-id", required=True, help="学号")
    add_leave_parser.add_argument("--session", required=True, help="会话代码")
    add_leave_parser.add_argument("--start", required=True, help="开始时间")
    add_leave_parser.add_argument("--end", required=True, help="结束时间")
    add_leave_parser.add_argument("--reason", help="请假原因")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = DatabaseManager(args.db)
    
    if args.command == "student":
        if args.student_action == "list":
            manager.print_students()
        elif args.student_action == "stats":
            manager.print_statistics()
        elif args.student_action == "add":
            manager.add_student(
                student_id=args.id,
                name=args.name,
                nickname=args.nickname,
                photo_path=args.photo,
            )
            print(f"✓ 成功添加学生: {args.id} - {args.name}")
        elif args.student_action == "update":
            updates = {}
            if args.name:
                updates['name'] = args.name
            if args.nickname:
                updates['nickname'] = args.nickname
            if args.photo:
                updates['photo_path'] = args.photo
            if args.cut is not None:
                updates['cut_count'] = args.cut
            if args.called is not None:
                updates['called_count'] = args.called
            
            if manager.update_student(args.id, **updates):
                print(f"✓ 成功更新学生: {args.id}")
            else:
                print(f"✗ 学生不存在: {args.id}")
        elif args.student_action == "delete":
            if manager.delete_student(args.id):
                print(f"✓ 成功删除学生: {args.id}")
            else:
                print(f"✗ 学生不存在: {args.id}")
        elif args.student_action == "reset":
            if manager.reset_student_statistics(args.id):
                print(f"✓ 成功重置学生统计: {args.id}")
            else:
                print(f"✗ 学生不存在: {args.id}")
        elif args.student_action == "search":
            students = manager.search_students(args.keyword)
            print(f"\n找到 {len(students)} 名学生：")
            for s in students:
                print(f"  {s.student_id} - {s.name} ({s.nickname or '无昵称'})")
    
    elif args.command == "leave":
        if args.leave_action == "list":
            leaves = manager.list_leaves()
            print(f"\n共 {len(leaves)} 条请假记录：")
            for leave in leaves:
                print(f"  {leave['student_id']} - {leave['session_code']} ({leave['reason'] or '无原因'})")
        elif args.leave_action == "add":
            leave_id = manager.add_leave(
                student_id=args.student_id,
                session_code=args.session,
                start_time=args.start,
                end_time=args.end,
                reason=args.reason,
            )
            print(f"✓ 成功添加请假记录: ID={leave_id}")


if __name__ == "__main__":
    main()

