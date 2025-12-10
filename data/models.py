#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据模型层 - 定义数据库实体模型
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Student:
    """学生模型"""
    student_id: str
    name: str
    nickname: Optional[str] = None
    photo_path: Optional[str] = None
    cut_count: int = 0
    called_count: int = 0
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'student_id': self.student_id,
            'name': self.name,
            'nickname': self.nickname,
            'photo_path': self.photo_path,
            'cut_count': self.cut_count,
            'called_count': self.called_count,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> Student:
        """从数据库行创建对象"""
        return cls(
            student_id=row[0],
            name=row[1],
            nickname=row[2],
            photo_path=row[3],
            cut_count=row[4] or 0,
            called_count=row[5] or 0,
        )


@dataclass
class StudentLeave:
    """学生请假记录模型"""
    id: Optional[int] = None
    student_id: str = ""
    session_code: str = ""
    start_time: str = ""
    end_time: str = ""
    reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'session_code': self.session_code,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'reason': self.reason,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> StudentLeave:
        """从数据库行创建对象"""
        return cls(
            id=row[0],
            student_id=row[1],
            session_code=row[2],
            start_time=row[3],
            end_time=row[4],
            reason=row[5],
        )


@dataclass
class RollCall:
    """点名会话模型"""
    id: Optional[int] = None
    session_code: str = ""
    mode: str = ""
    strategy: str = ""
    selected_count: int = 0
    started_at: str = ""
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'session_code': self.session_code,
            'mode': self.mode,
            'strategy': self.strategy,
            'selected_count': self.selected_count,
            'started_at': self.started_at,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> RollCall:
        """从数据库行创建对象"""
        return cls(
            id=row[0],
            session_code=row[1],
            mode=row[2],
            strategy=row[3],
            selected_count=row[4] or 0,
            started_at=row[5],
        )


@dataclass
class RollCallRecord:
    """点名记录模型"""
    id: Optional[int] = None
    roll_call_id: int = 0
    student_id: str = ""
    student_name: Optional[str] = None  # 保存点名时的学生姓名快照，确保历史记录准确
    order_index: int = 0
    status: str = ""
    called_time: str = ""
    updated_time: Optional[str] = None
    note: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'roll_call_id': self.roll_call_id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'order_index': self.order_index,
            'status': self.status,
            'called_time': self.called_time,
            'updated_time': self.updated_time,
            'note': self.note,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> RollCallRecord:
        """从数据库行创建对象"""
        # 兼容旧版本（没有student_name字段）和新版本
        if len(row) >= 9:
            # 新版本：包含student_name字段
            return cls(
                id=row[0],
                roll_call_id=row[1],
                student_id=row[2],
                student_name=row[3],
                order_index=row[4],
                status=row[5],
                called_time=row[6],
                updated_time=row[7],
                note=row[8],
            )
        else:
            # 旧版本：没有student_name字段
            return cls(
                id=row[0],
                roll_call_id=row[1],
                student_id=row[2],
                student_name=None,
                order_index=row[3],
                status=row[4],
                called_time=row[5],
                updated_time=row[6],
                note=row[7],
            )

