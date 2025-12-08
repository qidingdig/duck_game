#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代码统计业务逻辑服务
"""

from typing import Dict, List, Optional, Set

from services.code_statistics.base import CodeCounterBase
from services.code_statistics.report_formatter import ReportFormatter
from models.code_statistics import (
    Summary,
    PythonFunctionStats,
    CFunctionStats,
)


class CodeStatisticsService:
    """代码统计业务逻辑服务"""
    
    def __init__(self, code_counter: CodeCounterBase):
        """
        初始化统计服务
        
        Args:
            code_counter: 代码统计器实例
        """
        self.code_counter = code_counter
        self.report_formatter = ReportFormatter()
    
    def execute_statistics(
        self,
        target_dir: str,
        selected_languages: Optional[Set[str]] = None,
        include_blank: bool = True,
        include_comment: bool = True,
        include_function_stats: bool = True,
        include_c_function_stats: bool = False,
    ) -> Dict:
        """
        执行代码统计
        
        Args:
            target_dir: 目标目录
            selected_languages: 选中的语言集合（None表示统计所有语言）
            include_blank: 是否包含空行统计
            include_comment: 是否包含注释统计
            include_function_stats: 是否包含Python函数统计
            include_c_function_stats: 是否包含C/C++函数统计
        
        Returns:
            包含统计结果的字典
        """
        # 构建包含模式
        include_patterns = []
        if selected_languages:
            ext_to_lang = self.code_counter.EXT_TO_LANGUAGE
            lang_to_exts: Dict[str, List[str]] = {}
            for ext, lang in ext_to_lang.items():
                lang_to_exts.setdefault(lang, []).append(ext)
            for lang in selected_languages:
                for ext in lang_to_exts.get(lang, []):
                    include_patterns.append(f"**/*{ext}")
        
        # 执行统计
        result = self.code_counter.count_code_by_language(
            target_dir, include=include_patterns if include_patterns else None
        )
        
        summary = result["summary"]
        by_language = result["by_language"]
        elapsed_time = result["elapsed_time"]
        
        # 如果指定了语言，过滤结果
        if selected_languages:
            by_language = {lang: stat for lang, stat in by_language.items() if lang in selected_languages}
        
        # 函数统计
        function_stats = None
        if include_function_stats:
            function_stats = self.code_counter.count_python_functions(target_dir)
        
        c_function_stats = None
        has_c_like_language = any(
            lang.lower() in {"c", "c++", "c/c++ header", "c++ header"} for lang in by_language.keys()
        )
        if include_c_function_stats or has_c_like_language:
            c_function_stats = self.code_counter.count_c_functions(target_dir)
        
        return {
            "summary": summary,
            "by_language": by_language,
            "by_ext": result["by_ext"],
            "per_file": result["per_file"],
            "elapsed_time": elapsed_time,
            "function_stats": function_stats,
            "c_function_stats": c_function_stats,
        }
    
    def format_report(
        self,
        target_dir: str,
        summary: Summary,
        by_language: Dict[str, Summary],
        elapsed_time: float,
        include_comment: bool,
        include_blank: bool,
        function_stats: Optional[PythonFunctionStats] = None,
        c_function_stats: Optional[CFunctionStats] = None,
    ) -> str:
        """
        格式化统计报告
        
        Returns:
            格式化后的报告字符串
        """
        return self.report_formatter.format_text_report(
            target_dir=target_dir,
            summary=summary,
            by_language=by_language,
            elapsed_time=elapsed_time,
            include_comment=include_comment,
            include_blank=include_blank,
            function_stats=function_stats,
            c_function_stats=c_function_stats,
        )

