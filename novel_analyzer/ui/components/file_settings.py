# ui/components/file_settings.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import logging
from config_manager import ConfigManager

logger = logging.getLogger(__name__)


class FileSettings(ttk.LabelFrame):
    def __init__(self, parent, config_manager):
        super().__init__(parent, text="文件设置")
        self.config = config_manager
        self.parent = parent

        # 使用网格布局确保比例
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

        # 小说文件路径
        ttk.Label(self, text="小说文件:", font=("Arial", 10)).grid(
            row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.novel_path_var = tk.StringVar(value=self.config.get('global', 'novel_path'))
        self.novel_entry = ttk.Entry(self, textvariable=self.novel_path_var, width=60)
        self.novel_entry.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W + tk.E)
        ttk.Button(
            self,
            text="浏览...",
            command=self.browse_novel,
            width=10
        ).grid(row=0, column=2, padx=10, sticky=tk.W)

        # 输出目录
        ttk.Label(self, text="输出目录:", font=("Arial", 10)).grid(
            row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.output_dir_var = tk.StringVar(value=self.config.get('global', 'output_dir'))
        self.output_entry = ttk.Entry(self, textvariable=self.output_dir_var, width=60)
        self.output_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W + tk.E)
        ttk.Button(
            self,
            text="浏览...",
            command=self.browse_output,
            width=10
        ).grid(row=1, column=2, padx=10, sticky=tk.W)

        # 新增打开目录按钮
        ttk.Button(
            self,
            text="打开目录",
            command=self.open_output_dir,
            width=10
        ).grid(row=1, column=3, padx=10, sticky=tk.W)

    def browse_novel(self):
        path = filedialog.askopenfilename(
            title="选择小说文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if path:
            self.novel_path_var.set(path)

    def browse_output(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir_var.set(path)

    def open_output_dir(self):
        """打开输出目录"""
        output_dir = self.output_dir_var.get()
        if output_dir and os.path.exists(output_dir):
            try:
                os.startfile(output_dir)  # Windows
                logger.info(f"已打开目录: {output_dir}")
            except:
                try:
                    import subprocess
                    subprocess.Popen(['xdg-open', output_dir])  # Linux
                    logger.info(f"已打开目录: {output_dir}")
                except Exception as e:
                    logger.error(f"打开目录失败: {str(e)}")
                    messagebox.showerror("错误", f"无法打开目录: {str(e)}")
        else:
            logger.warning("输出目录不存在")
            messagebox.showwarning("警告", "输出目录不存在")

    def save_settings(self):
        self.config.set('global', 'novel_path', self.novel_path_var.get())
        self.config.set('global', 'output_dir', self.output_dir_var.get())