#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
角色系统 - 唐老鸭和唐小鸭
"""

import pygame
import math
import random

class Character:
    """角色基类"""
    
    def __init__(self, x, y, width, height, color, name):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.name = name
        self.original_x = x
        self.original_y = y
        
        # 动画相关
        self.animating = False
        self.animation_speed = 2
        self.animation_direction = 1
        self.bounce_height = 10
        self.original_bounce = 0
        
        # 移动相关
        self.moving = False
        self.move_speed = 3
        self.target_x = x
        self.target_y = y
        
        # 状态
        self.active = True
    
    def update(self):
        """更新角色状态"""
        if not self.active:
            return
        
        # 处理移动动画
        if self.moving:
            self.update_movement()
        
        # 处理弹跳动画
        if self.animating:
            self.update_bounce()
    
    def update_movement(self):
        """更新移动状态"""
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < self.move_speed:
            self.x = self.target_x
            self.y = self.target_y
            self.moving = False
        else:
            self.x += (dx / distance) * self.move_speed
            self.y += (dy / distance) * self.move_speed
    
    def update_bounce(self):
        """更新弹跳动画"""
        self.original_bounce += self.animation_direction * self.animation_speed
        if abs(self.original_bounce) >= self.bounce_height:
            self.animation_direction *= -1
    
    def move_to(self, x, y):
        """移动到指定位置"""
        self.target_x = x
        self.target_y = y
        self.moving = True
    
    def start_bounce(self):
        """开始弹跳动画"""
        self.animating = True
        self.original_bounce = 0
        self.animation_direction = 1
    
    def stop_bounce(self):
        """停止弹跳动画"""
        self.animating = False
        self.original_bounce = 0
    
    def reset_position(self):
        """重置到原始位置"""
        self.x = self.original_x
        self.y = self.original_y
        self.target_x = self.original_x
        self.target_y = self.original_y
        self.moving = False
        self.stop_bounce()
    
    def render(self, screen):
        """渲染角色"""
        if not self.active:
            return
        
        # 计算实际渲染位置（包含弹跳效果）
        render_y = self.y - self.original_bounce
        
        # 绘制角色身体
        pygame.draw.ellipse(screen, self.color, 
                          (self.x, render_y, self.width, self.height))
        
        # 绘制角色边框
        pygame.draw.ellipse(screen, (0, 0, 0), 
                          (self.x, render_y, self.width, self.height), 2)
        
        # 绘制眼睛
        eye_size = 8
        eye_y = render_y + self.height // 3
        pygame.draw.circle(screen, (0, 0, 0), 
                         (self.x + self.width // 3, eye_y), eye_size)
        pygame.draw.circle(screen, (0, 0, 0), 
                         (self.x + 2 * self.width // 3, eye_y), eye_size)
        
        # 绘制嘴巴
        mouth_y = render_y + 2 * self.height // 3
        pygame.draw.arc(screen, (0, 0, 0), 
                       (self.x + self.width // 4, mouth_y - 5, 
                        self.width // 2, 10), 0, math.pi, 2)
        
        # 绘制名字
        font = pygame.font.Font(None, 24)
        text = font.render(self.name, True, (0, 0, 0))
        text_rect = text.get_rect(center=(self.x + self.width // 2, render_y - 20))
        screen.blit(text, text_rect)
    
    def get_rect(self):
        """获取角色矩形区域"""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def is_clicked(self, pos):
        """检查是否被点击"""
        return self.get_rect().collidepoint(pos)

class DonaldDuck(Character):
    """唐老鸭类"""
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, (255, 255, 0), "唐老鸭")
        self.hat_color = (0, 0, 0)  # 黑色帽子
        self.beak_color = (255, 165, 0)  # 橙色嘴巴
    
    def render(self, screen):
        """渲染唐老鸭"""
        if not self.active:
            return
        
        # 计算实际渲染位置
        render_y = self.y - self.original_bounce
        
        # 绘制身体
        pygame.draw.ellipse(screen, self.color, 
                          (self.x, render_y, self.width, self.height))
        pygame.draw.ellipse(screen, (0, 0, 0), 
                          (self.x, render_y, self.width, self.height), 2)
        
        # 绘制帽子
        hat_rect = (self.x - 5, render_y - 15, self.width + 10, 20)
        pygame.draw.ellipse(screen, self.hat_color, hat_rect)
        pygame.draw.ellipse(screen, (0, 0, 0), hat_rect, 2)
        
        # 绘制眼睛
        eye_size = 10
        eye_y = render_y + self.height // 3
        pygame.draw.circle(screen, (0, 0, 0), 
                         (self.x + self.width // 3, eye_y), eye_size)
        pygame.draw.circle(screen, (0, 0, 0), 
                         (self.x + 2 * self.width // 3, eye_y), eye_size)
        
        # 绘制白色眼珠
        pygame.draw.circle(screen, (255, 255, 255), 
                         (self.x + self.width // 3 + 3, eye_y - 3), 4)
        pygame.draw.circle(screen, (255, 255, 255), 
                         (self.x + 2 * self.width // 3 + 3, eye_y - 3), 4)
        
        # 绘制嘴巴
        mouth_y = render_y + 2 * self.height // 3
        pygame.draw.ellipse(screen, self.beak_color, 
                          (self.x + self.width // 4, mouth_y - 8, 
                           self.width // 2, 16))
        pygame.draw.ellipse(screen, (0, 0, 0), 
                          (self.x + self.width // 4, mouth_y - 8, 
                           self.width // 2, 16), 2)
        
        # 绘制名字
        font = pygame.font.Font(None, 24)
        text = font.render(self.name, True, (0, 0, 0))
        text_rect = text.get_rect(center=(self.x + self.width // 2, render_y - 25))
        screen.blit(text, text_rect)

class Duckling(Character):
    """汤小鸭类"""
    
    def __init__(self, x, y, width, height, name):
        super().__init__(x, y, width, height, (255, 165, 0), name)
        self.size = width  # 记录原始大小
        self.beak_color = (255, 200, 0)  # 黄色嘴巴
        self.body_color_choices = [
            (255, 204, 153),
            (255, 178, 102),
            (255, 221, 153),
            (255, 198, 128),
            (255, 230, 179),
            (255, 215, 170),
            (255, 190, 130),
        ]
        self.hat_color_choices = [
            (0, 0, 0),
            (30, 144, 255),
            (65, 105, 225),
            (25, 25, 112),
            (138, 43, 226),
        ]
        self.bow_color_choices = [
            (255, 0, 0),
            (220, 20, 60),
            (255, 105, 180),
            (199, 21, 133),
            (255, 20, 147),
        ]
        self._init_appearance()
        self.font = self._load_font(20)
    
    def _load_font(self, size: int):
        candidates = ["msyh.ttc", "simhei.ttf", "MicrosoftYaHei", "SimHei", None]
        for name in candidates:
            try:
                if name is None:
                    return pygame.font.Font(None, size)
                if name.endswith(".ttc") or name.endswith(".ttf"):
                    path = pygame.font.match_font(name) or name
                    return pygame.font.Font(path, size)
                return pygame.font.SysFont(name, size)
            except Exception:
                continue
        return pygame.font.Font(None, size)
    
    def _init_appearance(self):
        self.original_body_color = random.choice(self.body_color_choices)
        self.original_has_hat = random.choice([True, False])
        self.original_hat_color = random.choice(self.hat_color_choices)
        self.original_has_bow = random.choice([True, False])
        self.original_bow_color = random.choice(self.bow_color_choices)
        self.original_body_size = self.size
        self.original_eye_size = 6
        self.restore_original_appearance()
    
    def render(self, screen):
        """渲染汤小鸭"""
        if not self.active:
            return
        
        # 计算实际渲染位置
        render_y = self.y - self.original_bounce
        
        # 绘制身体
        body_rect = (self.x, render_y, self.width, self.height)
        pygame.draw.ellipse(screen, self.color, body_rect)
        pygame.draw.ellipse(screen, (0, 0, 0), body_rect, 2)
        
        # 帽子
        if self.has_hat:
            hat_rect = (self.x - 4, render_y - 12, self.width + 8, 15)
            pygame.draw.ellipse(screen, self.hat_color, hat_rect)
            pygame.draw.ellipse(screen, (0, 0, 0), hat_rect, 2)
            # 绘制帽子上的穗（只有有帽子时才绘制）
            tassel_y = render_y - 12
            tassel_x = self.x + self.width // 2
            pygame.draw.circle(screen, (255, 255, 0), (tassel_x, tassel_y), 3)
            pygame.draw.circle(screen, (0, 0, 0), (tassel_x, tassel_y), 3, 1)
        
        # 绘制眼睛
        eye_size = self.eye_size
        eye_y = render_y + self.height // 3
        pygame.draw.circle(screen, (0, 0, 0), 
                         (self.x + self.width // 3, eye_y), eye_size)
        pygame.draw.circle(screen, (0, 0, 0), 
                         (self.x + 2 * self.width // 3, eye_y), eye_size)
        
        # 绘制嘴巴（使用完整的椭圆，参考唐老鸭的绘制方式）
        mouth_y = render_y + 2 * self.height // 3
        # 绘制填充的嘴巴（完整的椭圆）
        beak_rect = (self.x + self.width // 4, mouth_y - 6, self.width // 2, 12)
        pygame.draw.ellipse(screen, self.beak_color, beak_rect)
        # 绘制嘴巴边框（完整的椭圆边框）
        pygame.draw.ellipse(screen, (0, 0, 0), beak_rect, 2)
        
        # 蝴蝶结
        if self.has_bow:
            bow_width = self.width // 2
            bow_rect = (self.x + self.width // 4, render_y + self.height - 8, bow_width, 12)
            pygame.draw.ellipse(screen, self.bow_color, bow_rect)
            pygame.draw.ellipse(screen, (0, 0, 0), bow_rect, 2)
        
        # 绘制名字（根据是否有帽子调整位置）
        text = self.font.render(self.name, True, (0, 0, 0))
        # 如果有帽子，名字位置更靠上，避免被帽子挡住
        name_y = render_y - 20 if self.has_hat else render_y - 15
        text_rect = text.get_rect(center=(self.x + self.width // 2, name_y))
        screen.blit(text, text_rect)
    
    def start_random_movement(self):
        """开始随机移动"""
        # 在原始位置附近随机移动
        offset_x = random.randint(-50, 50)
        offset_y = random.randint(-30, 30)
        self.move_to(self.original_x + offset_x, self.original_y + offset_y)
        self.start_bounce()
    
    def stop_random_movement(self):
        """停止随机移动"""
        self.reset_position()

    # 换装主题
    def switch_to_excited_theme(self):
        self.has_hat = False
        self.has_bow = True
        self.bow_color = (255, 0, 0)
        self.color = (255, 200, 120)
        self.eye_size = 7

    def switch_to_focused_theme(self):
        self.has_hat = True
        self.hat_color = (25, 25, 112)
        self.has_bow = False
        self.color = (255, 170, 90)
        self.eye_size = 6

    def restore_original_appearance(self):
        self.color = self.original_body_color
        self.has_hat = self.original_has_hat
        self.hat_color = self.original_hat_color
        self.has_bow = self.original_has_bow
        self.bow_color = self.original_bow_color
        self.eye_size = self.original_eye_size
