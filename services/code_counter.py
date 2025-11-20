#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代码统计服务 - 基于之前的代码统计功能
"""

import os
import fnmatch
import time
from typing import Dict, List, Optional, Tuple

class FileStat:
    """文件统计类"""
    def __init__(self, path: str):
        self.path = path
        self.total = 0
        self.code = 0
        self.comment = 0
        self.blank = 0

    def add_line(self, kind: str) -> None:
        self.total += 1
        if kind == "code":
            self.code += 1
        elif kind == "comment":
            self.comment += 1
        elif kind == "blank":
            self.blank += 1

class Summary:
    """统计汇总类"""
    def __init__(self):
        self.files = 0
        self.total = 0
        self.code = 0
        self.comment = 0
        self.blank = 0

    def add(self, stat: FileStat) -> None:
        self.files += 1
        self.total += stat.total
        self.code += stat.code
        self.comment += stat.comment
        self.blank += stat.blank

class CodeCounter:
    """代码统计服务"""
    
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
    
    def count_code_lines(self, path: str = ".", include: List[str] = None, exclude: List[str] = None) -> str:
        """统计代码行数"""
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
        by_ext: Dict[str, Summary] = {}
        
        for st in per_file:
            summary.add(st)
            ext = os.path.splitext(st.path)[1].lower() or "<noext>"
            by_ext.setdefault(ext, Summary())
            by_ext[ext].add(st)
        
        elapsed_s = time.perf_counter() - start_ts
        
        # 生成统计报告
        result = f"代码统计报告:\n"
        result += f"总文件数: {summary.files}\n"
        result += f"总行数: {summary.total}\n"
        result += f"代码行数: {summary.code}\n"
        result += f"注释行数: {summary.comment}\n"
        result += f"空行数: {summary.blank}\n"
        result += f"耗时: {elapsed_s:.3f} 秒\n\n"
        
        # 按文件类型统计
        if by_ext:
            result += "按文件类型统计:\n"
            for ext, sm in sorted(by_ext.items(), key=lambda x: (-x[1].code, x[0])):
                result += f"{ext}: {sm.files}个文件, {sm.code}行代码\n"
        
        return result
