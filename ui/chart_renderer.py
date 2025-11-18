#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
负责代码统计图表的绘制与展示。
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from tkinter import messagebox


class ChartRenderer:
    """封装 Matplotlib 图表绘制逻辑"""

    def __init__(self):
        self._fonts_configured = False

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

    def show_code_statistics_charts(
        self,
        code_result: Dict[str, Any],
        function_stats: Optional[Any] = None,
        c_function_stats: Optional[Any] = None,
        detail_table: Optional[Dict[str, Any]] = None,
    ):
        """显示代码统计图表 - 使用 Matplotlib 自带窗口（可自由缩放）"""
        try:
            self._ensure_matplotlib_backend()
            self._create_integrated_chart(code_result, function_stats, c_function_stats, detail_table)
        except ImportError:
            messagebox.showwarning("警告", "需要安装matplotlib才能显示图表:\npip install matplotlib")
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
        import matplotlib.pyplot as plt

        show_table = bool(detail_table and detail_table.get("rows"))
        using_external_fig = figure is not None
        if using_external_fig:
            fig = figure
        else:
            base_size = (12, 10) if show_table else (12, 8.5)
            fig = plt.figure(figsize=base_size)
            fig.canvas.manager.set_window_title("代码统计图表")
        if show_table:
            gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.9])
            ax1 = fig.add_subplot(gs[0, 0])
            ax2 = fig.add_subplot(gs[0, 1])
            ax3 = fig.add_subplot(gs[1, 0])
            ax4 = fig.add_subplot(gs[1, 1])
            ax_table = fig.add_subplot(gs[2, :])
        else:
            gs = fig.add_gridspec(2, 2)
            ax1 = fig.add_subplot(gs[0, 0])
            ax2 = fig.add_subplot(gs[0, 1])
            ax3 = fig.add_subplot(gs[1, 0])
            ax4 = fig.add_subplot(gs[1, 1])

        labels = []
        values = []
        try:
            if isinstance(code_result, dict) and "by_language" in code_result:
                by_language = code_result["by_language"]
                for lang, stat in by_language.items():
                    code_lines = None
                    if hasattr(stat, "code"):
                        code_lines = getattr(stat, "code")
                    elif isinstance(stat, dict) and "code" in stat:
                        code_lines = stat["code"]
                    elif isinstance(stat, (int, float)):
                        code_lines = int(stat)
                    if code_lines in (None, 0):
                        continue
                    labels.append(str(lang))
                    values.append(int(code_lines))
            elif hasattr(code_result, "items"):
                for lang, stat in code_result.items():
                    if lang in {"summary", "elapsed_time"}:
                        continue
                    code_lines = None
                    if hasattr(stat, "code"):
                        code_lines = getattr(stat, "code")
                    elif isinstance(stat, dict) and "code" in stat:
                        code_lines = stat["code"]
                    elif isinstance(stat, (int, float)):
                        code_lines = int(stat)
                    if code_lines in (None, 0):
                        continue
                    labels.append(str(lang))
                    values.append(int(code_lines))
        except Exception as exc:  # pragma: no cover - 仅用于调试
            print(f"[ChartRenderer] 解析代码统计数据错误: {exc}")
            return

        if labels:
            sorted_data = sorted(zip(labels, values), key=lambda x: -x[1])
            labels = [lang for lang, _ in sorted_data]
            values = [val for _, val in sorted_data]

        if labels:
            ax1.bar(labels, values, color="#4C9AFF")
            ax1.set_title("各语言代码行数（柱状图）", fontsize=10, fontweight="bold")
            ax1.set_ylabel("行数", fontsize=9)
            ax1.tick_params(axis="x", rotation=45, labelsize=8)
            ax1.tick_params(axis="y", labelsize=8)
        else:
            ax1.text(
                0.5,
                0.5,
                "没有找到代码统计数据",
                ha="center",
                va="center",
                transform=ax1.transAxes,
                fontsize=10,
            )
            ax1.set_title("各语言代码行数（柱状图）", fontsize=10, fontweight="bold")

        if labels:
            wedges, _, _ = ax2.pie(values, labels=None, autopct="%1.1f%%", startangle=140, textprops={"fontsize": 8})
            ax2.legend(wedges, labels, title="语言", loc="center left", bbox_to_anchor=(1.05, 0.5), fontsize=8)
            ax2.set_title("各语言占比（饼图）", fontsize=10, fontweight="bold")
        else:
            ax2.text(
                0.5,
                0.5,
                "没有找到代码统计数据",
                ha="center",
                va="center",
                transform=ax2.transAxes,
                fontsize=10,
            )
            ax2.set_title("各语言占比（饼图）", fontsize=10, fontweight="bold")

        self._plot_function_stats(ax3, function_stats, "Python")
        self._plot_function_stats(ax4, c_function_stats, "C/C++")

        if show_table:
            ax_table.axis("off")
            table = ax_table.table(
                cellText=detail_table["rows"],
                colLabels=detail_table["columns"],
                cellLoc="center",
                loc="center",
            )
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1, 1.2)
            ax_table.set_title(detail_table.get("title", "语言明细表"), fontsize=11, fontweight="bold", pad=10)

        def adjust_layout():
            try:
                if show_table:
                    fig.subplots_adjust(top=0.93, bottom=0.08, left=0.06, right=0.92, hspace=0.55, wspace=0.3)
                else:
                    fig.subplots_adjust(top=0.93, bottom=0.12, left=0.08, right=0.92, hspace=0.35, wspace=0.3)
            except Exception:
                pass

        adjust_layout()

        if not using_external_fig:
            import matplotlib.pyplot as plt

            def _refresh_layout(event=None):
                adjust_layout()
                fig.canvas.draw_idle()

            fig.canvas.mpl_connect("resize_event", _refresh_layout)
            plt.show(block=False)
        else:
            return adjust_layout

    def _plot_function_stats(self, ax, function_stats, lang_name="Python"):
        lengths = []
        summary_vals = {
            "均值": 0,
            "中位数": 0,
            "最小值": 0,
            "最大值": 0,
        }

        if function_stats:
            try:
                if hasattr(function_stats, "functions"):
                    funcs = getattr(function_stats, "functions")
                    for item in funcs:
                        if hasattr(item, "line_count"):
                            lengths.append(int(getattr(item, "line_count")))
                        elif hasattr(item, "length"):
                            lengths.append(int(getattr(item, "length")))
                elif isinstance(function_stats, dict) and "functions" in function_stats:
                    for item in function_stats["functions"]:
                        if isinstance(item, dict):
                            if "line_count" in item:
                                lengths.append(int(item["line_count"]))
                            elif "length" in item:
                                lengths.append(int(item["length"]))
                        elif hasattr(item, "line_count"):
                            lengths.append(int(item.line_count))
                        elif hasattr(item, "length"):
                            lengths.append(int(item.length))

                if hasattr(function_stats, "mean_length"):
                    summary_vals["均值"] = getattr(function_stats, "mean_length", 0) or 0
                    summary_vals["中位数"] = getattr(function_stats, "median_length", 0) or 0
                    summary_vals["最小值"] = getattr(function_stats, "min_length", 0) or 0
                    summary_vals["最大值"] = getattr(function_stats, "max_length", 0) or 0
                elif isinstance(function_stats, dict) and "summary" in function_stats:
                    info = function_stats["summary"]
                    summary_vals["均值"] = info.get("mean", 0) or 0
                    summary_vals["中位数"] = info.get("median", 0) or 0
                    summary_vals["最小值"] = info.get("min", 0) or 0
                    summary_vals["最大值"] = info.get("max", 0) or 0
            except Exception:
                pass

        if lengths:
            ax.hist(lengths, bins=min(50, max(5, len(set(lengths)))), color="#00C853", edgecolor="black")
            ax.set_title(f"{lang_name} 函数长度直方图", fontsize=10, fontweight="bold")
            ax.set_xlabel("行数", fontsize=9)
            ax.set_ylabel("函数个数", fontsize=9)
            ax.tick_params(labelsize=8)

            if summary_vals["均值"] > 0:
                ax.axvline(summary_vals["均值"], color="red", linestyle="--", linewidth=1.5, alpha=0.7, label="均值")
            if summary_vals["中位数"] > 0:
                ax.axvline(summary_vals["中位数"], color="green", linestyle="--", linewidth=1.5, alpha=0.7, label="中位数")
        else:
            ax.text(
                0.5,
                0.5,
                f"没有找到{lang_name}函数统计数据",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=10,
            )
            ax.set_title(f"{lang_name} 函数长度统计", fontsize=10, fontweight="bold")

        stats_text = (
            f"均值: {summary_vals['均值']:.1f}\n"
            f"中位数: {summary_vals['中位数']:.1f}\n"
            f"最小值: {summary_vals['最小值']}\n"
            f"最大值: {summary_vals['最大值']}"
        )
        ax.text(
            0.98,
            0.95,
            stats_text,
            transform=ax.transAxes,
            fontsize=8,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

