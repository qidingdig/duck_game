#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一日志系统
"""

import logging
import sys
from typing import Optional

# 全局日志配置
_logger: Optional[logging.Logger] = None


def get_logger(name: str = "duck_game") -> logging.Logger:
    """获取日志记录器"""
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.INFO)
        
        # 避免重复添加handler
        if not _logger.handlers:
            # 控制台handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # 格式化
            formatter = logging.Formatter(
                '[%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            _logger.addHandler(console_handler)
    
    return _logger


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """配置日志系统"""
    logger = get_logger()
    logger.setLevel(level)
    
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

