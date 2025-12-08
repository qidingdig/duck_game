#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV导出器
"""

import csv
import os
from typing import Any, Dict, Optional

from services.code_statistics.exporters.base_exporter import Exporter
from models.code_statistics import (
    Summary,
    PythonFunctionStats,
    CFunctionStats,
)


class CSVExporter(Exporter):
    """CSV导出器"""
    
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
        """导出为CSV格式"""
        try:
            csv_filename = f"{base_filename}.csv"
            csv_path = os.path.join(target_dir, csv_filename)
            
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["统计项", "数值"])
                writer.writerow(["统计目录", target_dir])
                writer.writerow(["总文件数", summary.files])
                writer.writerow(["总行数", summary.total])
                writer.writerow(["代码行数", summary.code])
                if include_comment:
                    writer.writerow(["注释行数", summary.comment])
                if include_blank:
                    writer.writerow(["空行数", summary.blank])
                writer.writerow(["耗时(秒)", f"{elapsed_time:.3f}"])
                writer.writerow([])
                
                # 按语言统计表
                header = ["语言", "文件数", "代码行数"]
                if include_comment:
                    header.append("注释行数")
                if include_blank:
                    header.append("空行数")
                writer.writerow(header)
                
                for lang, stat in sorted(by_language.items(), key=lambda x: -x[1].code):
                    row = [lang, stat.files, stat.code]
                    if include_comment:
                        row.append(stat.comment)
                    if include_blank:
                        row.append(stat.blank)
                    writer.writerow(row)
                
                # Python函数统计
                if function_stats and function_stats.total_functions > 0:
                    writer.writerow([])
                    writer.writerow(["Python函数统计"])
                    writer.writerow(["总函数数", function_stats.total_functions])
                    writer.writerow(["平均长度", f"{function_stats.mean_length:.2f}"])
                    writer.writerow(["中位数长度", f"{function_stats.median_length:.2f}"])
                    writer.writerow(["最小长度", function_stats.min_length])
                    writer.writerow(["最大长度", function_stats.max_length])
                
                # C/C++函数统计
                if c_function_stats and c_function_stats.total_functions > 0:
                    writer.writerow([])
                    writer.writerow(["C/C++函数统计"])
                    writer.writerow(["总函数数", c_function_stats.total_functions])
                    writer.writerow(["平均长度", f"{c_function_stats.mean_length:.2f}"])
                    writer.writerow(["中位数长度", f"{c_function_stats.median_length:.2f}"])
                    writer.writerow(["最小长度", c_function_stats.min_length])
                    writer.writerow(["最大长度", c_function_stats.max_length])
                
                # 明细表
                if detail_table and detail_table.get("rows"):
                    writer.writerow([])
                    writer.writerow(["语言明细表"])
                    writer.writerow(detail_table["columns"])
                    for row in detail_table["rows"]:
                        writer.writerow(row)
            
            return csv_filename
        except Exception as exc:
            if update_text_callback:
                update_text_callback(f"保存 CSV 文件失败: {str(exc)}\n")
            return None
    
    def get_file_extension(self) -> str:
        return "csv"

