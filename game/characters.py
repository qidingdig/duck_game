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
    
    # 可选的身体颜色
    BODY_COLORS = [
        (255, 255, 0),    # 黄色（经典）
        (255, 220, 100),  # 浅黄色
        (255, 240, 150),  # 淡黄色
        (255, 200, 0),    # 金黄色
    ]
    
    # 可选的帽子颜色
    HAT_COLORS = [
        (0, 0, 0),        # 黑色（经典）
        (139, 69, 19),    # 棕色
        (50, 50, 50),     # 深灰色
        (25, 25, 112),    # 深蓝色
        (139, 0, 0),      # 深红色
    ]
    
    # 可选的嘴巴颜色
    BEAK_COLORS = [
        (255, 165, 0),    # 橙色（经典）
        (255, 140, 0),    # 深橙色
        (255, 200, 0),    # 金色
        (255, 215, 0),    # 金黄色
    ]
    
    def __init__(self, x, y, width, height):
        # 随机选择外观
        self.body_color = random.choice(self.BODY_COLORS)
        self.hat_color = random.choice(self.HAT_COLORS)
        self.beak_color = random.choice(self.BEAK_COLORS)
        self.has_scarf = random.choice([True, False])  # 随机是否有围巾
        self.scarf_color = random.choice([
            (255, 0, 0),      # 红色
            (0, 0, 255),      # 蓝色
            (0, 255, 0),      # 绿色
            (255, 192, 203),  # 粉色
            (255, 255, 0),    # 黄色
        ]) if self.has_scarf else None
        
        # 保存初始外观（用于恢复）
        self.original_body_color = self.body_color
        self.original_hat_color = self.hat_color
        self.original_beak_color = self.beak_color
        self.original_has_scarf = self.has_scarf
        self.original_scarf_color = self.scarf_color
        self.has_glasses = False  # 眼镜装饰（用于工作主题）
        
        super().__init__(x, y, width, height, self.body_color, "唐老鸭")
    
    def switch_to_red_packet_theme(self):
        """切换到红包主题外观"""
        self.body_color = (255, 200, 0)  # 金黄色身体
        self.color = self.body_color  # 更新基类颜色
        self.hat_color = (255, 215, 0)  # 金色帽子
        self.beak_color = (255, 140, 0)  # 深橙色嘴巴
        self.has_scarf = True
        self.scarf_color = (255, 0, 0)  # 红色围巾
        self.has_glasses = False
    
    def switch_to_work_theme(self):
        """切换到工作主题外观"""
        self.body_color = (255, 255, 0)  # 黄色身体
        self.color = self.body_color  # 更新基类颜色
        self.hat_color = (25, 25, 112)  # 深蓝色帽子
        self.beak_color = (255, 165, 0)  # 橙色嘴巴
        self.has_scarf = False
        self.scarf_color = None
        self.has_glasses = True  # 添加眼镜装饰
    
    def restore_original_appearance(self):
        """恢复初始随机外观"""
        self.body_color = self.original_body_color
        self.color = self.body_color  # 更新基类颜色
        self.hat_color = self.original_hat_color
        self.beak_color = self.original_beak_color
        self.has_scarf = self.original_has_scarf
        self.scarf_color = self.original_scarf_color
        self.has_glasses = False
    
    def render(self, screen):
        """渲染唐老鸭"""
        if not self.active:
            return
        
        # 计算实际渲染位置
        render_y = self.y - self.original_bounce
        
        # 绘制身体
        pygame.draw.ellipse(screen, self.body_color, 
                          (self.x, render_y, self.width, self.height))
        pygame.draw.ellipse(screen, (0, 0, 0), 
                          (self.x, render_y, self.width, self.height), 2)
        
        # 绘制围巾（在身体下方）
        if self.has_scarf:
            scarf_y = render_y + self.height - 10
            pygame.draw.rect(screen, self.scarf_color,
                           (self.x - 5, scarf_y, self.width + 10, 12))
            pygame.draw.rect(screen, (0, 0, 0),
                           (self.x - 5, scarf_y, self.width + 10, 12), 2)
        
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
        
        # 绘制眼镜（工作主题）
        if self.has_glasses:
            glasses_y = render_y + self.height // 3 - 5
            # 绘制眼镜框
            pygame.draw.ellipse(screen, (100, 100, 100),
                              (self.x + self.width // 3 - 8, glasses_y - 3, 16, 12), 2)
            pygame.draw.ellipse(screen, (100, 100, 100),
                              (self.x + 2 * self.width // 3 - 8, glasses_y - 3, 16, 12), 2)
            # 绘制眼镜桥
            pygame.draw.line(screen, (100, 100, 100),
                           (self.x + self.width // 3 + 8, glasses_y + 1),
                           (self.x + 2 * self.width // 3 - 8, glasses_y + 1), 2)
        
        # 绘制名字
        font = pygame.font.Font(None, 24)
        text = font.render(self.name, True, (0, 0, 0))
        text_rect = text.get_rect(center=(self.x + self.width // 2, render_y - 25))
        screen.blit(text, text_rect)

class Duckling(Character):
    """汤小鸭类"""
    
    # 可选的身体颜色
    BODY_COLORS = [
        (255, 165, 0),    # 橙色（经典）
        (255, 200, 0),    # 金黄色
        (255, 140, 0),    # 深橙色
        (255, 220, 100), # 浅橙色
        (255, 192, 128), # 淡橙色
        (255, 255, 0),   # 黄色
        (255, 215, 0),   # 金黄色
    ]
    
    # 可选的帽子颜色（小鸭也可以戴小帽子）
    HAT_COLORS = [
        (139, 69, 19),   # 棕色
        (50, 50, 50),    # 深灰色
        (25, 25, 112),   # 深蓝色
        (139, 0, 0),     # 深红色
        (0, 100, 0),     # 深绿色
    ]
    
    def __init__(self, x, y, width, height, name):
        # 随机选择外观
        self.body_color = random.choice(self.BODY_COLORS)
        self.has_hat = random.choice([True, False])  # 随机是否有帽子
        self.hat_color = random.choice(self.HAT_COLORS) if self.has_hat else None
        self.has_bow = random.choice([True, False])  # 随机是否有蝴蝶结
        self.bow_color = random.choice([
            (255, 0, 0),      # 红色
            (0, 0, 255),      # 蓝色
            (255, 192, 203),  # 粉色
            (255, 255, 0),    # 黄色
            (0, 255, 0),      # 绿色
        ]) if self.has_bow else None
        
        # 保存初始外观（用于恢复）
        self.original_body_color = self.body_color
        self.original_has_hat = self.has_hat
        self.original_hat_color = self.hat_color
        self.original_has_bow = self.has_bow
        self.original_bow_color = self.bow_color
        
        super().__init__(x, y, width, height, self.body_color, name)
        self.size = width  # 记录原始大小
        
        # 行为状态
        self._spin_active = False
        self._spin_center = (self.x, self.y)
        self._spin_radius = 16
        self._spin_angle = 0.0
        self._fly_active = False
        self._fly_origin = (self.x, self.y)
        self._fly_amplitude = 20
        self._fly_phase = 0.0
        self._fly_speed = 0.15
    
    def switch_to_excited_theme(self):
        """切换到兴奋外观（红包主题）"""
        self.has_hat = False
        self.hat_color = None
        self.has_bow = True
        self.bow_color = (255, 0, 0)  # 统一红色蝴蝶结
        # 确保颜色同步更新
        self.color = self.body_color
    
    def switch_to_focused_theme(self):
        """切换到专注外观（工作主题）"""
        self.has_hat = True
        self.hat_color = (25, 25, 112)  # 统一深蓝色帽子
        self.has_bow = False
        self.bow_color = None
        # 确保颜色同步更新
        self.color = self.body_color
    
    def restore_original_appearance(self):
        """恢复初始随机外观"""
        self.body_color = self.original_body_color
        self.color = self.body_color  # 更新基类颜色
        self.has_hat = self.original_has_hat
        self.hat_color = self.original_hat_color
        self.has_bow = self.original_has_bow
        self.bow_color = self.original_bow_color
    
    def start_spin(self, radius: int = 16):
        """启动原地转圈动画"""
        self._spin_active = True
        self._spin_center = (self.x, self.y)
        self._spin_radius = radius
        self._spin_angle = 0.0
    
    def stop_spin(self):
        """停止转圈动画，恢复原位"""
        if self._spin_active:
            self.x, self.y = self._spin_center
        self._spin_active = False
        self._spin_angle = 0.0
    
    def start_fly(self, amplitude: int = 30):
        """启动上下飞行动画"""
        self._fly_active = True
        self._fly_origin = (self.x, self.y)
        self._fly_amplitude = amplitude
        self._fly_phase = 0.0
    
    def stop_fly(self):
        """停止飞行动画，恢复原位"""
        if self._fly_active:
            self.x, self.y = self._fly_origin
        self._fly_active = False
        self._fly_phase = 0.0
    
    def update_behavior_state(self, allow_position_override: bool = True):
        """更新动态行为（转圈、飞行）"""
        if self.animating:
            self.update_bounce()
        
        if self._spin_active and allow_position_override:
            self._spin_angle += 0.25
            base_x, base_y = self._spin_center
            self.x = base_x + math.cos(self._spin_angle) * self._spin_radius
            self.y = base_y + math.sin(self._spin_angle) * self._spin_radius
        
        if self._fly_active and allow_position_override:
            self._fly_phase += self._fly_speed
            base_x, base_y = self._fly_origin
            self.y = base_y - abs(math.sin(self._fly_phase)) * self._fly_amplitude
    
    def render(self, screen):
        """渲染唐小鸭"""
        if not self.active:
            return
        
        # 计算实际渲染位置
        render_y = self.y - self.original_bounce
        
        # 绘制身体
        pygame.draw.ellipse(screen, self.body_color, 
                          (self.x, render_y, self.width, self.height))
        pygame.draw.ellipse(screen, (0, 0, 0), 
                          (self.x, render_y, self.width, self.height), 2)
        
        # 绘制蝴蝶结（在身体下方）
        if self.has_bow:
            bow_y = render_y + self.height - 8
            # 绘制蝴蝶结主体
            pygame.draw.ellipse(screen, self.bow_color,
                              (self.x + self.width // 2 - 8, bow_y, 16, 10))
            pygame.draw.ellipse(screen, (0, 0, 0),
                              (self.x + self.width // 2 - 8, bow_y, 16, 10), 1)
            # 绘制蝴蝶结中心
            pygame.draw.circle(screen, (0, 0, 0),
                             (self.x + self.width // 2, bow_y + 5), 3)
        
        # 绘制小帽子（如果有）
        if self.hat_color:
            hat_rect = (self.x - 3, render_y - 10, self.width + 6, 12)
            pygame.draw.ellipse(screen, self.hat_color, hat_rect)
            pygame.draw.ellipse(screen, (0, 0, 0), hat_rect, 1)
        
        # 绘制眼睛
        eye_size = 6
        eye_y = render_y + self.height // 3
        pygame.draw.circle(screen, (0, 0, 0), 
                         (self.x + self.width // 3, eye_y), eye_size)
        pygame.draw.circle(screen, (0, 0, 0), 
                         (self.x + 2 * self.width // 3, eye_y), eye_size)
        
        # 绘制嘴巴（使用橙色椭圆，和唐老鸭一样）
        mouth_y = render_y + 2 * self.height // 3
        pygame.draw.ellipse(screen, (255, 165, 0),  # 橙色嘴巴
                          (self.x + self.width // 4, mouth_y - 8, 
                           self.width // 2, 16))
        pygame.draw.ellipse(screen, (0, 0, 0), 
                          (self.x + self.width // 4, mouth_y - 8, 
                           self.width // 2, 16), 2)
        
        # 绘制名字（使用支持中文的字体）
        font = self._get_chinese_font(20)
        text = font.render(self.name, True, (0, 0, 0))
        name_y_offset = -15 if not self.hat_color else -22
        text_rect = text.get_rect(center=(self.x + self.width // 2, render_y + name_y_offset))
        screen.blit(text, text_rect)
    
    @staticmethod
    def _get_chinese_font(size):
        """获取支持中文的字体"""
        import os
        import platform
        
        # Windows系统字体路径
        if platform.system() == "Windows":
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
                "C:/Windows/Fonts/simsun.ttc",    # 宋体
                "C:/Windows/Fonts/simhei.ttf",    # 黑体
                "C:/Windows/Fonts/simkai.ttf",    # 楷体
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        return pygame.font.Font(font_path, size)
                    except:
                        continue
        
        # 尝试使用pygame的SysFont查找中文字体
        chinese_fonts = [
            "microsoftyaheimicrosoftyaheiuimsyh",  # 微软雅黑
            "simsun",                              # 宋体
            "simhei",                              # 黑体
            "simkai",                              # 楷体
            "microsoftjhengheimicrosoftjhengheiui", # 微软正黑体
        ]
        for font_name in chinese_fonts:
            try:
                font = pygame.font.SysFont(font_name, size)
                # 测试是否能显示中文
                if font.size("中")[0] > 0:
                    return font
            except:
                continue
        
        # 如果都失败，尝试使用默认字体
        try:
            return pygame.font.Font(None, size)
        except:
            # 最后的备选方案
            return pygame.font.SysFont("arial", size)
    
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
