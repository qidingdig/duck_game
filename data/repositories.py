#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Repository层 - 数据访问接口和实现
遵循Repository模式，封装数据访问逻辑
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from data.database_interface import DatabaseInterface
from data.models import Student, StudentLeave, RollCall, RollCallRecord


class StudentRepository(ABC):
    """学生Repository抽象接口"""
    
    @abstractmethod
    def find_all(self) -> List[Student]:
        """查找所有学生"""
        pass
    
    @abstractmethod
    def find_by_id(self, student_id: str) -> Optional[Student]:
        """根据ID查找学生"""
        pass
    
    @abstractmethod
    def save(self, student: Student) -> None:
        """保存学生（新增或更新）"""
        pass
    
    @abstractmethod
    def update_statistics(self, student_id: str, cut_delta: int, called_delta: int) -> None:
        """更新学生统计信息"""
        pass
    
    @abstractmethod
    def delete(self, student_id: str) -> None:
        """删除学生"""
        pass


class StudentLeaveRepository(ABC):
    """学生请假Repository抽象接口"""
    
    @abstractmethod
    def has_leave(self, student_id: str, session_code: str) -> bool:
        """检查学生是否有请假记录"""
        pass
    
    @abstractmethod
    def save(self, leave: StudentLeave) -> int:
        """保存请假记录"""
        pass
    
    @abstractmethod
    def find_by_student_and_session(self, student_id: str, session_code: str) -> Optional[StudentLeave]:
        """根据学生ID和会话代码查找请假记录"""
        pass


class RollCallRepository(ABC):
    """点名会话Repository抽象接口"""
    
    @abstractmethod
    def create(self, roll_call: RollCall) -> int:
        """创建点名会话"""
        pass
    
    @abstractmethod
    def find_by_id(self, roll_call_id: int) -> Optional[RollCall]:
        """根据ID查找点名会话"""
        pass
    
    @abstractmethod
    def find_by_session_code(self, session_code: str) -> Optional[RollCall]:
        """根据会话代码查找点名会话"""
        pass
    
    @abstractmethod
    def delete(self, roll_call_id: int) -> bool:
        """删除点名会话及其所有记录"""
        pass
    
    @abstractmethod
    def delete_by_session_code(self, session_code: str) -> bool:
        """根据会话代码删除点名会话及其所有记录"""
        pass


class RollCallRecordRepository(ABC):
    """点名记录Repository抽象接口"""
    
    @abstractmethod
    def create(self, record: RollCallRecord) -> int:
        """创建点名记录"""
        pass
    
    @abstractmethod
    def update_status(self, record_id: int, new_status: str, updated_time: str) -> bool:
        """更新记录状态"""
        pass
    
    @abstractmethod
    def find_by_id(self, record_id: int) -> Optional[RollCallRecord]:
        """根据ID查找记录"""
        pass
    
    @abstractmethod
    def find_latest_by_roll_call_and_student(self, roll_call_id: int, student_id: str) -> Optional[RollCallRecord]:
        """查找最新的点名记录"""
        pass
    
    @abstractmethod
    def find_by_roll_call_id(self, roll_call_id: int) -> List[RollCallRecord]:
        """查找指定点名会话的所有记录"""
        pass
    
    @abstractmethod
    def delete(self, record_id: int) -> bool:
        """删除记录"""
        pass
    
    @abstractmethod
    def delete_many(self, record_ids: List[int]) -> int:
        """批量删除记录"""
        pass


# ============================================================================
# SQLite实现
# ============================================================================

