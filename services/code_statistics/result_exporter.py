#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
结果导出管理器 - 使用策略模式管理各种导出器
"""

from typing import Dict, Optional, List, Any, Callable

from services.code_statistics.exporters import (
    Exporter,
    CSVExporter,
    JSONExporter,
    XLSXExporter,
)
from models.code_statistics import (
    Summary,
    PythonFunctionStats,
    CFunctionStats,
)


class ResultExporter:
    """结果导出管理器"""
    
    def __init__(self):
        """初始化导出器注册表"""
        self.exporters: Dict[str, Exporter] = {
            'csv': CSVExporter(),
            'json': JSONExporter(),
            'xlsx': XLSXExporter(),
        }
    
    def register_exporter(self, format_name: str, exporter: Exporter) -> None:
        """
        注册新的导出器
        
        Args:
            format_name: 格式名称（如 'csv', 'json', 'xlsx'）
            exporter: 导出器实例
        """
        self.exporters[format_name] = exporter
    
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
        formats: List[str],
        base_filename: str,
        update_text_callback: Optional[Callable[[str], None]] = None,
    ) -> List[str]:
        """
        导出结果到指定格式
        
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
            formats: 要导出的格式列表（如 ['csv', 'json']）
            base_filename: 基础文件名（不含扩展名）
            update_text_callback: 更新文本回调
        
        Returns:
            成功导出的文件名列表
        """
        saved_files = []
        
        for format_name in formats:
            exporter = self.exporters.get(format_name)
            if not exporter:
                if update_text_callback:
                    update_text_callback(f"不支持的导出格式: {format_name}\n")
                continue
            
            filename = exporter.export(
                target_dir=target_dir,
                summary=summary,
                by_language=by_language,
                elapsed_time=elapsed_time,
                include_comment=include_comment,
                include_blank=include_blank,
                function_stats=function_stats,
                c_function_stats=c_function_stats,
                detail_table=detail_table,
                base_filename=base_filename,
                update_text_callback=update_text_callback,
            )
            
            if filename:
                saved_files.append(filename)
        
        return saved_files

