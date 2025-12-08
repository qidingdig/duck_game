#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代码统计基础类 - 包含公共功能
"""

import os
import fnmatch
from typing import Dict, List, Optional, Tuple

from models.code_statistics import FileStat


class CodeCounterBase:
    """代码统计基础类，包含公共功能"""
    
    # 文件扩展名到语言名称的映射
    EXT_TO_LANGUAGE = {
        ".py": "Python",
        ".pyw": "Python",
        ".pyi": "Python Stub",
        ".pyx": "Cython",
        ".pxd": "Cython Header",
        ".pxi": "Cython Include",
        ".java": "Java",
        ".c": "C",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",
        ".hh": "C++ Header",
        ".hin": "C/C++ Header",
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
        ".pcss": "PostCSS",
        ".postcss": "PostCSS",
        ".scss": "SCSS",
        ".less": "LESS",
        ".xml": "XML",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".cfg": "Config",
        ".conf": "Config",
        ".properties": "Properties",
        ".toml": "TOML",
        ".gradle": "Gradle",
        ".md": "Markdown",
        ".markdown": "Markdown",
        ".rst": "reStructuredText",
        ".tex": "TeX",
        ".sty": "TeX",
        ".cls": "TeX",
        ".csv": "CSV",
        ".tsv": "TSV",
        ".txt": "Text",
        ".mk": "Makefile",
        ".make": "Makefile",
        ".gmk": "Makefile",
        ".thrift": "Thrift",
        ".ps1": "PowerShell",
        ".psm1": "PowerShell",
        ".sh": "Shell",
        ".bash": "Shell",
        ".zsh": "Shell",
        ".bat": "Batch",
        ".cmd": "Batch",
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
        self.text_like_exts = (
            set(self.single_line_comments.keys())
            | set(self.multi_line_comments.keys())
            | set(self.EXT_TO_LANGUAGE.keys())
            | {
                ".txt",
                ".md",
                ".csv",
                ".tsv",
                ".cfg",
                ".conf",
                ".gradle",
                ".properties",
            }
        )

        self._default_exclude = [
            "**/.git/**",
            "**/.svn/**",
            "**/node_modules/**",
            "**/.venv/**",
            "**/dist/**",
            "**/build/**",
            "**/__pycache__/**",
            "**/.vscode/**",
            "**/.VSCodeCounter/**",
        ]
        
        # 二进制文件魔术头
        self.binary_magic_prefixes = [
            b"\x00\x01", b"\xff\xd8\xff", b"PK\x03\x04", b"\x7fELF", b"\x89PNG", b"GIF8"
        ]
    
    def is_binary(self, path: str, sample_size: int = 4096) -> bool:
        """检查文件是否为二进制文件"""
        try:
            # 确保路径是字符串类型，避免线程安全问题
            if not isinstance(path, str):
                return True
            if not os.path.exists(path):
                return True
            
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
        except (OSError, IOError, PermissionError, UnicodeDecodeError):
            # 文件无法读取时，保守地认为是二进制文件
            return True
        except Exception:
            # 其他异常也保守处理
            return True
    
    def detect_encoding(self, path: str) -> str:
        """检测文件编码"""
        try:
            # 确保路径是字符串类型，避免线程安全问题
            if not isinstance(path, str):
                return "utf-8"
            if not os.path.exists(path):
                return "utf-8"
            
            with open(path, "rb") as f:
                head = f.read(4)
            if head.startswith(b"\xff\xfe") or head.startswith(b"\xfe\xff"):
                return "utf-16"
            if head.startswith(b"\xef\xbb\xbf"):
                return "utf-8-sig"
            return "utf-8"
        except (OSError, IOError, PermissionError):
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
            # 确保路径是字符串类型
            if not isinstance(path, str):
                return None
            
            ext = os.path.splitext(path)[1].lower()
            # 对于常见文本/源码扩展名跳过二进制检测，以免误判
            if ext not in self.text_like_exts and self.is_binary(path):
                return None
            stat = FileStat(path=path)
            in_block: Optional[Tuple[str, str]] = None
            encoding = self.detect_encoding(path)
            with open(path, "r", encoding=encoding, errors="replace") as f:
                for line in f:
                    kind, in_block = self.classify_line(line, ext, in_block)
                    stat.add_line(kind)
            return stat
        except (OSError, IOError, PermissionError, UnicodeDecodeError):
            return None
        except Exception:
            return None

