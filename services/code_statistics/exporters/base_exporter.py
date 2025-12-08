#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出器抽象基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from models.code_statistics import (
    Summary,
    PythonFunctionStats,
    CFunctionStats,
)


class Exporter(ABC):
    """导出器抽象基类"""
    
    @abstractmethod
    def export(
        self,
        target_dir: str,
        summary: Summary,
        by_language: Dict[str, Summary],
        elapsed_time: float,
        include_comment: bool,
        include_blank: bool,
        function_stats: Optional[PythonFunctionStats],
        c_function_stats: Optional[CFunctionStats],
        detail_table: Optional[Dict[str, Any]],
        base_filename: str,
        update_text_callback: Optional[callable] = None,
    ) -> Optional[str]:
        """
        导出结果
        
        Args:
            target_dir: 目标目录
            summary: 统计汇总
            by_language: 按语言统计
            elapsed_time: 耗时
            include_comment: 是否包含注释
            include_blank: 是否包含空行
            function_stats: Python函数统计
            c_function_stats: C/C++函数统计
            detail_table: 明细表数据
            base_filename: 基础文件名（不含扩展名）
            update_text_callback: 更新文本回调（用于错误提示）
        
        Returns:
            成功返回文件名，失败返回None
        """
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """获取文件扩展名（不含点）"""
        pass

