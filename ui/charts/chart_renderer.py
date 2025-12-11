#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
负责代码统计图表的绘制与展示。
重构后遵循开闭原则：对扩展开放，对修改关闭。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ui.message_dialog import MessageDialogHelper
from ui.charts.chart_types import (
    ChartStyle,
    ChartType,
    BarChart,
    PieChart,
    FunctionStatsChart,
    DetailTableChart,
)
from ui.charts.chart_layout import LayoutStrategy, DefaultLayoutStrategy
from ui.charts.chart_data_extractor import ChartDataExtractor


class ChartRenderer:
    """
    封装 Matplotlib 图表绘制逻辑
    
    重构后的设计特点：
    1. 使用图表类型抽象（ChartType），易于扩展新图表类型
    2. 使用布局策略（LayoutStrategy），易于扩展新布局
    3. 使用样式配置（ChartStyle），易于自定义样式
    4. 符合开闭原则：添加新图表类型或布局无需修改现有代码
    """

    def __init__(
        self,
        message_dialog: Optional[MessageDialogHelper] = None,
        style: Optional[ChartStyle] = None,
        layout_strategy: Optional[LayoutStrategy] = None,
    ):
        self._fonts_configured = False
        self._message_dialog = message_dialog or MessageDialogHelper()
        self.style = style or ChartStyle()
        self.layout_strategy = layout_strategy or DefaultLayoutStrategy(
            figure_size_with_table=self.style.figure_size_with_table,
            figure_size_without_table=self.style.figure_size_without_table,
        )
        
        # 注册默认图表类型
        self._chart_registry: Dict[str, ChartType] = {
            'bar': BarChart(style=self.style),
            'pie': PieChart(style=self.style),
            'function_python': FunctionStatsChart(lang_name="Python", style=self.style),
            'function_c': FunctionStatsChart(lang_name="C/C++", style=self.style),
        }

    def _ensure_matplotlib_backend(self):
        import matplotlib

        matplotlib.use("TkAgg")
        if not self._fonts_configured:
            try:
                matplotlib.rcParams["font.sans-serif"] = [
                    "SimHei",
                    "Microsoft YaHei",
                    "Arial Unicode MS",
                    "DejaVu Sans",
                ]
                matplotlib.rcParams["axes.unicode_minus"] = False
            except Exception:
                pass
            self._fonts_configured = True

    def register_chart_type(self, chart_id: str, chart_type: ChartType) -> None:
        """
        注册新的图表类型（扩展点）
        
        Args:
            chart_id: 图表标识符
            chart_type: 图表类型实例
        """
        self._chart_registry[chart_id] = chart_type
    
    def show_code_statistics_charts(
        self,
        code_result: Dict[str, Any],
        function_stats: Optional[Any] = None,
        c_function_stats: Optional[Any] = None,
        detail_table: Optional[Dict[str, Any]] = None,
    ):
        """显示代码统计图表 - 使用 Matplotlib 自带窗口"""
        try:
            self._ensure_matplotlib_backend()
            self._create_integrated_chart(code_result, function_stats, c_function_stats, detail_table)
        except ImportError:
            self._message_dialog.show_warning("需要安装matplotlib才能显示图表:\npip install matplotlib", "警告")
        except Exception as exc:  # pragma: no cover - 仅用于调试
            print(f"显示图表错误: {exc}")
            import traceback

            traceback.print_exc()

    # --- 内部实现 ---------------------------------------------------------
    def _create_integrated_chart(
        self,
        code_result: Dict[str, Any],
        function_stats: Optional[Any] = None,
        c_function_stats: Optional[Any] = None,
        detail_table: Optional[Dict[str, Any]] = None,
        figure=None,
    ):
        """
        创建综合图表
        
        重构后的实现：
        1. 使用布局策略创建布局
        2. 使用图表类型注册表绘制图表
        3. 使用数据提取器提取数据
        4. 易于扩展：添加新图表类型只需注册，无需修改此方法
        """
        import matplotlib.pyplot as plt

        show_table = bool(detail_table and detail_table.get("rows"))
        using_external_fig = figure is not None
        
        # 创建或使用外部figure
        if using_external_fig:
            fig = figure
        else:
            fig_size = self.layout_strategy.get_figure_size(show_table)
            fig = plt.figure(figsize=fig_size)
            fig.canvas.manager.set_window_title("代码统计图表")
        
        # 确定要绘制的图表类型列表
        chart_types_list = ['bar', 'pie', 'function_python', 'function_c']
        if show_table:
            chart_types_list.append('table')
        
        # 使用布局策略创建布局
        axes = self.layout_strategy.create_layout(fig, chart_types_list, show_table)
        
        # 提取数据
        language_data = ChartDataExtractor.extract_language_data(code_result)
        python_function_data = ChartDataExtractor.extract_function_stats(function_stats)
        c_function_data = ChartDataExtractor.extract_function_stats(c_function_stats)
        
        # 绘制各个图表（使用注册的图表类型）
        if 'bar' in axes:
            self._chart_registry['bar'].plot(axes['bar'], language_data)
        
        if 'pie' in axes:
            self._chart_registry['pie'].plot(axes['pie'], language_data)
        
        if 'function_python' in axes:
            self._chart_registry['function_python'].plot(axes['function_python'], python_function_data)
        
        if 'function_c' in axes:
            self._chart_registry['function_c'].plot(axes['function_c'], c_function_data)
        
        # 绘制明细表
        if show_table and 'table' in axes and detail_table:
            table_chart = DetailTableChart(style=self.style)
            table_chart.plot(axes['table'], detail_table)
        
        # 调整布局
        def adjust_layout():
            self.layout_strategy.adjust_layout(fig, show_table)

        adjust_layout()

        # 设置窗口大小调整事件处理
        if not using_external_fig:
            def _refresh_layout(event=None):
                adjust_layout()
                fig.canvas.draw_idle()

            fig.canvas.mpl_connect("resize_event", _refresh_layout)
            plt.show(block=False)
        else:
            return adjust_layout


