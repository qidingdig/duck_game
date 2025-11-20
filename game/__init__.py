#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
游戏逻辑层模块。
"""

from game.duck_game import DuckGame
from game.characters import Duckling
from game.command_processor import CommandProcessor, CommandHandler, PatternCommandHandler

__all__ = [
    "DuckGame",
    "Duckling",
    "CommandProcessor",
    "CommandHandler",
    "PatternCommandHandler",
]