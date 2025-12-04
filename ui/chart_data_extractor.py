#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图表数据提取器 - 从统计结果中提取图表所需的数据。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ChartDataExtractor:
    """从代码统计结果中提取图表数据"""
    
    @staticmethod
    def extract_language_data(code_result: Dict[str, Any]) -> Dict[str, List]:
        """
        从代码统计结果中提取语言数据
        
        Returns:
            {'labels': [...], 'values': [...]}
        """
        labels = []
        values = []
        
        try:
            if isinstance(code_result, dict) and "by_language" in code_result:
                by_language = code_result["by_language"]
                for lang, stat in by_language.items():
                    code_lines = ChartDataExtractor._extract_code_lines(stat)
                    if code_lines is not None and code_lines > 0:
                        labels.append(str(lang))
                        values.append(int(code_lines))
            elif hasattr(code_result, "items"):
                for lang, stat in code_result.items():
                    if lang in {"summary", "elapsed_time"}:
                        continue
                    code_lines = ChartDataExtractor._extract_code_lines(stat)
                    if code_lines is not None and code_lines > 0:
                        labels.append(str(lang))
                        values.append(int(code_lines))
        except Exception as exc:
            print(f"[ChartDataExtractor] 解析代码统计数据错误: {exc}")
            return {"labels": [], "values": []}
        
        # 按值降序排序
        if labels:
            sorted_data = sorted(zip(labels, values), key=lambda x: -x[1])
            labels = [lang for lang, _ in sorted_data]
            values = [val for _, val in sorted_data]
        
        return {"labels": labels, "values": values}
    
    @staticmethod
    def _extract_code_lines(stat: Any) -> Optional[int]:
        """从统计对象中提取代码行数"""
        if hasattr(stat, "code"):
            return getattr(stat, "code")
        elif isinstance(stat, dict) and "code" in stat:
            return stat["code"]
        elif isinstance(stat, (int, float)):
            return int(stat)
        return None
    
    @staticmethod
    def extract_function_stats(function_stats: Optional[Any]) -> Dict[str, Any]:
        """
        从函数统计对象中提取数据
        
        Returns:
            {
                'lengths': [...],
                'summary': {'均值': ..., '中位数': ..., '最小值': ..., '最大值': ...}
            }
        """
        lengths = []
        summary_vals = {
            "均值": 0,
            "中位数": 0,
            "最小值": 0,
            "最大值": 0,
        }
        
        if not function_stats:
            return {"lengths": lengths, "summary": summary_vals}
        
        try:
            # 提取函数长度列表
            if hasattr(function_stats, "functions"):
                funcs = getattr(function_stats, "functions")
                for item in funcs:
                    length = ChartDataExtractor._extract_function_length(item)
                    if length is not None:
                        lengths.append(length)
            elif isinstance(function_stats, dict) and "functions" in function_stats:
                for item in function_stats["functions"]:
                    length = ChartDataExtractor._extract_function_length(item)
                    if length is not None:
                        lengths.append(length)
            
            # 提取统计摘要
            if hasattr(function_stats, "mean_length"):
                summary_vals["均值"] = getattr(function_stats, "mean_length", 0) or 0
                summary_vals["中位数"] = getattr(function_stats, "median_length", 0) or 0
                summary_vals["最小值"] = getattr(function_stats, "min_length", 0) or 0
                summary_vals["最大值"] = getattr(function_stats, "max_length", 0) or 0
            elif isinstance(function_stats, dict) and "summary" in function_stats:
                info = function_stats["summary"]
                summary_vals["均值"] = info.get("mean", 0) or 0
                summary_vals["中位数"] = info.get("median", 0) or 0
                summary_vals["最小值"] = info.get("min", 0) or 0
                summary_vals["最大值"] = info.get("max", 0) or 0
        except Exception:
            pass
        
        return {"lengths": lengths, "summary": summary_vals}
    
    @staticmethod
    def _extract_function_length(item: Any) -> Optional[int]:
        """从函数对象中提取长度"""
        if hasattr(item, "line_count"):
            return int(getattr(item, "line_count"))
        elif hasattr(item, "length"):
            return int(getattr(item, "length"))
        elif isinstance(item, dict):
            if "line_count" in item:
                return int(item["line_count"])
            elif "length" in item:
                return int(item["length"])
        return None

