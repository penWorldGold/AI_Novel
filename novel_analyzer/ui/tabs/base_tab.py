# ui/tabs/base_tab.py
import tkinter as tk
from tkinter import ttk
import os
import shutil


class BaseTab(ttk.Frame):
    def __init__(self, parent, config_manager, app):
        super().__init__(parent)
        self.config = config_manager
        self.app = app
        self.tab_name = "未命名标签"
        self.buttons = []  # 用于存储所有需要锁定的按钮

        # 设置标签页内边距
        self.grid(padx=15, pady=15)

    def log(self, message, level="info"):
        self.app.log(message, level)

    def update_progress(self, value):
        self.app.update_progress(value)

    def update_status(self, message):
        self.app.update_status(message)

    def reset_progress(self):
        self.app.progress_log.reset()

    def set_ui_state(self, state):
        """设置UI状态（正常/禁用）"""
        for widget in self.buttons:
            widget.configure(state=state)

    def register_button(self, button):
        """注册需要状态控制的按钮"""
        self.buttons.append(button)

    def clear_stage_files(self, stage_dir, file_patterns):
        """清除指定阶段的文件"""
        output_dir = self.config.get('global', 'output_dir', 'output')
        target_dir = os.path.join(output_dir, stage_dir)

        if not os.path.exists(target_dir):
            self.log(f"未找到目录: {target_dir}", level="warning")
            return False

        deleted_count = 0
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                for pattern in file_patterns:
                    if file.endswith(pattern):
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                        deleted_count += 1
                        self.log(f"已删除: {file_path}")

        if deleted_count == 0:
            self.log(f"未找到匹配的文件: {stage_dir}/{','.join(file_patterns)}", level="warning")
        else:
            self.log(f"已清除 {deleted_count} 个文件")

        return deleted_count > 0