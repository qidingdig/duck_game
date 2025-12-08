#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强代码统计工具
功能：
1. 统计任意目录下的代码，按语言分类
2. 图形化显示（柱状图、饼状图）
3. Python函数长度统计（均值、最大值、最小值、中位数）
4. C/C++函数长度统计
"""

import ast
import statistics
import re
import time
from typing import Dict, List, Optional

from services.code_statistics.base import CodeCounterBase
from models.code_statistics import (
    FileStat,
    Summary,
    FunctionStat,
    PythonFunctionStats,
    CFunctionStats,
)


class AdvancedCodeCounter(CodeCounterBase):
    """增强代码统计工具"""
    
    def analyze_python_functions(self, path: str) -> List[FunctionStat]:
        """分析Python文件中的函数"""
        functions = []
        try:
            # 确保路径是字符串类型
            if not isinstance(path, str):
                return functions
            
            if not path.endswith('.py'):
                return functions
            
            encoding = self.detect_encoding(path)
            with open(path, "r", encoding=encoding, errors="replace") as f:
                source = f.read()
            
            tree = ast.parse(source, filename=path)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # 计算函数行数
                    start_line = node.lineno
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else start_line
                    line_count = end_line - start_line + 1
                    
                    functions.append(FunctionStat(
                        name=node.name,
                        file_path=path,
                        line_count=line_count,
                        start_line=start_line,
                        end_line=end_line
                    ))
        except (OSError, IOError, PermissionError, UnicodeDecodeError):
            # 文件操作错误，返回空列表
            return functions
        except (SyntaxError, ValueError):
            # 语法错误或解析错误，返回空列表
            return functions
        except Exception:
            # 其他异常，返回空列表
            return functions
        
        return functions
    
    def count_python_functions(self, root: str, exclude: List[str] = None) -> PythonFunctionStats:
        """统计Python函数长度"""
        if exclude is None:
            exclude = list(self._default_exclude)
        
        all_functions = []
        
        for file_path in self.iter_files(root, ["**/*.py"], exclude):
            functions = self.analyze_python_functions(file_path)
            all_functions.extend(functions)
        
        if not all_functions:
            return PythonFunctionStats(
                total_functions=0,
                mean_length=0.0,
                median_length=0.0,
                min_length=0,
                max_length=0,
                functions=[]
            )
        
        lengths = [f.line_count for f in all_functions]
        
        return PythonFunctionStats(
            total_functions=len(all_functions),
            mean_length=statistics.mean(lengths),
            median_length=statistics.median(lengths),
            min_length=min(lengths),
            max_length=max(lengths),
            functions=all_functions
        )
    
    def analyze_c_functions(self, path: str) -> List[FunctionStat]:
        """分析C/C++文件中的函数"""
        functions = []
        try:
            # 确保路径是字符串类型
            if not isinstance(path, str):
                return functions
            
            # 检查文件扩展名
            ext = os.path.splitext(path)[1].lower()
            if ext not in ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp']:
                return functions
            
            encoding = self.detect_encoding(path)
            with open(path, "r", encoding=encoding, errors="replace") as f:
                content = f.read()
                lines = content.splitlines(True)  # 保留换行符
            
            if not lines:
                return functions
            
            # 使用更健壮的C函数检测方法
            # 先找到所有可能的函数定义位置，然后验证
            i = 0
            in_multiline_comment = False
            
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()
                
                # 处理多行注释
                if in_multiline_comment:
                    comment_end = stripped.find('*/')
                    if comment_end >= 0:
                        in_multiline_comment = False
                        # 检查注释后面是否还有代码
                        remaining = stripped[comment_end + 2:].strip()
                        if remaining:
                            line = remaining
                            stripped = remaining
                    else:
                        i += 1
                        continue
                else:
                    # 检查是否开始多行注释
                    comment_start = stripped.find('/*')
                    if comment_start >= 0:
                        comment_end = stripped.find('*/', comment_start + 2)
                        if comment_end < 0:
                            in_multiline_comment = True
                            # 移除注释前的部分
                            stripped = stripped[:comment_start].strip()
                            if not stripped:
                                i += 1
                                continue
                        else:
                            # 移除注释
                            stripped = stripped[:comment_start] + stripped[comment_end + 2:]
                            stripped = stripped.strip()
                
                # 跳过预处理指令、空行和单行注释
                if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                    i += 1
                    continue
                
                # 查找函数模式：函数名(参数) { 或 函数名(参数)\n{
                # 排除结构体、联合体、枚举等定义
                # 排除函数指针声明
                
                # 先检查是否是结构体/联合体/枚举定义
                if re.match(r'^\s*(struct|union|enum)\s+\w+', stripped):
                    i += 1
                    continue
                
                # 查找函数定义模式：返回类型 函数名(参数) {
                # 改进：匹配更复杂的返回类型和函数名
                func_match = re.search(r'(\w+)\s*\([^)]*\)\s*\{', line)
                if func_match:
                    func_name = func_match.group(1)
                    
                    # 检查函数名前面是否有返回类型标识符
                    # 简单检查：函数名前面应该有标识符（返回类型关键字或类型名）
                    func_start = func_match.start()
                    before_func = line[:func_start].strip()
                    
                    # 排除一些明显不是函数定义的情况
                    # 如：if (条件) {, while (条件) {, for (条件) {, switch (条件) {
                    if re.search(r'\b(if|while|for|switch|catch)\s*\(', before_func):
                        i += 1
                        continue
                    
                    # 排除函数指针：*func_name 或 (*func_name)
                    if re.search(r'[*&]\s*' + re.escape(func_name) + r'\s*\(', line[:func_match.start()]):
                        i += 1
                        continue
                    
                    # 找到函数体开始的大括号
                    brace_pos = line.find('{', func_match.end() - 1)
                    if brace_pos < 0:
                        # 可能是多行声明，查找下一行的{
                        i += 1
                        if i < len(lines):
                            next_line = lines[i].strip()
                            if next_line.startswith('{'):
                                brace_pos = 0
                                start_line = i + 1  # 函数体从下一行开始
                            else:
                                i -= 1
                                i += 1
                                continue
                        else:
                            i += 1
                            continue
                    else:
                        start_line = i + 1  # 行号从1开始
                    
                    # 找到匹配的结束大括号
                    brace_count = 1
                    current_line_idx = i
                    current_line_pos = brace_pos + 1
                    end_line = i
                    
                    # 逐字符扫描，跳过字符串、字符字面量和注释
                    in_string = False
                    in_char = False
                    string_char = None
                    escape_next = False
                    
                    while brace_count > 0 and current_line_idx < len(lines):
                        if current_line_pos >= len(lines[current_line_idx]):
                            current_line_idx += 1
                            current_line_pos = 0
                            if current_line_idx >= len(lines):
                                break
                            continue
                        
                        char = lines[current_line_idx][current_line_pos]
                        
                        if escape_next:
                            escape_next = False
                            current_line_pos += 1
                            continue
                        
                        if char == '\\':
                            escape_next = True
                            current_line_pos += 1
                            continue
                        
                        # 处理字符串
                        if char in ('"', "'") and not in_char and not in_string:
                            string_char = char
                            in_string = True
                            current_line_pos += 1
                            continue
                        elif char == string_char and in_string:
                            in_string = False
                            string_char = None
                            current_line_pos += 1
                            continue
                        
                        if in_string:
                            current_line_pos += 1
                            continue
                        
                        # 处理单行注释
                        if char == '/' and current_line_pos + 1 < len(lines[current_line_idx]):
                            if lines[current_line_idx][current_line_pos + 1] == '/':
                                # 跳到行尾
                                current_line_pos = len(lines[current_line_idx])
                                continue
                            elif lines[current_line_idx][current_line_pos + 1] == '*':
                                # 多行注释开始
                                current_line_pos += 2
                                while current_line_idx < len(lines):
                                    while current_line_pos < len(lines[current_line_idx]):
                                        if (lines[current_line_idx][current_line_pos] == '*' and 
                                            current_line_pos + 1 < len(lines[current_line_idx]) and
                                            lines[current_line_idx][current_line_pos + 1] == '/'):
                                            current_line_pos += 2
                                            break
                                        current_line_pos += 1
                                    if current_line_pos < len(lines[current_line_idx]):
                                        break
                                    current_line_idx += 1
                                    current_line_pos = 0
                                continue
                        
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_line = current_line_idx
                                break
                        
                        current_line_pos += 1
                    
                    if brace_count == 0:
                        # 成功找到函数体
                        line_count = end_line - start_line + 1
                        if line_count > 0:  # 确保是有效的函数
                            functions.append(FunctionStat(
                                name=func_name,
                                file_path=path,
                                line_count=line_count,
                                start_line=start_line,
                                end_line=end_line + 1
                            ))
                            i = end_line + 1
                            continue
                
                i += 1
                
        except (OSError, IOError, PermissionError, UnicodeDecodeError):
            # 文件操作错误，返回空列表
            return functions
        except Exception:
            # 其他异常，返回空列表
            return functions
        
        return functions
    
    def count_c_functions(self, root: str, exclude: List[str] = None) -> CFunctionStats:
        """统计C/C++函数长度"""
        if exclude is None:
            exclude = list(self._default_exclude)
        
        all_functions = []
        
        for file_path in self.iter_files(root, ["**/*.c", "**/*.cpp", "**/*.cc", "**/*.cxx", "**/*.h", "**/*.hpp"], exclude):
            functions = self.analyze_c_functions(file_path)
            all_functions.extend(functions)
        
        if not all_functions:
            return CFunctionStats(
                total_functions=0,
                mean_length=0.0,
                median_length=0.0,
                min_length=0,
                max_length=0,
                functions=[]
            )
        
        lengths = [f.line_count for f in all_functions]
        
        return CFunctionStats(
            total_functions=len(all_functions),
            mean_length=statistics.mean(lengths),
            median_length=statistics.median(lengths),
            min_length=min(lengths),
            max_length=max(lengths),
            functions=all_functions
        )
    
    def count_code_by_language(self, path: str = ".", include: List[str] = None, exclude: List[str] = None) -> Dict:
        """按语言统计代码量"""
        import os
        start_ts = time.perf_counter()
        
        if include is None:
            include = []
        if exclude is None:
            exclude = list(self._default_exclude)
        
        per_file: List[FileStat] = []
        for f in self.iter_files(path, include, exclude):
            st = self.count_file(f)
            if st is not None:
                per_file.append(st)
        
        summary = Summary()
        by_language: Dict[str, Summary] = {}
        by_ext: Dict[str, Summary] = {}
        
        for st in per_file:
            summary.add(st)
            ext = os.path.splitext(st.path)[1].lower() or "<noext>"
            
            # 按扩展名统计
            by_ext.setdefault(ext, Summary())
            by_ext[ext].add(st)
            
            # 按语言统计
            language = self.EXT_TO_LANGUAGE.get(ext, "Other")
            by_language.setdefault(language, Summary())
            by_language[language].add(st)
        
        elapsed_s = time.perf_counter() - start_ts
        
        return {
            "summary": summary,
            "by_language": by_language,
            "by_ext": by_ext,
            "per_file": per_file,
            "elapsed_time": elapsed_s
        }