class SQLiteStudentRepository(StudentRepository):
    """SQLite学生Repository实现"""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
    
    def find_all(self) -> List[Student]:
        query = """
            SELECT student_id, name, nickname, photo_path, cut_count, called_count
            FROM students
            ORDER BY student_id
        """
        rows = self.db.fetch_all(query)
        return [Student.from_row(row) for row in rows]
    
    def find_by_id(self, student_id: str) -> Optional[Student]:
        query = """
            SELECT student_id, name, nickname, photo_path, cut_count, called_count
            FROM students
            WHERE student_id = ?
        """
        row = self.db.fetch_one(query, (student_id,))
        return Student.from_row(row) if row else None
    
    def save(self, student: Student) -> None:
        query = """
            INSERT OR REPLACE INTO students 
            (student_id, name, nickname, photo_path, cut_count, called_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        self.db.execute(
            query,
            (
                student.student_id,
                student.name,
                student.nickname,
                student.photo_path,
                student.cut_count,
                student.called_count,
            ),
        )
    
    def update_statistics(self, student_id: str, cut_delta: int, called_delta: int) -> None:
        query = """
            UPDATE students
            SET cut_count = cut_count + ?,
                called_count = called_count + ?
            WHERE student_id = ?
        """
        self.db.execute(query, (cut_delta, called_delta, student_id))
    
    def delete(self, student_id: str) -> None:
        query = "DELETE FROM students WHERE student_id = ?"
        self.db.execute(query, (student_id,))


class SQLiteStudentLeaveRepository(StudentLeaveRepository):
    """SQLite学生请假Repository实现"""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
    
    def has_leave(self, student_id: str, session_code: str) -> bool:
        query = """
            SELECT COUNT(*) FROM student_leaves
            WHERE student_id = ? AND session_code = ?
        """
        row = self.db.fetch_one(query, (student_id, session_code))
        return row[0] > 0 if row else False
    
    def save(self, leave: StudentLeave) -> int:
        # 必须在同一个连接中执行插入和获取 last_insert_rowid
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO student_leaves 
                (student_id, session_code, start_time, end_time, reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    leave.student_id,
                    leave.session_code,
                    leave.start_time,
                    leave.end_time,
                    leave.reason,
                ),
            )
            row = cursor.execute("SELECT last_insert_rowid()").fetchone()
            return row[0] if row else 0
    
    def find_by_student_and_session(self, student_id: str, session_code: str) -> Optional[StudentLeave]:
        query = """
            SELECT id, student_id, session_code, start_time, end_time, reason
            FROM student_leaves
            WHERE student_id = ? AND session_code = ?
        """
        row = self.db.fetch_one(query, (student_id, session_code))
        return StudentLeave.from_row(row) if row else None


class SQLiteRollCallRepository(RollCallRepository):
    """SQLite点名会话Repository实现"""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
    
    def create(self, roll_call: RollCall) -> int:
        # 必须在同一个连接中执行插入和获取 last_insert_rowid
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO roll_calls 
                (session_code, mode, strategy, selected_count, started_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    roll_call.session_code,
                    roll_call.mode,
                    roll_call.strategy,
                    roll_call.selected_count,
                    roll_call.started_at,
                ),
            )
            row = cursor.execute("SELECT last_insert_rowid()").fetchone()
            return row[0] if row else 0
    
    def find_by_id(self, roll_call_id: int) -> Optional[RollCall]:
        query = """
            SELECT id, session_code, mode, strategy, selected_count, started_at
            FROM roll_calls
            WHERE id = ?
        """
        row = self.db.fetch_one(query, (roll_call_id,))
        return RollCall.from_row(row) if row else None
    
    def find_by_session_code(self, session_code: str) -> Optional[RollCall]:
        query = """
            SELECT id, session_code, mode, strategy, selected_count, started_at
            FROM roll_calls
            WHERE session_code = ?
            ORDER BY started_at DESC
            LIMIT 1
        """
        row = self.db.fetch_one(query, (session_code,))
        return RollCall.from_row(row) if row else None
    
    def delete(self, roll_call_id: int) -> bool:
        """删除点名会话及其所有记录"""
        # 先删除所有相关记录
        query_records = "DELETE FROM roll_call_records WHERE roll_call_id = ?"
        self.db.execute(query_records, (roll_call_id,))
        # 再删除会话
        query_session = "DELETE FROM roll_calls WHERE id = ?"
        affected = self.db.execute(query_session, (roll_call_id,))
        return affected > 0
    
    def delete_by_session_code(self, session_code: str) -> bool:
        """根据会话代码删除点名会话及其所有记录"""
        roll_call = self.find_by_session_code(session_code)
        if not roll_call or not roll_call.id:
            return False
        return self.delete(roll_call.id)


class SQLiteRollCallRecordRepository(RollCallRecordRepository):
    """SQLite点名记录Repository实现"""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
    
    def create(self, record: RollCallRecord) -> int:
        # 必须在同一个连接中执行插入和获取 last_insert_rowid
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO roll_call_records
                (roll_call_id, student_id, student_name, order_index, status, called_time, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.roll_call_id,
                    record.student_id,
                    record.student_name,
                    record.order_index,
                    record.status,
                    record.called_time,
                    record.note,
                ),
            )
            row = cursor.execute("SELECT last_insert_rowid()").fetchone()
            return row[0] if row else 0
    
    def update_status(self, record_id: int, new_status: str, updated_time: str) -> bool:
        query = """
            UPDATE roll_call_records
            SET status = ?, updated_time = ?
            WHERE id = ?
        """
        affected = self.db.execute(query, (new_status, updated_time, record_id))
        return affected > 0
    
    def find_by_id(self, record_id: int) -> Optional[RollCallRecord]:
        query = """
            SELECT id, roll_call_id, student_id, student_name, order_index, status, called_time, updated_time, note
            FROM roll_call_records
            WHERE id = ?
        """
        row = self.db.fetch_one(query, (record_id,))
        return RollCallRecord.from_row(row) if row else None
    
    def find_latest_by_roll_call_and_student(self, roll_call_id: int, student_id: str) -> Optional[RollCallRecord]:
        query = """
            SELECT id, roll_call_id, student_id, student_name, order_index, status, called_time, updated_time, note
            FROM roll_call_records
            WHERE roll_call_id = ? AND student_id = ?
            ORDER BY called_time DESC
            LIMIT 1
        """
        row = self.db.fetch_one(query, (roll_call_id, student_id))
        return RollCallRecord.from_row(row) if row else None
    
    def find_by_roll_call_id(self, roll_call_id: int) -> List[RollCallRecord]:
        query = """
            SELECT id, roll_call_id, student_id, student_name, order_index, status, called_time, updated_time, note
            FROM roll_call_records
            WHERE roll_call_id = ?
            ORDER BY order_index ASC
        """
        rows = self.db.fetch_all(query, (roll_call_id,))
        return [RollCallRecord.from_row(row) for row in rows]
    
    def delete(self, record_id: int) -> bool:
        """删除记录"""
        query = "DELETE FROM roll_call_records WHERE id = ?"
        affected = self.db.execute(query, (record_id,))
        return affected > 0
    
    def delete_many(self, record_ids: List[int]) -> int:
        """批量删除记录"""
        if not record_ids:
            return 0
        placeholders = ','.join(['?'] * len(record_ids))
        query = f"DELETE FROM roll_call_records WHERE id IN ({placeholders})"
        affected = self.db.execute(query, tuple(record_ids))
        return affected

