#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
红包游戏管理器 - 协调所有组件
"""

import pygame
import time
from typing import List, Tuple, Optional, Callable
from .red_packet import RedPacket
from .spawner import RedPacketSpawner
from .collision_detector import RedPacketCollisionDetector
from .movement_controller import DucklingMovementController, RedPacketMovementController
from .statistics import RedPacketStatistics
from .renderer import RedPacketRenderer
from ..base_minigame import BaseMinigame
from core.event_system import EventManager, GameEvent


class RedPacketGameManager(BaseMinigame):
    """红包游戏管理器"""
    
    def __init__(
        self, screen: pygame.Surface, screen_width: int, screen_height: int,
        duckling_positions: List[Tuple[float, float]], duckling_size: int,
        donald_pos: Tuple[float, float], donald_size: int,
        event_manager: Optional[EventManager] = None,
        on_statistics_update: Optional[Callable[[str], None]] = None
    ):
        """
        初始化游戏管理器
        
        Args:
            screen: Pygame屏幕表面
            screen_width, screen_height: 屏幕尺寸
            duckling_positions: 小鸭位置列表（会被修改）
            duckling_size: 小鸭尺寸
            donald_pos: 唐老鸭位置
            donald_size: 唐老鸭尺寸
            event_manager: 事件管理器（可选）
            on_statistics_update: 统计更新回调（可选）
        """
        super().__init__()
        
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.duckling_positions = duckling_positions
        self.duckling_size = duckling_size
        self.donald_pos = donald_pos
        self.donald_size = donald_size
        self.event_manager = event_manager
        self.on_statistics_update = on_statistics_update
        
        # 游戏状态
        self.game_duration = 30.0  # 30秒
        self.game_start_time = 0.0
        self.red_packets: List[RedPacket] = []
        self.original_duckling_positions = duckling_positions.copy()
        
        # 初始化组件
        self.spawner = RedPacketSpawner(event_manager)
        self.spawner.set_spawn_position_strategy(self._get_spawn_position)
        
        self.collision_detector = RedPacketCollisionDetector(screen_width, screen_height)
        
        self.duckling_movement = DucklingMovementController(
            duckling_positions, screen_width, screen_height, duckling_size
        )
        
        self.packet_movement = RedPacketMovementController(screen_width, screen_height)
        
        self.statistics = RedPacketStatistics()
        
        self.renderer = RedPacketRenderer(screen)
        
        # 订阅事件
        if event_manager:
            event_manager.subscribe(GameEvent.RED_PACKET_CAUGHT, self._on_packet_caught)
            event_manager.subscribe(GameEvent.RED_PACKET_HIT_WALL, self._on_packet_hit_wall)
    
    def _get_spawn_position(self) -> Tuple[float, float]:
        """获取生成位置（从唐老鸭位置）"""
        start_x = self.donald_pos[0] + self.donald_size // 2
        start_y = self.donald_pos[1] + self.donald_size // 2
        return (start_x, start_y)
    
    def start(self, duration: float = 30.0, **kwargs):
        """
        开始游戏
        
        Args:
            duration: 游戏时长（秒）
        """
        self._active = True
        self.game_duration = duration
        self.game_start_time = time.time()
        self.red_packets.clear()
        self.statistics.reset()
        
        # 启动小鸭移动
        self.duckling_movement.start_movement()
        
        # 启动生成器
        self.spawner.resume()
        
        # 发布事件
        if self.event_manager:
            self.event_manager.emit(GameEvent.GAME_STARTED, {'game_type': 'red_packet'})
    
    def stop(self):
        """停止游戏"""
        self._active = False
        self.duckling_movement.stop_movement()
        self.spawner.pause()
        
        # 重置小鸭位置
        self.duckling_movement.reset_positions(self.original_duckling_positions)
        
        # 清理红包
        self.red_packets.clear()
        
        # 发布事件
        if self.event_manager:
            self.event_manager.emit(GameEvent.GAME_ENDED, {'game_type': 'red_packet'})
        
        # 显示统计报告
        if self.on_statistics_update:
            report = self.statistics.format_report()
            self.on_statistics_update(report)
    
    def update(self, dt: float = 1.0):
        """
        更新游戏逻辑
        
        Args:
            dt: 时间增量（秒）
        """
        if not self._active:
            return
        
        # 检查游戏是否结束
        elapsed = time.time() - self.game_start_time
        if elapsed >= self.game_duration:
            self.stop()
            return
        
        # 生成新红包
        new_packet = self.spawner.update(dt * 60)  # 转换为帧数
        if new_packet:
            self.red_packets.append(new_packet)
        
        # 更新小鸭位置
        self.duckling_movement.update(dt, self.donald_pos, self.donald_size)
        
        # 更新红包位置
        for packet in self.red_packets[:]:
            if not packet.is_active():
                continue
            
            self.packet_movement.update(packet, dt)
            
            # 检查碰撞
            # 1. 检查与小鸭碰撞
            duckling_idx = self.collision_detector.check_duckling_collision(
                packet, self.duckling_positions, self.duckling_size
            )
            if duckling_idx is not None:
                self.collision_detector.handle_collision(packet, 'duckling')
                self.statistics.record_packet_caught_by_duckling(duckling_idx, packet)
                if self.event_manager:
                    self.event_manager.emit(
                        GameEvent.DUCKLING_CAUGHT_PACKET,
                        {'duckling_idx': duckling_idx, 'packet': packet}
                    )
                self.red_packets.remove(packet)
                continue
            
            # 2. 检查墙壁碰撞
            if self.collision_detector.check_wall_collision(packet):
                self.collision_detector.handle_collision(packet, 'wall')
                self.statistics.record_packet_hit_wall(packet)
                if self.event_manager:
                    self.event_manager.emit(GameEvent.RED_PACKET_HIT_WALL, packet)
                self.red_packets.remove(packet)
    
    def render(self, screen: pygame.Surface):
        """
        渲染游戏
        
        Args:
            screen: Pygame屏幕表面
        """
        if not self._active:
            return
        
        self.renderer.render_all(self.red_packets)
    
    def is_active(self) -> bool:
        """是否激活"""
        return self._active
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        return self.statistics.get_total_stats()
    
    def get_remaining_time(self) -> float:
        """获取剩余时间（秒）"""
        if not self._active:
            return 0.0
        elapsed = time.time() - self.game_start_time
        return max(0.0, self.game_duration - elapsed)
    
    def _on_packet_caught(self, data):
        """处理红包被抢到事件"""
        pass
    
    def _on_packet_hit_wall(self, data):
        """处理红包碰壁事件"""
        pass

