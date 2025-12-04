#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库迁移管理 - 管理数据库版本和表结构变更
"""

from __future__ import annotations

import os
from typing import Optional

from data.database_interface import DatabaseInterface


class DatabaseMigration:
    """数据库迁移管理器"""
    
    def __init__(self, db: DatabaseInterface, db_path: str):
        self.db = db
        self.db_path = db_path
        self.current_version = self._get_current_version()
    
    def _get_current_version(self) -> int:
        """获取当前数据库版本"""
        # 检查版本表是否存在
        version_table_exists = self._check_table_exists("schema_version")
        
        if not version_table_exists:
            # 创建版本表
            self.db.execute_script("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
            """)
            return 0
        
        row = self.db.fetch_one("SELECT MAX(version) FROM schema_version")
        return row[0] if row and row[0] is not None else 0
    
    def _check_table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        # SQLite特定实现
        try:
            row = self.db.fetch_one("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            return row is not None
        except Exception:
            return False
    
    def migrate(self) -> None:
        """执行数据库迁移"""
        target_version = self._get_target_version()
        
        if self.current_version >= target_version:
            return
        
        # 执行迁移脚本
        for version in range(self.current_version + 1, target_version + 1):
            migration_script = self._get_migration_script(version)
            if migration_script:
                self._apply_migration(version, migration_script)
    
    def _get_target_version(self) -> int:
        """获取目标版本（当前为1）"""
        return 1
    
    def _get_migration_script(self, version: int) -> Optional[str]:
        """获取指定版本的迁移脚本"""
        migrations = {
            1: self._get_v1_migration_script(),
        }
        return migrations.get(version)
    
    def _get_v1_migration_script(self) -> str:
        """获取版本1的迁移脚本（创建所有表）"""
        return """
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                nickname TEXT,
                photo_path TEXT,
                cut_count INTEGER DEFAULT 0,
                called_count INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS student_leaves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                session_code TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                reason TEXT,
                FOREIGN KEY(student_id) REFERENCES students(student_id)
            );
            
            CREATE TABLE IF NOT EXISTS roll_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_code TEXT NOT NULL,
                mode TEXT NOT NULL,
                strategy TEXT NOT NULL,
                selected_count INTEGER DEFAULT 0,
                started_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS roll_call_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_call_id INTEGER NOT NULL,
                student_id TEXT NOT NULL,
                order_index INTEGER NOT NULL,
                status TEXT NOT NULL,
                called_time TEXT NOT NULL,
                updated_time TEXT,
                note TEXT,
                FOREIGN KEY(roll_call_id) REFERENCES roll_calls(id),
                FOREIGN KEY(student_id) REFERENCES students(student_id)
            );
        """
    
    def _apply_migration(self, version: int, script: str) -> None:
        """应用迁移脚本"""
        import time
        
        try:
            self.db.execute_script(script)
            # 记录版本
            self.db.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (version, time.strftime("%Y-%m-%d %H:%M:%S")),
            )
            self.current_version = version
            print(f"[OK] Database migrated to version {version}")
        except Exception as e:
            print(f"[ERROR] Database migration to version {version} failed: {e}")
            raise
    
    def seed_sample_data(self) -> None:
        """填充示例数据（仅在数据库为空时）"""
        # 检查是否已有数据
        row = self.db.fetch_one("SELECT COUNT(*) FROM students")
        if row and row[0] > 0:
            return
        
        # 插入示例学生数据（25个学生）
        sample_students = [
            ("2023001", "唐小雨", "雨宝", "assets/images/students/student01.png", 3, 15),
            ("2023002", "唐小勇", None, "assets/images/students/student02.png", 0, 12),
            ("2023003", "唐小雅", "雅雅", "assets/images/students/student03.png", 1, 20),
            ("2023004", "唐小新", "小新", "assets/images/students/student04.png", 5, 5),
            ("2023005", "唐小敏", None, "assets/images/students/student05.png", 2, 18),
            ("2023006", "唐小波", "波波", "assets/images/students/student06.png", 4, 8),
            ("2023007", "唐小月", "小月", "assets/images/students/student07.png", 0, 22),
            ("2023008", "唐小杰", None, "assets/images/students/student08.png", 6, 4),
            ("2023009", "唐小青", "青青", "assets/images/students/student09.png", 1, 30),
            ("2023010", "唐小峰", "峰峰", "assets/images/students/student10.png", 0, 9),
            ("2023011", "唐小晨", "晨晨", "assets/images/students/student11.png", 2, 14),
            ("2023012", "唐小阳", None, "assets/images/students/student12.png", 1, 16),
            ("2023013", "唐小星", "星星", "assets/images/students/student13.png", 0, 19),
            ("2023014", "唐小云", "云云", "assets/images/students/student14.png", 3, 11),
            ("2023015", "唐小风", None, "assets/images/students/student15.png", 4, 7),
            ("2023016", "唐小雪", "小雪", "assets/images/students/student16.png", 2, 21),
            ("2023017", "唐小雷", "雷雷", "assets/images/students/student17.png", 1, 13),
            ("2023018", "唐小电", None, "assets/images/students/student18.png", 5, 6),
            ("2023019", "唐小光", "光光", "assets/images/students/student19.png", 0, 24),
            ("2023020", "唐小影", "影影", "assets/images/students/student20.png", 3, 10),
            ("2023021", "唐小音", None, "assets/images/students/student21.png", 2, 17),
            ("2023022", "唐小色", "色色", "assets/images/students/student22.png", 1, 15),
            ("2023023", "唐小香", "香香", "assets/images/students/student23.png", 4, 8),
            ("2023024", "唐小味", None, "assets/images/students/student24.png", 0, 23),
            ("2023025", "唐小触", "触触", "assets/images/students/student25.png", 2, 12),
        ]
        
        self.db.execute_many(
            """
            INSERT INTO students (student_id, name, nickname, photo_path, cut_count, called_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            sample_students,
        )
        
        # 插入示例请假数据
        sample_leaves = [
            ("2023003", "2024-11-20-AM", "2024-11-20 08:00", "2024-11-20 10:00", "校运动会"),
            ("2023005", "2024-11-20-AM", "2024-11-20 08:00", "2024-11-20 10:00", "身体不适"),
            ("2023007", "2024-11-20-PM", "2024-11-20 13:00", "2024-11-20 15:00", "学术竞赛"),
            ("2023009", "2024-11-21-AM", "2024-11-21 08:00", "2024-11-21 10:00", "实习面试"),
        ]
        
        self.db.execute_many(
            """
            INSERT INTO student_leaves (student_id, session_code, start_time, end_time, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            sample_leaves,
        )

