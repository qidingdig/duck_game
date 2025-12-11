#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图表类型抽象接口和具体实现。
遵循开闭原则：对扩展开放，对修改关闭。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ChartStyle:
    """图表样式配置"""
    # 颜色配置
    bar_color: str = "#4C9AFF"
    pie_colors: Optional[list] = None
    histogram_color: str = "#00C853"
    histogram_edge_color: str = "black"
    mean_line_color: str = "red"
    median_line_color: str = "green"
    
    # 字体配置
    title_fontsize: int = 10
    label_fontsize: int = 9
    tick_fontsize: int = 8
    table_fontsize: int = 8
    
    # 图表配置
    figure_size_with_table: Tuple[float, float] = (12, 10)
    figure_size_without_table: Tuple[float, float] = (12, 8.5)
    
    # 布局配置
    rotation: int = 45
    pie_startangle: int = 140
    pie_autopct: str = "%1.1f%%"
    
    # 统计文本框配置
    stats_box_facecolor: str = "wheat"
    stats_box_alpha: float = 0.8
    
    def __post_init__(self):
        if self.pie_colors is None:
            self.pie_colors = []


class ChartType(ABC):
    """图表类型抽象基类"""
    
    def __init__(self, style: Optional[ChartStyle] = None):
        self.style = style or ChartStyle()
    
    @abstractmethod
    def plot(self, ax, data: Dict[str, Any]) -> None:
        """
        在给定的坐标轴上绘制图表
        
        Args:
            ax: matplotlib坐标轴对象
            data: 图表数据字典
        """
        pass
    
    @abstractmethod
    def get_title(self) -> str:
        """返回图表标题"""
        pass
    
    def has_data(self, data: Dict[str, Any]) -> bool:
        """检查是否有有效数据"""
        return True


class BarChart(ChartType):
    """柱状图 - 显示各语言代码行数"""
    
    def plot(self, ax, data: Dict[str, Any]) -> None:
        labels = data.get("labels", [])
        values = data.get("values", [])
        
        if not labels or not values:
            ax.text(
                0.5, 0.5,
                "没有找到代码统计数据",
                ha="center", va="center",
                transform=ax.transAxes,
                fontsize=self.style.label_fontsize,
            )
        else:
            ax.bar(labels, values, color=self.style.bar_color)
            ax.set_ylabel("行数", fontsize=self.style.label_fontsize)
            ax.tick_params(axis="x", rotation=self.style.rotation, labelsize=self.style.tick_fontsize)
            ax.tick_params(axis="y", labelsize=self.style.tick_fontsize)
        
        ax.set_title(self.get_title(), fontsize=self.style.title_fontsize, fontweight="bold")
    
    def get_title(self) -> str:
        return "各语言代码行数（柱状图）"


class PieChart(ChartType):
    """饼图 - 显示各语言占比"""
    
    def plot(self, ax, data: Dict[str, Any]) -> None:
        labels = data.get("labels", [])
        values = data.get("values", [])
        
        if not labels or not values:
            ax.text(
                0.5, 0.5,
                "没有找到代码统计数据",
                ha="center", va="center",
                transform=ax.transAxes,
                fontsize=self.style.label_fontsize,
            )
        else:
            wedges, _, _ = ax.pie(
                values,
                labels=None,
                autopct=self.style.pie_autopct,
                startangle=self.style.pie_startangle,
                textprops={"fontsize": self.style.tick_fontsize},
                colors=self.style.pie_colors if self.style.pie_colors else None,
            )
            ax.legend(
                wedges, labels,
                title="语言",
                loc="center left",
                bbox_to_anchor=(1.05, 0.5),
                fontsize=self.style.tick_fontsize,
            )
        
        ax.set_title(self.get_title(), fontsize=self.style.title_fontsize, fontweight="bold")
    
    def get_title(self) -> str:
        return "各语言占比（饼图）"


class FunctionStatsChart(ChartType):
    """函数统计直方图 - 显示函数长度分布"""
    
    def __init__(self, lang_name: str = "Python", style: Optional[ChartStyle] = None):
        super().__init__(style)
        self.lang_name = lang_name
    
    def plot(self, ax, data: Dict[str, Any]) -> None:
        lengths = data.get("lengths", [])
        summary_vals = data.get("summary", {
            "均值": 0,
            "中位数": 0,
            "最小值": 0,
            "最大值": 0,
        })
        
        if not lengths:
            ax.text(
                0.5, 0.5,
                f"没有找到{self.lang_name}函数统计数据",
                ha="center", va="center",
                transform=ax.transAxes,
                fontsize=self.style.label_fontsize,
            )
        else:
            ax.hist(
                lengths,
                bins=min(50, max(5, len(set(lengths)))),
                color=self.style.histogram_color,
                edgecolor=self.style.histogram_edge_color,
            )
            ax.set_xlabel("行数", fontsize=self.style.label_fontsize)
            ax.set_ylabel("函数个数", fontsize=self.style.label_fontsize)
            ax.tick_params(labelsize=self.style.tick_fontsize)
            
            # 绘制均值和中位数线
            if summary_vals.get("均值", 0) > 0:
                ax.axvline(
                    summary_vals["均值"],
                    color=self.style.mean_line_color,
                    linestyle="--",
                    linewidth=1.5,
                    alpha=0.7,
                    label="均值",
                )
            if summary_vals.get("中位数", 0) > 0:
                ax.axvline(
                    summary_vals["中位数"],
                    color=self.style.median_line_color,
                    linestyle="--",
                    linewidth=1.5,
                    alpha=0.7,
                    label="中位数",
                )
            
            # 添加统计信息文本框
            stats_text = (
                f"均值: {summary_vals.get('均值', 0):.1f}\n"
                f"中位数: {summary_vals.get('中位数', 0):.1f}\n"
                f"最小值: {summary_vals.get('最小值', 0)}\n"
                f"最大值: {summary_vals.get('最大值', 0)}"
            )
            ax.text(
                0.98, 0.95,
                stats_text,
                transform=ax.transAxes,
                fontsize=self.style.tick_fontsize,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(
                    boxstyle="round",
                    facecolor=self.style.stats_box_facecolor,
                    alpha=self.style.stats_box_alpha,
                ),
            )
        
        ax.set_title(
            f"{self.lang_name} 函数长度{'直方图' if lengths else '统计'}",
            fontsize=self.style.title_fontsize,
            fontweight="bold",
        )
    
    def get_title(self) -> str:
        return f"{self.lang_name} 函数长度统计"


class DetailTableChart(ChartType):
    """明细表图表 - 显示语言明细数据"""
    
    def plot(self, ax, data: Dict[str, Any]) -> None:
        rows = data.get("rows", [])
        columns = data.get("columns", [])
        title = data.get("title", "语言明细表")
        
        if not rows or not columns:
            ax.text(
                0.5, 0.5,
                "没有明细数据",
                ha="center", va="center",
                transform=ax.transAxes,
                fontsize=self.style.label_fontsize,
            )
        else:
            ax.axis("off")
            table = ax.table(
                cellText=rows,
                colLabels=columns,
                cellLoc="center",
                loc="center",
            )
            table.auto_set_font_size(False)
            table.set_fontsize(self.style.table_fontsize)
            table.scale(1, 1.2)
        
        ax.set_title(title, fontsize=self.style.title_fontsize + 1, fontweight="bold", pad=10)
    
    def get_title(self) -> str:
        return "语言明细表"

