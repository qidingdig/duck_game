#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
点名记录查看和导出窗口
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Any, Callable, Dict, List, Optional

from services.roll_call_service import RollCallService
from ui.message_dialog import MessageDialogHelper


class RollCallRecordsWindow:
    """点名记录查看和导出窗口"""

    def __init__(
        self,
        tk_root: tk.Misc,
        service: RollCallService,
        message_dialog: MessageDialogHelper,
    ):
        self._root = tk_root
        self._service = service
        self._message_dialog = message_dialog

        self._window: Optional[tk.Toplevel] = None
        self._sessions_tree: Optional[ttk.Treeview] = None
        self._records_tree: Optional[ttk.Treeview] = None
        self._selected_session: Optional[str] = None
        self._session_checkboxes: Dict[str, tk.BooleanVar] = {}  # 会话代码 -> 复选框变量
        self._select_all_button: Optional[tk.Button] = None
        self._all_selected: bool = False  # 全选状态

    def show(self) -> None:
        """显示窗口"""
        if self._window and tk.Toplevel.winfo_exists(self._window):
            self._window.lift()
            return

        self._window = tk.Toplevel(self._root)
        self._window.title("点名记录查看与导出")
        self._window.geometry("1000x700")
        self._window.minsize(800, 600)

        self._build_ui()
        self._refresh_sessions()

    def _build_ui(self) -> None:
        """构建UI"""
        # 主容器
        main_frame = tk.Frame(self._window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 上半部分：会话列表
        sessions_frame = tk.LabelFrame(main_frame, text="点名会话列表", padx=10, pady=10)
        sessions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 会话列表工具栏
        sessions_toolbar = tk.Frame(sessions_frame)
        sessions_toolbar.pack(fill=tk.X, pady=(0, 5))

        tk.Button(sessions_toolbar, text="刷新", command=self._refresh_sessions).pack(side=tk.LEFT, padx=5)
        tk.Button(sessions_toolbar, text="导出所有(CSV)", command=lambda: self._export_all("csv")).pack(side=tk.LEFT, padx=5)
        tk.Button(sessions_toolbar, text="导出所有(XLSX)", command=lambda: self._export_all("xlsx")).pack(side=tk.LEFT, padx=5)
        
        # 全选/取消全选按钮（切换）
        self._select_all_button = tk.Button(
            sessions_toolbar, 
            text="全选", 
            command=self._toggle_select_all, 
            bg="#4CAF50", 
            fg="white"
        )
        self._select_all_button.pack(side=tk.LEFT, padx=5)
        
        # 删除选中会话按钮
        tk.Button(
            sessions_toolbar, 
            text="删除选中会话", 
            command=self._delete_selected_sessions, 
            bg="#F44336", 
            fg="white"
        ).pack(side=tk.LEFT, padx=5)

        # 会话列表
        sessions_tree_frame = tk.Frame(sessions_frame)
        sessions_tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar_sessions = ttk.Scrollbar(sessions_tree_frame, orient=tk.VERTICAL)
        scrollbar_sessions.pack(side=tk.RIGHT, fill=tk.Y)

        self._sessions_tree = ttk.Treeview(
            sessions_tree_frame,
            columns=("select", "session_code", "started_at", "mode", "strategy", "count", "records"),
            show="headings",
            yscrollcommand=scrollbar_sessions.set,
        )
        scrollbar_sessions.config(command=self._sessions_tree.yview)

        # 设置列
        self._sessions_tree.heading("select", text="选择")
        self._sessions_tree.heading("session_code", text="会话代码")
        self._sessions_tree.heading("started_at", text="开始时间")
        self._sessions_tree.heading("mode", text="点名方式")
        self._sessions_tree.heading("strategy", text="选择策略")
        self._sessions_tree.heading("count", text="选择人数")
        self._sessions_tree.heading("records", text="记录数")

        self._sessions_tree.column("select", width=60, anchor="center")
        self._sessions_tree.column("session_code", width=150, anchor="center")
        self._sessions_tree.column("started_at", width=180, anchor="center")
        self._sessions_tree.column("mode", width=80, anchor="center")
        self._sessions_tree.column("strategy", width=120, anchor="center")
        self._sessions_tree.column("count", width=80, anchor="center")
        self._sessions_tree.column("records", width=80, anchor="center")

        self._sessions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # 绑定选择事件（用于显示详情）
        self._sessions_tree.bind("<<TreeviewSelect>>", self._on_session_selected)
        # 绑定双击事件（用于切换选择状态）
        self._sessions_tree.bind("<Double-Button-1>", self._on_sessions_tree_double_click)
        # 绑定单击事件（用于切换选择列的选择状态）
        self._sessions_tree.bind("<Button-1>", self._on_sessions_tree_click)

        # 下半部分：记录详情
        records_frame = tk.LabelFrame(main_frame, text="点名记录详情", padx=10, pady=10)
        records_frame.pack(fill=tk.BOTH, expand=True)

        # 记录工具栏
        records_toolbar = tk.Frame(records_frame)
        records_toolbar.pack(fill=tk.X, pady=(0, 5))

        tk.Label(records_toolbar, text="当前会话:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self._current_session_label = tk.Label(records_toolbar, text="未选择", font=("Arial", 10, "bold"), fg="gray")
        self._current_session_label.pack(side=tk.LEFT, padx=5)

        tk.Button(records_toolbar, text="导出当前会话(CSV)", command=lambda: self._export_current("csv")).pack(side=tk.LEFT, padx=5)
        tk.Button(records_toolbar, text="导出当前会话(XLSX)", command=lambda: self._export_current("xlsx")).pack(side=tk.LEFT, padx=5)

        # 记录列表
        records_tree_frame = tk.Frame(records_frame)
        records_tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar_records = ttk.Scrollbar(records_tree_frame, orient=tk.VERTICAL)
        scrollbar_records.pack(side=tk.RIGHT, fill=tk.Y)

        self._records_tree = ttk.Treeview(
            records_tree_frame,
            columns=("order", "student_id", "name", "status", "called_time", "note"),
            show="headings",
            yscrollcommand=scrollbar_records.set,
        )
        scrollbar_records.config(command=self._records_tree.yview)

        # 设置列
        self._records_tree.heading("order", text="顺序")
        self._records_tree.heading("student_id", text="学号")
        self._records_tree.heading("name", text="姓名")
        self._records_tree.heading("status", text="状态")
        self._records_tree.heading("called_time", text="点名时间")
        self._records_tree.heading("note", text="备注")

        self._records_tree.column("order", width=60, anchor="center")
        self._records_tree.column("student_id", width=100, anchor="center")
        self._records_tree.column("name", width=120, anchor="center")
        self._records_tree.column("status", width=80, anchor="center")
        self._records_tree.column("called_time", width=180, anchor="center")
        self._records_tree.column("note", width=200, anchor="center")

        self._records_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 关闭按钮
        close_btn = tk.Button(main_frame, text="关闭", command=self._window.destroy, width=10)
        close_btn.pack(pady=(10, 0))

    def _refresh_sessions(self) -> None:
        """刷新会话列表"""
        if not self._sessions_tree:
            return

        # 保存当前选中状态
        old_selected = set()
        for session_code, var in self._session_checkboxes.items():
            if var.get():
                old_selected.add(session_code)

        # 清空现有数据
        for item in self._sessions_tree.get_children():
            self._sessions_tree.delete(item)
        
        # 清空复选框字典
        self._session_checkboxes.clear()

        try:
            sessions = self._service.list_all_sessions()
            for session in sessions:
                mode_text = "全点" if session["mode"] == "all" else "抽点"
                strategy_text = {
                    "random": "随机",
                    "most_absent": "优先旷课最多",
                    "least_called": "优先点到最少",
                }.get(session["strategy"], session["strategy"])

                session_code = session["session_code"]
                # 初始化复选框状态，如果之前选中过则保持选中
                was_selected = session_code in old_selected
                var = tk.BooleanVar(value=was_selected)
                self._session_checkboxes[session_code] = var
                
                self._sessions_tree.insert(
                    "",
                    tk.END,
                    values=(
                        "☑" if was_selected else "□",  # 根据之前的状态显示
                        session_code,
                        session["started_at"],
                        mode_text,
                        strategy_text,
                        session["selected_count"],
                        session["record_count"],
                    ),
                    tags=(session_code,)
                )
            
            # 更新全选按钮状态
            all_selected = all(var.get() for var in self._session_checkboxes.values()) if self._session_checkboxes else False
            self._all_selected = all_selected
            if self._select_all_button:
                if self._all_selected:
                    self._select_all_button.config(text="取消全选", bg="#FF9800")
                else:
                    self._select_all_button.config(text="全选", bg="#4CAF50")
        except Exception as e:
            self._message_dialog.show_error(f"刷新会话列表失败: {e}")

    def _on_session_selected(self, event) -> None:
        """会话选择事件（单击查看详情）"""
        selection = self._sessions_tree.selection()
        if not selection:
            return

        item = self._sessions_tree.item(selection[0])
        # values[0] 是选择列，values[1] 是会话代码
        if len(item["values"]) < 2:
            return
        
        session_code = item["values"][1]  # 会话代码在第二列
        self._selected_session = session_code
        self._current_session_label.config(text=session_code, fg="blue")
        self._refresh_records(session_code)

    def _refresh_records(self, session_code: str) -> None:
        """刷新记录列表"""
        if not self._records_tree:
            return

        # 清空现有数据
        for item in self._records_tree.get_children():
            self._records_tree.delete(item)

        try:
            from services.roll_call_service import STATUS_MAP
            details = self._service.get_session_details(session_code)

            for detail in details:
                # 插入记录
                self._records_tree.insert(
                    "",
                    tk.END,
                    values=(
                        detail["order_index"],
                        detail["student_id"],
                        detail["name"],
                        STATUS_MAP.get(detail["status"], detail["status"]),
                        detail["called_time"],
                        detail["note"],
                    ),
                )
        except Exception as e:
            print(f"[RollCallRecordsWindow] 刷新记录失败: {e}")
            import traceback
            traceback.print_exc()
            self._message_dialog.show_error(f"刷新记录列表失败: {e}")

    def _export_all(self, format_type: str) -> None:
        """导出所有记录"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=f".{format_type}",
                filetypes=[
                    (f"{format_type.upper()} files", f"*.{format_type}"),
                    ("All files", "*.*"),
                ],
                title="导出所有点名记录",
            )

            if not file_path:
                return

            if format_type == "csv":
                self._service.export_to_csv(None, file_path)
            elif format_type == "xlsx":
                self._service.export_to_excel(None, file_path)
            else:
                self._message_dialog.show_error(f"不支持的格式: {format_type}")
                return

            self._message_dialog.show_info(f"导出成功: {file_path}")
        except Exception as e:
            self._message_dialog.show_error(f"导出失败: {e}")

    def _export_current(self, format_type: str) -> None:
        """导出当前会话记录"""
        if not self._selected_session:
            self._message_dialog.show_warning("请先选择一个会话")
            return

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=f".{format_type}",
                filetypes=[
                    (f"{format_type.upper()} files", f"*.{format_type}"),
                    ("All files", "*.*"),
                ],
                title=f"导出会话 {self._selected_session} 的记录",
                initialfile=f"roll_call_{self._selected_session}.{format_type}",
            )

            if not file_path:
                return

            if format_type == "csv":
                self._service.export_to_csv(self._selected_session, file_path)
            elif format_type == "xlsx":
                self._service.export_to_excel(self._selected_session, file_path)
            else:
                self._message_dialog.show_error(f"不支持的格式: {format_type}")
                return

            self._message_dialog.show_info(f"导出成功: {file_path}")
        except Exception as e:
            self._message_dialog.show_error(f"导出失败: {e}")
    
    def _on_sessions_tree_click(self, event) -> None:
        """会话列表点击事件"""
        region = self._sessions_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self._sessions_tree.identify_column(event.x, event.y)
            if column == "#1":  # 选择列
                item = self._sessions_tree.identify_row(event.y)
                if item:
                    self._toggle_session_selection(item)
                    # 阻止事件继续传播，避免触发选择事件
                    return "break"
        # 如果不是点击选择列，允许 Treeview 正常处理选择
        # 不返回 "break"，让 <<TreeviewSelect>> 事件正常触发
    
    def _on_sessions_tree_double_click(self, event) -> None:
        """会话列表双击事件"""
        region = self._sessions_tree.identify_region(event.x, event.y)
        if region == "cell" or region == "row":
            item = self._sessions_tree.identify_row(event.y)
            if item:
                # 双击整行也可以切换选择状态
                self._toggle_session_selection(item)
    
    def _toggle_session_selection(self, item) -> None:
        """切换会话选择状态"""
        tags = self._sessions_tree.item(item, "tags")
        if tags:
            session_code = tags[0]
            if session_code in self._session_checkboxes:
                var = self._session_checkboxes[session_code]
                var.set(not var.get())
                # 更新显示
                values = list(self._sessions_tree.item(item, "values"))
                values[0] = "☑" if var.get() else "□"
                self._sessions_tree.item(item, values=values)
                
                # 更新全选按钮状态
                all_selected = all(v.get() for v in self._session_checkboxes.values()) if self._session_checkboxes else False
                if all_selected != self._all_selected:
                    self._all_selected = all_selected
                    if self._select_all_button:
                        if self._all_selected:
                            self._select_all_button.config(text="取消全选", bg="#FF9800")
                        else:
                            self._select_all_button.config(text="全选", bg="#4CAF50")
    
    def _toggle_select_all(self) -> None:
        """切换全选/取消全选状态"""
        self._all_selected = not self._all_selected
        
        # 更新所有会话的选择状态
        for session_code, var in self._session_checkboxes.items():
            var.set(self._all_selected)
            # 更新显示
            for item in self._sessions_tree.get_children():
                tags = self._sessions_tree.item(item, "tags")
                if tags and tags[0] == session_code:
                    values = list(self._sessions_tree.item(item, "values"))
                    values[0] = "☑" if self._all_selected else "□"
                    self._sessions_tree.item(item, values=values)
                    break
        
        # 更新按钮文本和颜色
        if self._select_all_button:
            if self._all_selected:
                self._select_all_button.config(text="取消全选", bg="#FF9800")
            else:
                self._select_all_button.config(text="全选", bg="#4CAF50")
    
    def _delete_selected_sessions(self) -> None:
        """删除选中的会话"""
        # 重新统计选中的会话（确保数据是最新的）
        selected_sessions = []
        for item in self._sessions_tree.get_children():
            tags = self._sessions_tree.item(item, "tags")
            if tags:
                session_code = tags[0]
                if session_code in self._session_checkboxes:
                    var = self._session_checkboxes[session_code]
                    if var.get():
                        selected_sessions.append(session_code)
        
        if not selected_sessions:
            self._message_dialog.show_warning("请先选择要删除的会话")
            return
        
        # 确认删除
        count = len(selected_sessions)
        session_list = "\n".join([f"  - {code}" for code in selected_sessions[:10]])  # 最多显示10个
        if len(selected_sessions) > 10:
            session_list += f"\n  ... 还有 {len(selected_sessions) - 10} 个会话"
        
        if not messagebox.askyesno(
            "确认删除",
            f"确定要删除选中的 {count} 个点名会话吗？\n\n会话列表：\n{session_list}\n\n这将删除这些会话的所有记录，此操作不可恢复！",
            parent=self._window
        ):
            return
        
        try:
            deleted_count = self._service.delete_sessions(selected_sessions)
            if deleted_count > 0:
                self._message_dialog.show_info(f"成功删除 {deleted_count} 个会话")
                # 刷新会话列表
                self._refresh_sessions()
                # 清空记录列表
                for item in self._records_tree.get_children():
                    self._records_tree.delete(item)
                self._selected_session = None
                self._current_session_label.config(text="未选择", fg="gray")
            else:
                self._message_dialog.show_warning("删除失败，请重试")
        except Exception as e:
            self._message_dialog.show_error(f"删除失败: {e}")

