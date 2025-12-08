#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代码统计相关数据模型
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class FileStat:
    """文件统计类"""
    path: str
    total: int = 0
    code: int = 0
    comment: int = 0
    blank: int = 0

    def add_line(self, kind: str) -> None:
        """添加一行统计"""
        self.total += 1
        if kind == "code":
            self.code += 1
        elif kind == "comment":
            self.comment += 1
        elif kind == "blank":
            self.blank += 1


@dataclass
class Summary:
    """统计汇总类"""
    files: int = 0
    total: int = 0
    code: int = 0
    comment: int = 0
    blank: int = 0

    def add(self, stat: FileStat) -> None:
        """添加文件统计到汇总"""
        self.files += 1
        self.total += stat.total
        self.code += stat.code
        self.comment += stat.comment
        self.blank += stat.blank


@dataclass
class FunctionStat:
    """函数统计类"""
    name: str
    file_path: str
    line_count: int
    start_line: int
    end_line: int


@dataclass
class PythonFunctionStats:
    """Python函数统计汇总"""
    total_functions: int
    mean_length: float
    median_length: float
    min_length: int
    max_length: int
    functions: List[FunctionStat]


@dataclass
class CFunctionStats:
    """C/C++函数统计汇总"""
    total_functions: int
    mean_length: float
    median_length: float
    min_length: int
    max_length: int
    functions: List[FunctionStat]


@dataclass
class StatisticsResult:
    """统计结果数据模型"""
    summary: Summary
    by_language: Dict[str, Summary]
    by_ext: Dict[str, Summary]
    per_file: List[FileStat]
    elapsed_time: float
    python_function_stats: Optional[PythonFunctionStats] = None
    c_function_stats: Optional[CFunctionStats] = None

