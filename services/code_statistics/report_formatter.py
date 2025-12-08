#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
报告格式化器 - 负责格式化统计报告
"""

from typing import Dict, Set, Optional

from models.code_statistics import (
    Summary,
    PythonFunctionStats,
    CFunctionStats,
)


class ReportFormatter:
    """报告格式化器"""
    
    @staticmethod
    def format_text_report(
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
        格式化文本报告
        
        Returns:
            格式化后的报告字符串
        """
        report_lines = [
            "代码统计报告:",
            "=" * 50,
            f"统计目录: {target_dir}",
            f"总文件数: {summary.files}",
            f"总行数: {summary.total}",
            f"代码行数: {summary.code}",
        ]
        
        if include_comment:
            report_lines.append(f"注释行数: {summary.comment}")
        if include_blank:
            report_lines.append(f"空行数: {summary.blank}")
        
        report_lines.append(f"耗时: {elapsed_time:.3f} 秒\n")
        
        if by_language:
            header = f"{'语言':<20} {'文件数':<10} {'代码行数':<15}"
            if include_comment:
                header += f" {'注释行数':<15}"
            if include_blank:
                header += f" {'空行数':<15}"
            report_lines.append("按语言统计:")
            report_lines.append(header)
            report_lines.append("-" * 80)
            
            for lang, stat in sorted(by_language.items(), key=lambda x: -x[1].code):
                row = f"{lang:<20} {stat.files:<10} {stat.code:<15}"
                if include_comment:
                    row += f" {stat.comment:<15}"
                if include_blank:
                    row += f" {stat.blank:<15}"
                report_lines.append(row)
        else:
            report_lines.append("未找到匹配的代码文件。")
        
        # Python函数统计
        if function_stats and function_stats.total_functions > 0:
            report_lines.extend([
                "",
                "Python函数统计:",
                f"总函数数: {function_stats.total_functions}",
                f"平均长度: {function_stats.mean_length:.2f} 行",
                f"中位数长度: {function_stats.median_length:.2f} 行",
                f"最小长度: {function_stats.min_length} 行",
                f"最大长度: {function_stats.max_length} 行",
            ])
        
        # C/C++函数统计
        if c_function_stats and c_function_stats.total_functions > 0:
            report_lines.extend([
                "",
                "C/C++函数统计:",
                f"总函数数: {c_function_stats.total_functions}",
                f"平均长度: {c_function_stats.mean_length:.2f} 行",
                f"中位数长度: {c_function_stats.median_length:.2f} 行",
                f"最小长度: {c_function_stats.min_length} 行",
                f"最大长度: {c_function_stats.max_length} 行",
            ])
        
        return "\n".join(report_lines)

