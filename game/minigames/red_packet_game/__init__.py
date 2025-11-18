#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
红包游戏模块
"""

from .game_manager import RedPacketGameManager
from .red_packet import RedPacket
from .spawner import RedPacketSpawner
from .collision_detector import RedPacketCollisionDetector
from .movement_controller import DucklingMovementController, RedPacketMovementController
from .statistics import RedPacketStatistics
from .renderer import RedPacketRenderer

__all__ = [
    'RedPacketGameManager',
    'RedPacket',
    'RedPacketSpawner',
    'RedPacketCollisionDetector',
    'DucklingMovementController',
    'RedPacketMovementController',
    'RedPacketStatistics',
    'RedPacketRenderer',
]

