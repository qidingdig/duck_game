#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强代码统计工具
功能：
1. 统计任意目录下的代码，按语言分类
2. 图形化显示（柱状图、饼状图）
3. Python函数长度统计（均值、最大值、最小值、中位数）
"""

import os
import fnmatch
import ast
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FileStat:
    """文件统计类"""
    path: str
    total: int = 0
    code: int = 0
    comment: int = 0
    blank: int = 0

    def add_line(self, kind: str) -> None:
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


class AdvancedCodeCounter:
    """增强代码统计工具"""
    
    # 文件扩展名到语言名称的映射
    EXT_TO_LANGUAGE = {
        ".py": "Python",
        ".pyw": "Python",
        ".java": "Java",
        ".c": "C",
        ".cpp": "C++",
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",
        ".cs": "C#",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript React",
        ".jsx": "JavaScript React",
        ".vue": "Vue",
        ".go": "Go",
        ".rs": "Rust",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".php": "PHP",
        ".rb": "Ruby",
        ".sql": "SQL",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".less": "LESS",
        ".xml": "XML",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".sh": "Shell",
        ".bat": "Batch",
        ".cmd": "Batch",
        ".ps1": "PowerShell",
        ".m": "MATLAB",
        ".r": "R",
    }
    
    def __init__(self):
        # 单行注释符
        self.single_line_comments = {
            ".py": ["#"],
            ".pyw": ["#"],
            ".sh": ["#"],
            ".ps1": ["#"],
            ".psm1": ["#"],
            ".bat": ["::", "REM ", "rem "],
            ".cmd": ["::", "REM ", "rem "],
            ".c": ["//"],
            ".h": ["//"],
            ".cpp": ["//"],
            ".hpp": ["//"],
            ".cs": ["//"],
            ".java": ["//"],
            ".go": ["//"],
            ".js": ["//"],
            ".ts": ["//"],
            ".tsx": ["//"],
            ".jsx": ["//"],
            ".kt": ["//"],
            ".scala": ["//"],
            ".swift": ["//"],
            ".rs": ["//"],
            ".sql": ["--"],
            ".ini": [";", "#"],
            ".toml": ["#"],
            ".yaml": ["#"],
            ".yml": ["#"],
            ".m": ["%"],
            ".tex": ["%"],
            ".r": ["#"],
        }
        
        # 多行注释对
        self.multi_line_comments = {
            ".c": [("/*", "*/")],
            ".h": [("/*", "*/")],
            ".cpp": [("/*", "*/")],
            ".hpp": [("/*", "*/")],
            ".cs": [("/*", "*/")],
            ".java": [("/*", "*/")],
            ".go": [("/*", "*/")],
            ".js": [("/*", "*/")],
            ".ts": [("/*", "*/")],
            ".tsx": [("/*", "*/")],
            ".jsx": [("/*", "*/")],
            ".kt": [("/*", "*/")],
            ".scala": [("/*", "*/")],
            ".swift": [("/*", "*/")],
            ".rs": [("/*", "*/")],
            ".sql": [("/*", "*/")],
            ".css": [("/*", "*/")],
            ".scss": [("/*", "*/")],
            ".less": [("/*", "*/")],
            ".html": [("<!--", "-->")],
            ".htm": [("<!--", "-->")],
            ".xml": [("<!--", "-->")],
            ".vue": [("<!--", "-->")],
        }
        
        # 文本类型文件扩展名
        self.text_like_exts = set(self.single_line_comments.keys()) | set(self.multi_line_comments.keys()) | {
            ".txt", ".md", ".csv", ".tsv", ".cfg", ".conf", ".gradle", ".properties"
        }
        
        # 二进制文件魔术头
        self.binary_magic_prefixes = [
            b"\x00\x01", b"\xff\xd8\xff", b"PK\x03\x04", b"\x7fELF", b"\x89PNG", b"GIF8"
        ]
    
    def is_binary(self, path: str, sample_size: int = 4096) -> bool:
        """检查文件是否为二进制文件"""
        try:
            with open(path, "rb") as f:
                chunk = f.read(sample_size)
                if not chunk:
                    return False
                # UTF-16/UTF-8 BOM -> 文本
                if chunk.startswith(b"\xff\xfe") or chunk.startswith(b"\xfe\xff") or chunk.startswith(b"\xef\xbb\xbf"):
                    return False
                # 二进制魔术头 -> 二进制
                for mg in self.binary_magic_prefixes:
                    if chunk.startswith(mg):
                        return True
                # 非 BOM 情况出现 0x00 -> 倾向二进制
                if b"\x00" in chunk:
                    return True
                # 非文本字节比例启发式
                text_bytes = bytes(range(32, 127)) + b"\n\r\t\b\f\x1b"
                non_text = sum(1 for b in chunk if b not in text_bytes)
                return (non_text / max(1, len(chunk))) > 0.30
        except Exception:
            return True
    
    def detect_encoding(self, path: str) -> str:
        """检测文件编码"""
        try:
            with open(path, "rb") as f:
                head = f.read(4)
            if head.startswith(b"\xff\xfe") or head.startswith(b"\xfe\xff"):
                return "utf-16"
            if head.startswith(b"\xef\xbb\xbf"):
                return "utf-8-sig"
            return "utf-8"
        except Exception:
            return "utf-8"
    
    def iter_files(self, root: str, include: List[str], exclude: List[str]):
        """遍历文件"""
        norm_exclude = [p.replace("\\", "/") for p in exclude]
        norm_include = [p.replace("\\", "/") for p in include]
        
        if os.path.isfile(root):
            yield root
            return
        
        for dirpath, dirnames, filenames in os.walk(root):
            # 目录过滤
            dirnames[:] = [
                d for d in dirnames
                if not any(fnmatch.fnmatch(os.path.join(dirpath, d).replace("\\", "/"), pat) for pat in norm_exclude)
            ]
            for name in filenames:
                full = os.path.join(dirpath, name)
                norm_full = full.replace("\\", "/")
                if any(fnmatch.fnmatch(norm_full, pat) for pat in norm_exclude):
                    continue
                if norm_include and not any(fnmatch.fnmatch(norm_full, pat) for pat in norm_include):
                    continue
                yield full
    
    def classify_line(self, line: str, ext: str, in_block: Optional[Tuple[str, str]]) -> Tuple[str, Optional[Tuple[str, str]]]:
        """分类代码行"""
        s = line.rstrip("\n\r")
        stripped = s.lstrip()
        
        if len(stripped) == 0:
            return "blank", in_block
        
        pairs = self.multi_line_comments.get(ext, [])
        if in_block is not None:
            start, end = in_block
            if end in s:
                return "comment", None
            else:
                return "comment", in_block
        
        for start, end in pairs:
            start_pos = s.find(start)
            if start_pos != -1:
                end_pos = s.find(end, start_pos + len(start))
                if end_pos != -1:
                    before = s[:start_pos].strip()
                    after = s[end_pos + len(end):].strip()
                    if before or after:
                        return "code", None
                    else:
                        return "comment", None
                else:
                    return "comment", (start, end)
        
        for tok in self.single_line_comments.get(ext, []):
            if stripped.startswith(tok):
                return "comment", None
        
        return "code", None
    
    def count_file(self, path: str) -> Optional[FileStat]:
        """统计单个文件"""
        try:
            if self.is_binary(path):
                return None
            stat = FileStat(path=path)
            ext = os.path.splitext(path)[1].lower()
            in_block: Optional[Tuple[str, str]] = None
            encoding = self.detect_encoding(path)
            with open(path, "r", encoding=encoding, errors="replace") as f:
                for line in f:
                    kind, in_block = self.classify_line(line, ext, in_block)
                    stat.add_line(kind)
            return stat
        except Exception:
            return None
    
    def analyze_python_functions(self, path: str) -> List[FunctionStat]:
        """分析Python文件中的函数"""
        functions = []
        try:
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
        except Exception:
            pass
        
        return functions
    
    def count_python_functions(self, root: str, exclude: List[str] = None) -> PythonFunctionStats:
        """统计Python函数长度"""
        if exclude is None:
            exclude = ["**/.git/**", "**/.svn/**", "**/node_modules/**", "**/.venv/**", "**/dist/**", "**/build/**", "**/__pycache__/**"]
        
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
    
    def count_code_by_language(self, path: str = ".", include: List[str] = None, exclude: List[str] = None) -> Dict:
        """按语言统计代码量"""
        import time
        start_ts = time.perf_counter()
        
        if include is None:
            include = []
        if exclude is None:
            exclude = ["**/.git/**", "**/.svn/**", "**/node_modules/**", "**/.venv/**", "**/dist/**", "**/build/**"]
        
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


