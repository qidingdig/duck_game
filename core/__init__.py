#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
核心系统模块 - 提供游戏的基础架构
"""

from .game_state import GameState, GameStateManager
from .event_system import GameEvent, EventManager
from .render_system import RenderLayer, RenderSystem
from .physics_system import CollisionDetector, MovementController

__all__ = [
    'GameState',
    'GameStateManager',
    'GameEvent',
    'EventManager',
    'RenderLayer',
    'RenderSystem',
    'CollisionDetector',
    'MovementController',
]

