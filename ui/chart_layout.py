#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图表布局策略抽象和实现。
遵循开闭原则：可以扩展新的布局策略而不修改现有代码。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Any
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


class LayoutStrategy(ABC):
    """布局策略抽象基类"""
    
    @abstractmethod
    def create_layout(
        self,
        fig: Any,
        chart_types: List[str],
        show_table: bool = False,
    ) -> Dict[str, Any]:
        """
        创建图表布局
        
        Args:
            fig: matplotlib figure对象
            chart_types: 图表类型列表，如 ['bar', 'pie', 'function_python', 'function_c']
            show_table: 是否显示明细表
        
        Returns:
            包含坐标轴对象的字典，键为图表类型标识
        """
        pass
    
    @abstractmethod
    def get_figure_size(self, show_table: bool = False) -> Tuple[float, float]:
        """获取图表尺寸"""
        pass
    
    @abstractmethod
    def adjust_layout(self, fig: Any, show_table: bool = False) -> None:
        """调整布局参数"""
        pass


class DefaultLayoutStrategy(LayoutStrategy):
    """默认布局策略 - 2x2网格布局"""
    
    def __init__(
        self,
        figure_size_with_table: Tuple[float, float] = (12, 10),
        figure_size_without_table: Tuple[float, float] = (12, 8.5),
    ):
        self.figure_size_with_table = figure_size_with_table
        self.figure_size_without_table = figure_size_without_table
    
    def create_layout(
        self,
        fig: Any,
        chart_types: List[str],
        show_table: bool = False,
    ) -> Dict[str, Any]:
        """创建默认2x2网格布局"""
        axes = {}
        
        if show_table:
            # 3行2列布局，最后一行用于表格
            gs = GridSpec(3, 2, figure=fig, height_ratios=[1, 1, 0.9])
            axes['bar'] = fig.add_subplot(gs[0, 0])
            axes['pie'] = fig.add_subplot(gs[0, 1])
            axes['function_python'] = fig.add_subplot(gs[1, 0])
            axes['function_c'] = fig.add_subplot(gs[1, 1])
            axes['table'] = fig.add_subplot(gs[2, :])
        else:
            # 2行2列布局
            gs = GridSpec(2, 2, figure=fig)
            axes['bar'] = fig.add_subplot(gs[0, 0])
            axes['pie'] = fig.add_subplot(gs[0, 1])
            axes['function_python'] = fig.add_subplot(gs[1, 0])
            axes['function_c'] = fig.add_subplot(gs[1, 1])
        
        return axes
    
    def get_figure_size(self, show_table: bool = False) -> Tuple[float, float]:
        if show_table:
            return self.figure_size_with_table
        return self.figure_size_without_table
    
    def adjust_layout(self, fig: Any, show_table: bool = False) -> None:
        """调整布局间距"""
        try:
            if show_table:
                fig.subplots_adjust(
                    top=0.93, bottom=0.08,
                    left=0.06, right=0.92,
                    hspace=0.55, wspace=0.3,
                )
            else:
                fig.subplots_adjust(
                    top=0.93, bottom=0.12,
                    left=0.08, right=0.92,
                    hspace=0.35, wspace=0.3,
                )
        except Exception:
            pass


class CompactLayoutStrategy(LayoutStrategy):
    """紧凑布局策略 - 1行3列布局（示例：展示如何扩展）"""
    
    def __init__(
        self,
        figure_size: Tuple[float, float] = (14, 5),
    ):
        self.figure_size = figure_size
    
    def create_layout(
        self,
        fig: Any,
        chart_types: List[str],
        show_table: bool = False,
    ) -> Dict[str, Any]:
        """创建紧凑的1行布局"""
        axes = {}
        num_charts = len(chart_types)
        if num_charts == 0:
            num_charts = 1
        
        gs = GridSpec(1, num_charts, figure=fig)
        for idx, chart_type in enumerate(chart_types[:num_charts]):
            axes[chart_type] = fig.add_subplot(gs[0, idx])
        
        if show_table:
            # 在下方添加表格
            gs2 = GridSpec(2, num_charts, figure=fig, height_ratios=[3, 1])
            # 重新创建axes
            axes = {}
            for idx, chart_type in enumerate(chart_types[:num_charts]):
                axes[chart_type] = fig.add_subplot(gs2[0, idx])
            axes['table'] = fig.add_subplot(gs2[1, :])
        
        return axes
    
    def get_figure_size(self, show_table: bool = False) -> Tuple[float, float]:
        return self.figure_size
    
    def adjust_layout(self, fig: Any, show_table: bool = False) -> None:
        """调整紧凑布局间距"""
        try:
            if show_table:
                fig.subplots_adjust(
                    top=0.90, bottom=0.15,
                    left=0.05, right=0.95,
                    hspace=0.4, wspace=0.3,
                )
            else:
                fig.subplots_adjust(
                    top=0.90, bottom=0.10,
                    left=0.05, right=0.95,
                    wspace=0.3,
                )
        except Exception:
            pass

