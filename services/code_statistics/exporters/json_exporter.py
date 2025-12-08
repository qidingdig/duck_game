#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSON导出器
"""

import json
import os
from typing import Any, Dict, Optional

from services.code_statistics.exporters.base_exporter import Exporter
from models.code_statistics import (
    Summary,
    PythonFunctionStats,
    CFunctionStats,
)


class JSONExporter(Exporter):
    """JSON导出器"""
    
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
        """导出为JSON格式"""
        try:
            json_filename = f"{base_filename}.json"
            json_path = os.path.join(target_dir, json_filename)
            
            save_data = {
                "summary": {
                    "target_dir": target_dir,
                    "files": summary.files,
                    "total": summary.total,
                    "code": summary.code,
                    "comment": summary.comment if include_comment else None,
                    "blank": summary.blank if include_blank else None,
                    "elapsed_time": elapsed_time,
                },
                "by_language": {},
            }
            
            for lang, stat in by_language.items():
                lang_data = {"files": stat.files, "code": stat.code}
                if include_comment:
                    lang_data["comment"] = stat.comment
                if include_blank:
                    lang_data["blank"] = stat.blank
                save_data["by_language"][lang] = lang_data
            
            if function_stats and function_stats.total_functions > 0:
                save_data["python_functions"] = {
                    "total_functions": function_stats.total_functions,
                    "mean_length": function_stats.mean_length,
                    "median_length": function_stats.median_length,
                    "min_length": function_stats.min_length,
                    "max_length": function_stats.max_length,
                }
            
            if c_function_stats and c_function_stats.total_functions > 0:
                save_data["c_functions"] = {
                    "total_functions": c_function_stats.total_functions,
                    "mean_length": c_function_stats.mean_length,
                    "median_length": c_function_stats.median_length,
                    "min_length": c_function_stats.min_length,
                    "max_length": c_function_stats.max_length,
                }
            
            if detail_table and detail_table.get("rows"):
                save_data["detail_table"] = detail_table
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            return json_filename
        except Exception as exc:
            if update_text_callback:
                update_text_callback(f"保存 JSON 文件失败: {str(exc)}\n")
            return None
    
    def get_file_extension(self) -> str:
        return "json"

