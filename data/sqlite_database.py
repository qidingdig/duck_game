#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQLite数据库实现 - 实现DatabaseInterface接口
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator, List, Optional, Tuple

from data.database_interface import DatabaseInterface


class SQLiteDatabase(DatabaseInterface):
    """SQLite数据库实现"""
    
    def __init__(self, db_path: str):
        """
        初始化SQLite数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
    
    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """
        获取数据库连接（上下文管理器）
        
        Yields:
            sqlite3.Connection对象
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使用Row工厂，便于访问列
        try:
            yield conn
        finally:
            conn.close()
    
    def execute(self, query: str, params: Tuple = ()) -> int:
        """执行SQL语句"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """批量执行SQL语句"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
    
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Tuple]:
        """执行查询并返回单行结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return tuple(row) if row else None
    
    def fetch_all(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """执行查询并返回所有结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [tuple(row) for row in rows]
    
    def begin_transaction(self) -> None:
        """开始事务（SQLite自动事务，此方法保留接口一致性）"""
        pass
    
    def commit(self) -> None:
        """提交事务（在get_connection中自动处理）"""
        pass
    
    def rollback(self) -> None:
        """回滚事务"""
        if self._connection:
            self._connection.rollback()
    
    def execute_script(self, script: str) -> None:
        """执行SQL脚本"""
        with self.get_connection() as conn:
            conn.executescript(script)
            conn.commit()
    
    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """
        事务上下文管理器（用于需要手动控制事务的场景）
        
        Yields:
            sqlite3.Connection对象
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

