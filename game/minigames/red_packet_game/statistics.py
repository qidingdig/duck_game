#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
红包游戏统计收集器
"""

from typing import Dict, List
from .red_packet import RedPacket


class RedPacketStatistics:
    """红包游戏统计收集器"""
    
    def __init__(self):
        """初始化统计器"""
        self.reset()
    
    def reset(self):
        """重置统计"""
        self.duckling_stats: Dict[int, Dict[str, float]] = {}  # {小鸭索引: {'count': 数量, 'amount': 金额}}
        self.user_stats = {
            'total_count': 0,
            'total_amount': 0.0,
            'type_counts': [0, 0, 0],  # 小红包、中红包、大红包
            'type_amounts': [0.0, 0.0, 0.0]
        }
    
    def record_packet_caught_by_duckling(self, duckling_idx: int, packet: RedPacket):
        """
        记录小鸭抢到的红包
        
        Args:
            duckling_idx: 小鸭索引
            packet: 红包对象
        """
        if duckling_idx not in self.duckling_stats:
            self.duckling_stats[duckling_idx] = {'count': 0, 'amount': 0.0}
        
        self.duckling_stats[duckling_idx]['count'] += 1
        self.duckling_stats[duckling_idx]['amount'] += packet.get_amount()
    
    def record_packet_hit_wall(self, packet: RedPacket):
        """
        记录碰壁的红包（用户抢到的）
        
        Args:
            packet: 红包对象
        """
        packet_type = packet.get_type()
        
        self.user_stats['total_count'] += 1
        self.user_stats['total_amount'] += packet.get_amount()
        self.user_stats['type_counts'][packet_type] += 1
        self.user_stats['type_amounts'][packet_type] += packet.get_amount()
    
    def get_duckling_stats(self, duckling_idx: int) -> Dict[str, float]:
        """
        获取小鸭统计
        
        Args:
            duckling_idx: 小鸭索引
            
        Returns:
            Dict: {'count': 数量, 'amount': 金额}
        """
        return self.duckling_stats.get(duckling_idx, {'count': 0, 'amount': 0.0})
    
    def get_user_stats(self) -> Dict:
        """获取用户统计"""
        return self.user_stats.copy()
    
    def get_total_stats(self) -> Dict:
        """获取总统计"""
        total_duckling_count = sum(stats['count'] for stats in self.duckling_stats.values())
        total_duckling_amount = sum(stats['amount'] for stats in self.duckling_stats.values())
        
        return {
            'duckling_stats': self.duckling_stats.copy(),
            'user_stats': self.user_stats.copy(),
            'total_duckling_count': total_duckling_count,
            'total_duckling_amount': total_duckling_amount,
            'grand_total_count': total_duckling_count + self.user_stats['total_count'],
            'grand_total_amount': total_duckling_amount + self.user_stats['total_amount']
        }
    
    def format_report(self) -> str:
        """格式化报告"""
        report = "红包游戏统计:\n"
        report += "=" * 50 + "\n"
        
        # 小鸭统计
        if self.duckling_stats:
            report += "小鸭抢到的红包:\n"
            for duckling_idx in sorted(self.duckling_stats.keys()):
                stats = self.duckling_stats[duckling_idx]
                duckling_name = f"唐小鸭{duckling_idx + 1}"
                report += f"  {duckling_name}: {stats['count']}个, 总金额 ¥{stats['amount']:.2f}\n"
            report += "\n"
        
        # 用户统计
        report += "您抢到的红包:\n"
        report += f"  总红包数: {self.user_stats['total_count']}\n"
        report += f"  总金额: ¥{self.user_stats['total_amount']:.2f}\n"
        report += f"  小红包: {self.user_stats['type_counts'][0]}个, ¥{self.user_stats['type_amounts'][0]:.2f}\n"
        report += f"  中红包: {self.user_stats['type_counts'][1]}个, ¥{self.user_stats['type_amounts'][1]:.2f}\n"
        report += f"  大红包: {self.user_stats['type_counts'][2]}个, ¥{self.user_stats['type_amounts'][2]:.2f}\n"
        
        return report

