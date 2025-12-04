#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库抽象接口层 - 定义数据库操作的抽象接口
遵循依赖倒置原则：高层模块依赖抽象而非具体实现
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Tuple


class DatabaseInterface(ABC):
    """数据库接口抽象基类"""
    
    @abstractmethod
    @contextmanager
    def get_connection(self) -> Iterator[Any]:
        """
        获取数据库连接（上下文管理器）
        
        Yields:
            数据库连接对象
        """
        pass
    
    @abstractmethod
    def execute(self, query: str, params: Tuple = ()) -> int:
        """
        执行SQL语句（INSERT/UPDATE/DELETE）
        
        Args:
            query: SQL语句
            params: 参数元组
        
        Returns:
            受影响的行数
        """
        pass
    
    @abstractmethod
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        批量执行SQL语句
        
        Args:
            query: SQL语句
            params_list: 参数列表
        
        Returns:
            受影响的行数
        """
        pass
    
    @abstractmethod
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Tuple]:
        """
        执行查询并返回单行结果
        
        Args:
            query: SQL语句
            params: 参数元组
        
        Returns:
            单行结果元组，如果没有结果返回None
        """
        pass
    
    @abstractmethod
    def fetch_all(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """
        执行查询并返回所有结果
        
        Args:
            query: SQL语句
            params: 参数元组
        
        Returns:
            结果列表
        """
        pass
    
    @abstractmethod
    def begin_transaction(self) -> None:
        """开始事务"""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """提交事务"""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """回滚事务"""
        pass
    
    @abstractmethod
    def execute_script(self, script: str) -> None:
        """
        执行SQL脚本（用于创建表等）
        
        Args:
            script: SQL脚本内容
        """
        pass

