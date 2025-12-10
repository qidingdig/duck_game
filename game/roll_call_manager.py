#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RollCallManager: orchestrates roll call workflow between service, UI, and game.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Callable, Deque, Dict, List, Optional

from services.roll_call_service import RollCallService, Student
from ui.roll_call_window import RollCallWindow
from ui.message_dialog import MessageDialogHelper


class RollCallManager:
    """Manage roll call configuration, execution, and persistence."""

    def __init__(
        self,
        service: RollCallService,
        ui_queue,
        message_dialog: MessageDialogHelper,
        trigger_behavior_callback: Optional[Callable[[str], None]] = None,
    ):
        self.service = service
        self._ui_queue = ui_queue
        self._message_dialog = message_dialog
        self.trigger_behavior_callback = trigger_behavior_callback

        self._window: Optional[RollCallWindow] = None
        self._current_roll_call_id: Optional[int] = None
        self._session_code: Optional[str] = None
        self._roster: Deque[Dict] = deque()
        self._current_student: Optional[Dict] = None
        self._current_order: int = 0
        self._last_record_ids: Dict[str, int] = {}

    # ------------------------------------------------------------------ API --
    def request_window(self) -> None:
        """Enqueue request to show the roll call window in UI thread."""
        print(f"[DEBUG] RollCallManager.request_window 被调用")
        print(f"[DEBUG] _ui_queue = {self._ui_queue}")
        try:
            self._ui_queue.put(("show_roll_call_window",), block=False)
            print(f"[DEBUG] 事件已放入队列")
        except Exception as exc:
            print(f"[RollCallManager] 无法请求点名窗口: {exc}")
            import traceback
            traceback.print_exc()

    def show_window(self, tk_root) -> None:
        """Create and display the roll call window (runs on UI thread)."""
        print(f"[DEBUG] show_window 被调用，tk_root={tk_root}")
        if self._window:
            print(f"[DEBUG] 窗口已存在，调用 show()")
            try:
                self._window.show()
                print(f"[DEBUG] 窗口 show() 调用成功")
            except Exception as e:
                print(f"[DEBUG] 窗口 show() 失败: {e}")
                import traceback
                traceback.print_exc()
            return

        print(f"[DEBUG] 创建新窗口")
        try:
            self._window = RollCallWindow(
                tk_root=tk_root,
                message_dialog=self._message_dialog,
                on_start_callback=self._on_start_config,
                on_mark_callback=self._on_mark_status,
                on_close_callback=self._on_window_closed,
                on_view_records_callback=self._on_view_records,
                on_import_students_callback=self._on_import_students,
            )
            print(f"[DEBUG] RollCallWindow 对象创建成功")
            self._window.show()
            print(f"[DEBUG] 窗口 show() 调用成功，窗口应该已显示")
        except Exception as e:
            print(f"[DEBUG] 创建或显示窗口失败: {e}")
            import traceback
            traceback.print_exc()
            self._window = None
    
    def request_records_window(self) -> None:
        """Enqueue request to show the roll call records window in UI thread."""
        try:
            self._ui_queue.put(("show_roll_call_records_window",), block=False)
        except Exception as exc:
            print(f"[RollCallManager] 无法请求记录窗口: {exc}")
    
    def show_records_window(self, tk_root) -> None:
        """Create and display the roll call records window (runs on UI thread)."""
        from ui.roll_call_records_window import RollCallRecordsWindow
        
        records_window = RollCallRecordsWindow(
            tk_root=tk_root,
            service=self.service,
            message_dialog=self._message_dialog,
        )
        records_window.show()

    # ---------------------------------------------------------------- Events --
    def _on_start_config(self, config: Dict) -> None:
        mode = config.get("mode", "all")
        strategy = config.get("strategy", "random")
        count_choice = config.get("count_choice", "10")
        custom_count = int(config.get("custom_count", 10) or 10)

        if mode == "partial":
            if count_choice == "custom":
                selected_count = max(1, custom_count)
            else:
                selected_count = int(count_choice)
        else:
            selected_count = 0  # will be ignored for full call

        try:
            students = self._prepare_roster(mode, strategy, selected_count)
        except ValueError as exc:
            self._message_dialog.show_warning(str(exc))
            # 确保在失败时清空状态
            self._current_roll_call_id = None
            self._current_student = None
            return

        # 检查是否有学生
        if not students:
            self._message_dialog.show_warning("没有可用于点名的学生。")
            self._current_roll_call_id = None
            self._current_student = None
            return

        session_code = time.strftime("%Y-%m-%d-%H%M")
        roll_call_id = self.service.start_roll_call(
            session_code=session_code,
            mode=mode,
            strategy=strategy,
            selected_count=len(students),
        )

        # 设置状态（必须在advance_student之前设置）
        self._session_code = session_code
        self._current_roll_call_id = roll_call_id
        self._roster = deque(students)
        self._current_order = 0
        self._last_record_ids.clear()

        self._message_dialog.show_info(f"点名开始，共 {len(students)} 人。")

        # 换装为点名主题
        if hasattr(self, '_ui_queue') and self._ui_queue:
            try:
                self._ui_queue.put(("change_duckling_theme", "roll_call"), block=False)
            except Exception:
                pass

        # 触发小鸭点名行为（弹跳，不播报语音）
        if hasattr(self, 'trigger_behavior_callback') and callable(self.trigger_behavior_callback):
            self.trigger_behavior_callback("roll_call")
        
        # 使用Tkinter的after方法延迟推进到第一个学生，避免阻塞UI线程
        # 等待行为持续时间结束后再推进到第一个学生
        # 这样特殊行为结束后才开始播报学生姓名
        if self._window and hasattr(self._window, '_root') and self._window._root:
            # 使用Tkinter的after方法，5000毫秒后执行
            self._window._root.after(5000, self._advance_student)
        else:
            # 如果没有窗口，直接推进（不应该发生）
            self._advance_student()
        
        # 最终验证状态
        # 注意：由于使用了after延迟调用_advance_student，所以_current_student在此时还是None是正常的
        print(f"[DEBUG] _on_start_config完成: roll_call_id={self._current_roll_call_id}, student=None (将在5秒后设置), roster剩余={len(self._roster)}")

    def _on_mark_status(self, status: str, student_id: Optional[str]) -> None:
        if status == "late":
            self._handle_late_status(student_id)
            return

        # 调试信息
        print(f"[DEBUG] _on_mark_status调用: status={status}, student_id={student_id}")
        print(f"[DEBUG] 状态检查: roll_call_id={self._current_roll_call_id}, current_student={self._current_student is not None}")
        if self._current_student:
            print(f"[DEBUG] current_student详情: {self._current_student.get('student_id')} - {self._current_student.get('name')}")

        # 检查点名是否已开始（注意：roll_call_id可能为0，所以不能使用if not检查）
        if self._current_roll_call_id is None:
            print(f"[DEBUG] 错误：_current_roll_call_id为None")
            self._message_dialog.show_warning("尚未开始点名。")
            return
        
        # 检查是否有当前学生（点名可能已结束）
        if not self._current_student:
            print(f"[DEBUG] 错误：_current_student为None，但roll_call_id={self._current_roll_call_id}")
            print(f"[DEBUG] roster长度={len(self._roster)}")
            self._message_dialog.show_warning("点名已结束或尚未开始。")
            return

        if student_id and student_id != self._current_student.get("student_id"):
            # safety: current student only
            self._message_dialog.show_warning("当前只能操作正在点名的同学。")
            return

        if status == "leave" and not self._current_student.get("has_leave"):
            self._message_dialog.show_warning("该同学未提交本节课假条，无法记录为请假。")
            return

        # 防止重复点击：检查当前学生是否已经在本次点名中被记录过
        current_student_id = self._current_student.get("student_id")
        if current_student_id in self._last_record_ids:
            # 如果当前学生已经有记录，说明可能被重复点击了
            # 检查是否是在同一个roll_call中
            existing_record = self.service.get_latest_record(self._current_roll_call_id, current_student_id)
            if existing_record and existing_record.get("id"):
                self._message_dialog.show_warning("该学生已经记录过了，正在推进到下一个学生。")
                self._advance_student()
                return

        student = self._current_student
        self._current_order += 1
        record_id = self.service.insert_record(
            roll_call_id=self._current_roll_call_id,
            student_id=student["student_id"],
            order_index=self._current_order,
            status=status,
            note=student.get("note", ""),
        )

        self._last_record_ids[student["student_id"]] = record_id
        self._advance_student()

    def _handle_late_status(self, student_id: Optional[str]) -> None:
        if not student_id:
            self._message_dialog.show_warning("请输入需要补签的学号。")
            return
        if student_id not in self._last_record_ids:
            self._message_dialog.show_warning("找不到该同学的点名记录。")
            return
        
        record_id = self._last_record_ids[student_id]
        
        # 先检查记录是否存在以及原状态是否为旷课
        record = self.service.record_repo.find_by_id(record_id)
        if not record:
            self._message_dialog.show_warning("找不到该同学的点名记录。")
            return
        
        if record.status != "absent":
            self._message_dialog.show_warning(f"只能将旷课记录改为迟到，当前状态为：{self._get_status_text(record.status)}。")
            return
        
        # 检查时间限制（10分钟内）
        import time
        try:
            called_ts = time.mktime(time.strptime(record.called_time, "%Y-%m-%d %H:%M:%S"))
            elapsed_minutes = (time.time() - called_ts) / 60
            if elapsed_minutes > 10:
                self._message_dialog.show_warning(f"超过10分钟无法改为迟到（已过去 {elapsed_minutes:.1f} 分钟）。")
                return
        except Exception as e:
            print(f"[RollCallManager] 时间解析错误: {e}")
            self._message_dialog.show_warning("无法解析记录时间，无法改为迟到。")
            return
        
        # 执行更新
        success = self.service.update_record_status(
            record_id=record_id,
            new_status="late",
            enforce_within_minutes=10,
        )
        if success:
            self._message_dialog.show_info(f"{student_id} 已改为迟到。")
        else:
            self._message_dialog.show_warning("无法改为迟到，请检查记录状态和时间限制。")
    
    def _get_status_text(self, status: str) -> str:
        """获取状态的中文文本"""
        status_map = {
            "present": "出勤",
            "absent": "旷课",
            "leave": "请假",
            "late": "迟到",
        }
        return status_map.get(status, status)

    # ---------------------------------------------------------- Flow helpers --
    def _prepare_roster(self, mode: str, strategy: str, selected_count: int) -> List[Dict]:
        if mode == "all":
            students = self.service.list_students()
        else:
            students = self.service.select_students(strategy=strategy, count=selected_count)

        if not students:
            raise ValueError("没有可用于点名的学生。")

        roster = []
        session_code = time.strftime("%Y-%m-%d-%H%M")
        for stu in students:
            has_leave = self.service.has_leave(stu.student_id, session_code)
            roster.append(
                {
                    "student_id": stu.student_id,
                    "name": stu.name,
                    "nickname": stu.nickname,
                    "photo_path": stu.photo_path,
                    "cut_count": stu.cut_count,
                    "called_count": stu.called_count,
                    "has_leave": has_leave,
                    "note": "已递交假条" if has_leave else "",
                }
            )
        return roster

    def _advance_student(self) -> None:
        """推进到下一个学生"""
        if not self._window:
            print(f"[DEBUG] _advance_student: 窗口不存在")
            return
        
        if not self._roster:
            self._window.show_message("点名结束，可以关闭窗口。")
            self._message_dialog.show_info("点名结束，数据已记录。")
            # 清空当前学生，表示点名结束
            self._current_student = None
            # 确保窗口也清空当前学生
            if self._window:
                self._window._current_student = None
            return
        
        # 从队列中取出下一个学生
        if len(self._roster) == 0:
            print(f"[DEBUG] 错误：roster为空但通过了检查")
            return
        
        self._current_student = self._roster.popleft()
        
        # 确保_current_student已设置
        if not self._current_student:
            print(f"[DEBUG] 错误：从roster取出后_current_student仍为None")
            return
        
        # 同步到窗口（这会设置窗口的_current_student）
        self._window.set_student(self._current_student)
        
        # 验证同步
        if self._window._current_student != self._current_student:
            print(f"[DEBUG] 警告：窗口和manager的_current_student不同步")
        
        # 验证状态（注意：roll_call_id可能为0，所以不能使用if not检查）
        if self._current_roll_call_id is None:
            print(f"[DEBUG] 警告：_current_roll_call_id为None，但_current_student已设置")
        
        # 播报学生名字（在特殊行为结束后）
        self._announce_student_name()
        
        # 最终验证
        print(f"[DEBUG] _advance_student完成: roll_call_id={self._current_roll_call_id}, student={self._current_student.get('name') if self._current_student else None}")

    def _announce_student_name(self) -> None:
        """播报当前学生名字"""
        if not self._current_student:
            return
        
        try:
            from services.duck_behavior_manager import SpeechEngine
            
            # 直接使用学生的姓名进行播报
            name = self._current_student.get("name", "")
            
            if name:
                # 使用单例模式或重用SpeechEngine实例，避免频繁创建导致的问题
                if not hasattr(self, '_speech_engine') or not self._speech_engine.available:
                    self._speech_engine = SpeechEngine()
                
                if self._speech_engine.available:
                    # 添加小延迟，确保之前的播报完成
                    time.sleep(0.1)
                    success = self._speech_engine.speak(name)
                    print(f"[DEBUG] 播报学生姓名: {name}, 成功: {success}")
                    if not success:
                        print(f"[RollCallManager] 语音播报失败：无法添加到队列")
                else:
                    print(f"[RollCallManager] 语音引擎不可用")
        except Exception as e:
            # 语音播报失败不影响功能
            print(f"[RollCallManager] 语音播报异常: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_view_records(self) -> None:
        """查看记录按钮回调"""
        if not self._window:
            self._message_dialog.show_warning("点名窗口未打开")
            return
        try:
            # 获取窗口的根窗口（Tk root）
            # RollCallWindow 的 _root 属性存储了 tk_root
            if hasattr(self._window, '_root') and self._window._root:
                root = self._window._root
            else:
                # 如果 _root 不可用，尝试从窗口获取顶层窗口
                root = self._window.winfo_toplevel() if self._window else None
            
            if root:
                self.show_records_window(root)
            else:
                self._message_dialog.show_warning("无法获取窗口根节点，请通过命令打开记录窗口")
        except Exception as e:
            self._message_dialog.show_error(f"打开记录窗口失败: {e}")
            print(f"[RollCallManager] 打开记录窗口失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_import_students(self, file_path: str, update_existing: bool = True) -> Dict[str, Any]:
        """处理导入学生请求"""
        try:
            return self.service.import_students_from_file(file_path, update_existing=update_existing)
        except Exception as e:
            print(f"[RollCallManager] 导入学生失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'total': 0,
                'imported': 0,
                'updated': 0,
                'skipped': 0,
                'errors': [str(e)],
                'warnings': []
            }
    
    def _on_window_closed(self) -> None:
        # 恢复小鸭原状
        if hasattr(self, '_ui_queue') and self._ui_queue:
            try:
                self._ui_queue.put(("change_duckling_theme", "original"), block=False)
            except Exception:
                pass
        
        self._window = None
        self._current_roll_call_id = None
        self._session_code = None
        self._roster.clear()
        self._current_student = None
        self._last_record_ids.clear()

