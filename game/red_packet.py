#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
红包系统 - 三种不同大小形状的红包
"""

import pygame
import math
import random

class RedPacket:
    """红包类"""
    
    def __init__(self, x, y, packet_type=0):
        self.x = x
        self.y = y
        self.packet_type = packet_type  # 0: 小红包, 1: 中红包, 2: 大红包
        
        # 根据类型设置大小和颜色
        self.sizes = [(30, 40), (50, 60), (70, 80)]
        self.colors = [(255, 0, 0), (255, 100, 100), (200, 0, 0)]
        self.amounts = [(1, 10), (10, 50), (50, 100)]  # 金额范围
        
        self.width, self.height = self.sizes[self.packet_type]
        self.color = self.colors[self.packet_type]
        
        # 随机生成金额
        min_amount, max_amount = self.amounts[self.packet_type]
        self.amount = round(random.uniform(min_amount, max_amount), 2)
        
        # 移动相关
        self.speed = random.uniform(2, 5)
        self.angle = random.uniform(0, 2 * math.pi)
        self.dx = math.cos(self.angle) * self.speed
        self.dy = math.sin(self.angle) * self.speed
        
        # 状态
        self.active = True
        self.hit_wall = False
        self.rotation = 0
        self.rotation_speed = random.uniform(-5, 5)
    
    def update(self, screen_width, screen_height):
        """更新红包状态"""
        if not self.active or self.hit_wall:
            return
        
        # 移动
        self.x += self.dx
        self.y += self.dy
        
        # 旋转
        self.rotation += self.rotation_speed
        
        # 检查边界碰撞
        if (self.x <= 0 or self.x >= screen_width - self.width or
            self.y <= 0 or self.y >= screen_height - self.height):
            self.hit_wall = True
            self.active = False
    
    def render(self, screen):
        """渲染红包"""
        if not self.active:
            return
        
        # 创建旋转后的红包表面
        packet_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # 绘制红包形状（根据类型绘制不同形状）
        if self.packet_type == 0:  # 小红包 - 矩形
            pygame.draw.rect(packet_surface, self.color, (0, 0, self.width, self.height))
            pygame.draw.rect(packet_surface, (0, 0, 0), (0, 0, self.width, self.height), 2)
        elif self.packet_type == 1:  # 中红包 - 圆角矩形
            pygame.draw.rect(packet_surface, self.color, (0, 0, self.width, self.height), 
                           border_radius=10)
            pygame.draw.rect(packet_surface, (0, 0, 0), (0, 0, self.width, self.height), 
                           2, border_radius=10)
        else:  # 大红包 - 椭圆
            pygame.draw.ellipse(packet_surface, self.color, (0, 0, self.width, self.height))
            pygame.draw.ellipse(packet_surface, (0, 0, 0), (0, 0, self.width, self.height), 2)
        
        # 绘制装饰线条
        pygame.draw.line(packet_surface, (255, 255, 0), 
                        (0, self.height // 2), (self.width, self.height // 2), 2)
        
        # 绘制金额
        font = pygame.font.Font(None, 16)
        amount_text = f"¥{self.amount}"
        text_surface = font.render(amount_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2))
        packet_surface.blit(text_surface, text_rect)
        
        # 旋转并绘制到屏幕
        if self.rotation != 0:
            rotated_surface = pygame.transform.rotate(packet_surface, self.rotation)
            rect = rotated_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
            screen.blit(rotated_surface, rect)
        else:
            screen.blit(packet_surface, (self.x, self.y))
    
    def get_rect(self):
        """获取红包矩形区域"""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_amount(self):
        """获取红包金额"""
        return self.amount
    
    def get_type(self):
        """获取红包类型"""
        return self.packet_type

class RedPacketManager:
    """红包管理器"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.red_packets = []
        self.statistics = {
            'total_count': 0,
            'total_amount': 0.0,
            'type_counts': [0, 0, 0],
            'type_amounts': [0.0, 0.0, 0.0]
        }
        self.game_active = False
        self.spawn_timer = 0
        self.spawn_interval = 30  # 每30帧生成一个红包
    
    def start_game(self):
        """开始红包游戏"""
        self.game_active = True
        self.red_packets.clear()
        self.statistics = {
            'total_count': 0,
            'total_amount': 0.0,
            'type_counts': [0, 0, 0],
            'type_amounts': [0.0, 0.0, 0.0]
        }
        self.spawn_timer = 0
    
    def stop_game(self):
        """停止红包游戏"""
        self.game_active = False
    
    def update(self):
        """更新红包管理器"""
        if not self.game_active:
            return
        
        # 生成新红包
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_red_packet()
            self.spawn_timer = 0
        
        # 更新所有红包
        for packet in self.red_packets[:]:
            packet.update(self.screen_width, self.screen_height)
            if not packet.active:
                # 统计碰壁的红包
                if packet.hit_wall:
                    self.statistics['total_count'] += 1
                    self.statistics['total_amount'] += packet.get_amount()
                    self.statistics['type_counts'][packet.get_type()] += 1
                    self.statistics['type_amounts'][packet.get_type()] += packet.get_amount()
                self.red_packets.remove(packet)
    
    def spawn_red_packet(self):
        """生成新红包"""
        # 从屏幕边缘随机位置生成
        side = random.randint(0, 3)
        if side == 0:  # 上边
            x = random.randint(0, self.screen_width)
            y = -50
        elif side == 1:  # 右边
            x = self.screen_width + 50
            y = random.randint(0, self.screen_height)
        elif side == 2:  # 下边
            x = random.randint(0, self.screen_width)
            y = self.screen_height + 50
        else:  # 左边
            x = -50
            y = random.randint(0, self.screen_height)
        
        # 随机选择红包类型
        packet_type = random.randint(0, 2)
        packet = RedPacket(x, y, packet_type)
        self.red_packets.append(packet)
    
    def render(self, screen):
        """渲染所有红包"""
        for packet in self.red_packets:
            packet.render(screen)
    
    def get_statistics(self):
        """获取统计信息"""
        return self.statistics.copy()
    
    def get_statistics_text(self):
        """获取统计信息文本"""
        stats = self.get_statistics()
        text = f"红包游戏统计:\n"
        text += f"总红包数: {stats['total_count']}\n"
        text += f"总金额: ¥{stats['total_amount']:.2f}\n"
        text += f"小红包: {stats['type_counts'][0]}个, ¥{stats['type_amounts'][0]:.2f}\n"
        text += f"中红包: {stats['type_counts'][1]}个, ¥{stats['type_amounts'][1]:.2f}\n"
        text += f"大红包: {stats['type_counts'][2]}个, ¥{stats['type_amounts'][2]:.2f}\n"
        return text
