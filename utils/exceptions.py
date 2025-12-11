#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一异常处理工具
"""

import traceback
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from utils.logger import get_logger

F = TypeVar('F', bound=Callable[..., Any])


def handle_exceptions(
    logger_name: Optional[str] = None,
    default_return: Any = None,
    reraise: bool = False
):
    """
    异常处理装饰器
    
    Args:
        logger_name: 日志记录器名称
        default_return: 异常时的默认返回值
        reraise: 是否重新抛出异常
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{func.__name__} 执行失败: {e}")
                logger.debug(traceback.format_exc())
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


def log_exception(logger_name: Optional[str] = None, message: Optional[str] = None):
    """
    记录异常的工具函数
    
    Args:
        logger_name: 日志记录器名称
        message: 自定义错误消息
    """
    logger = get_logger(logger_name or "duck_game")
    exc_type, exc_value, exc_traceback = traceback.sys.exc_info()
    error_msg = message or f"异常: {exc_type.__name__}: {exc_value}"
    logger.error(error_msg)
    logger.debug(traceback.format_exception(exc_type, exc_value, exc_traceback))

