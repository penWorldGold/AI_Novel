# ui/components/api_settings.py
import tkinter as tk
from tkinter import ttk
import logging
from config_manager import ConfigManager

logger = logging.getLogger(__name__)


class APISettings(ttk.LabelFrame):
    def __init__(self, parent, config_manager):
        super().__init__(parent, text="API设置")
        self.config = config_manager

        # 使用网格布局
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

        # API引擎选择
        ttk.Label(self, text="API引擎:", font=("Arial", 10)).grid(
            row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.engine_var = tk.StringVar(value=self.config.get('global', 'api_engine'))
        engine_combo = ttk.Combobox(
            self,
            textvariable=self.engine_var,
            values=["DeepSeek", "Kimi"],
            state="readonly",
            width=15,
            font=("Arial", 10)
        )
        engine_combo.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        # API密钥
        ttk.Label(self, text="API密钥:", font=("Arial", 10)).grid(
            row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.api_key_var = tk.StringVar(value=self.config.get('global', 'api_key'))
        self.api_entry = ttk.Entry(self, textvariable=self.api_key_var, width=60, show="*")
        self.api_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W + tk.E)

        # 密钥状态
        self.key_status = ttk.Label(self, text="", foreground="red", font=("Arial", 10))
        self.key_status.grid(row=1, column=2, padx=10, sticky=tk.W)

        # 显示/隐藏密钥按钮
        self.show_key = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self,
            text="显示密钥",
            variable=self.show_key,
            command=self.toggle_key_visibility,
            width=10
        ).grid(row=1, column=3, padx=10, sticky=tk.W)

        # API套餐选择
        ttk.Label(self, text="API套餐:", font=("Arial", 10)).grid(
            row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.plan_var = tk.StringVar(value=self.config.get('global', 'api_plan', 'free'))
        plan_combo = ttk.Combobox(
            self,
            textvariable=self.plan_var,
            values=["free", "paid"],
            state="readonly",
            width=15,
            font=("Arial", 10)
        )
        plan_combo.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

        # 套餐说明
        ttk.Label(self, text="(免费版有限速)", font=("Arial", 9), foreground="gray").grid(
            row=2, column=2, padx=5, sticky=tk.W)

        # 初始化密钥状态
        self._update_key_status()

    def toggle_key_visibility(self):
        if self.show_key.get():
            self.api_entry.config(show="")
        else:
            self.api_entry.config(show="*")
        self._update_key_status()

    def _update_key_status(self):
        """更新密钥状态显示"""
        key = self.api_key_var.get()
        if key:
            status = "密钥已设置" if self.show_key.get() else "密钥已隐藏"
            color = "green"
        else:
            status = "密钥未设置"
            color = "red"
        self.key_status.config(text=status, foreground=color)

    def save_settings(self):
        self.config.set('global', 'api_engine', self.engine_var.get())
        self.config.set('global', 'api_key', self.api_key_var.get())
        self.config.set('global', 'api_plan', self.plan_var.get())
        self._update_key_status()