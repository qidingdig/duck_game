#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
红包渲染器
"""

import pygame
from typing import List
from .red_packet import RedPacket


class RedPacketRenderer:
    """红包渲染器"""
    
    def __init__(self, screen: pygame.Surface):
        """
        初始化渲染器
        
        Args:
            screen: Pygame屏幕表面
        """
        self.screen = screen
        self.font = pygame.font.Font(None, 16)
    
    def render_packet(self, packet: RedPacket):
        """
        渲染单个红包
        
        Args:
            packet: 红包对象
        """
        if not packet.is_active():
            return
        
        x, y = packet.get_position()
        width, height = packet.width, packet.height
        color = packet.color
        
        # 绘制红包矩形
        packet_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, color, packet_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), packet_rect, 2)
        
        # 绘制金额
        self.render_amount(packet)
    
    def render_amount(self, packet: RedPacket):
        """
        渲染金额文字
        
        Args:
            packet: 红包对象
        """
        x, y = packet.get_position()
        width, height = packet.width, packet.height
        amount = packet.get_amount()
        
        amount_text = self.font.render(f"¥{amount}", True, (255, 255, 255))
        text_rect = amount_text.get_rect(
            center=(x + width // 2, y + height // 2)
        )
        self.screen.blit(amount_text, text_rect)
    
    def render_all(self, packets: List[RedPacket]):
        """
        渲染所有红包
        
        Args:
            packets: 红包列表
        """
        for packet in packets:
            self.render_packet(packet)

