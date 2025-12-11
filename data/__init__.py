#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据访问层：提供数据库接口、模型、仓库和迁移功能。
"""

from data.database_interface import DatabaseInterface
from data.sqlite_database import SQLiteDatabase
from data.models import Student, StudentLeave, RollCall, RollCallRecord
from data.repositories import (
    StudentRepository,
    StudentLeaveRepository,
    RollCallRepository,
    RollCallRecordRepository,
    SQLiteStudentRepository,
    SQLiteStudentLeaveRepository,
    SQLiteRollCallRepository,
    SQLiteRollCallRecordRepository,
)
from data.database_migration import DatabaseMigration

__all__ = [
    "DatabaseInterface",
    "SQLiteDatabase",
    "Student",
    "StudentLeave",
    "RollCall",
    "RollCallRecord",
    "StudentRepository",
    "StudentLeaveRepository",
    "RollCallRepository",
    "RollCallRecordRepository",
    "SQLiteStudentRepository",
    "SQLiteStudentLeaveRepository",
    "SQLiteRollCallRepository",
    "SQLiteRollCallRecordRepository",
    "DatabaseMigration",
]

