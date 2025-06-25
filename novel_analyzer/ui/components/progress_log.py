# ui/components/progress_log.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import time
import logging
import sys


class TkinterLogHandler(logging.Handler):
    def __init__(self, progress_log):
        super().__init__()
        self.progress_log = progress_log
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        log_entry = self.format(record)
        level = record.levelname.lower()
        if level not in ["debug", "info", "warning", "error", "critical"]:
            level = "info"
        self.progress_log.log(log_entry, level)


class ProgressLog(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="进度与日志")
        self.pack_propagate(False)
        self.grid_propagate(False)
        self.last_update_time = time.time()

        # 进度条 - 加粗加长
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            self,
            variable=self.progress_var,
            maximum=100,
            length=600,  # 加长进度条
            style="Custom.Horizontal.TProgressbar"  # 使用自定义样式
        )
        self.progress_bar.pack(fill=tk.X, padx=15, pady=15)  # 增加内边距

        # 状态标签 - 加大字体
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            font=("Arial", 12, "bold"),
            anchor=tk.CENTER
        )
        status_label.pack(fill=tk.X, padx=15, pady=5)

        # 日志区域
        log_frame = ttk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # 添加日志过滤选项
        filter_frame = ttk.Frame(log_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="日志级别:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.log_level = tk.StringVar(value="all")
        level_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.log_level,
            values=["all", "info", "warning", "error"],
            state="readonly",
            width=8,
            font=("Arial", 10)
        )
        level_combo.pack(side=tk.LEFT, padx=5)
        level_combo.bind("<<ComboboxSelected>>", self.filter_logs)

        ttk.Button(
            filter_frame,
            text="清空日志",
            command=self.clear_log,
            width=10
        ).pack(side=tk.RIGHT, padx=5)

        # 加大日志区域
        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            state='disabled',
            wrap=tk.WORD,
            font=("Arial", 10),
            height=25,  # 增加高度
            width=120  # 增加宽度
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # 配置标签样式
        self.log_area.tag_config("error", foreground="red")
        self.log_area.tag_config("warning", foreground="orange")
        self.log_area.tag_config("info", foreground="blue")
        self.log_area.tag_config("success", foreground="green")
        self.log_area.tag_config("title", font=("Arial", 12, "bold"))
        self.log_area.tag_config("subtitle", font=("Arial", 10, "bold"))

        # 存储所有日志用于过滤
        self.all_logs = []

        # 添加日志处理器
        self.log_handler = TkinterLogHandler(self)
        logging.root.addHandler(self.log_handler)

    def log(self, message, level="info"):
        """添加日志消息"""
        # 存储日志
        self.all_logs.append((message, level))

        # 根据当前过滤级别显示日志
        if self.log_level.get() == "all" or self.log_level.get() == level:
            self.log_area.config(state='normal')
            self.log_area.insert(tk.END, message + "\n", level)
            self.log_area.see(tk.END)  # 滚动到底部
            self.log_area.config(state='disabled')

            # 自动滚动
            self.log_area.yview_moveto(1.0)

    def filter_logs(self, event=None):
        """过滤日志"""
        selected_level = self.log_level.get()

        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)

        for log_entry, level in self.all_logs:
            if selected_level == "all" or selected_level == level:
                self.log_area.insert(tk.END, log_entry + "\n", level)

        self.log_area.see(tk.END)  # 滚动到底部
        self.log_area.config(state='disabled')

    def update_progress(self, value):
        """更新进度条"""
        self.progress_var.set(value)
        self.update_idletasks()

    def update_status(self, message):
        """更新状态消息"""
        self.status_var.set(message)
        self.update_idletasks()

    def reset(self):
        """重置进度和状态"""
        self.progress_var.set(0)
        self.status_var.set("就绪")

    def clear_log(self):
        """清空日志"""
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        self.all_logs = []