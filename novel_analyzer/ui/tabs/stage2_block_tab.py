# ui/tabs/stage2_block_tab.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import json
import shutil
from analyzers.stage2_block_analyzer import Stage2BlockAnalyzer
from .base_tab import BaseTab


class Stage2BlockTab(BaseTab):
    def __init__(self, parent, config_manager, app):
        super().__init__(parent, config_manager, app)
        self.tab_name = "阶段2: 自动分块"
        self.analyzer = Stage2BlockAnalyzer(config_manager)

        # 配置区域
        config_frame = ttk.LabelFrame(self, text="分块配置")
        config_frame.pack(fill=tk.X, pady=15, padx=15)

        # 分块敏感度
        ttk.Label(config_frame, text="分块敏感度:", font=("Arial", 10)).grid(
            row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.sensitivity_var = tk.StringVar(value=self.config.get('stage2', 'block_sensitivity'))
        sensitivity_combo = ttk.Combobox(
            config_frame,
            textvariable=self.sensitivity_var,
            values=["low", "medium", "high"],
            state="readonly",
            width=10,
            font=("Arial", 10)
        )
        sensitivity_combo.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        # 跨卷分块
        self.cross_volume_var = tk.BooleanVar(value=self.config.get('stage2', 'cross_volume') == 'true')
        ttk.Checkbutton(
            config_frame,
            text="允许跨卷分块",
            variable=self.cross_volume_var
        ).grid(row=0, column=2, padx=10)

        # 提示词区域
        prompt_frame = ttk.Frame(config_frame)
        prompt_frame.grid(row=1, column=0, columnspan=4, sticky=tk.W + tk.E, padx=10, pady=10)

        ttk.Label(prompt_frame, text="提示词:", font=("Arial", 10)).pack(side=tk.TOP, anchor=tk.W)
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, wrap=tk.WORD, height=10, width=100,
                                                     font=("Arial", 10))
        self.prompt_text.pack(fill=tk.X, expand=True)
        self.prompt_text.insert(tk.END, self.config.get('stage2', 'prompt'))

        # 按钮区域
        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=2, column=0, columnspan=4, pady=10)

        ttk.Button(
            button_frame,
            text="保存配置",
            command=self.save_config,
            width=15
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            button_frame,
            text="恢复默认",
            command=self.restore_default,
            width=15
        ).pack(side=tk.LEFT, padx=10)

        # 结果显示区域
        result_frame = ttk.LabelFrame(self, text="分块结果")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=15, padx=15)

        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            font=("Arial", 10)
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 控制按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=15, padx=15)

        ttk.Button(
            btn_frame,
            text="开始分块",
            command=self.start_blocking,
            width=15
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            btn_frame,
            text="刷新显示",
            command=self.refresh_results,
            width=15
        ).pack(side=tk.LEFT, padx=10)

        # 新增清除文件按钮
        ttk.Button(
            btn_frame,
            text="清除文件",
            command=self.clear_files,
            width=15
        ).pack(side=tk.LEFT, padx=10)

    def save_config(self):
        """保存配置"""
        self.config.set('stage2', 'block_sensitivity', self.sensitivity_var.get())
        self.config.set('stage2', 'cross_volume', 'true' if self.cross_volume_var.get() else 'false')
        self.config.set('stage2', 'prompt', self.prompt_text.get("1.0", tk.END).strip())
        self.config.save_config()
        self.log("分块配置已保存")

    def restore_default(self):
        """恢复默认提示词"""
        default_prompt = self.config.defaults['stage2']['prompt']
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert(tk.END, default_prompt)
        self.log("已恢复默认提示词")

    def start_blocking(self):
        """安全启动分块任务"""
        # 设置控制事件
        self.analyzer.set_control_events(
            self.app.pause_event,
            self.app.stop_event
        )
        self.app.start_task(self._run_blocking)

    def _run_blocking(self):
        """实际执行分块任务"""
        self.log("开始自动分块分析...")
        if self.analyzer.run():
            self.log("自动分块完成")
            self.refresh_results()
        else:
            self.log("自动分块失败", level="error")

    def clear_files(self):
        """清除阶段2生成的文件"""
        # 使用基类方法清除文件
        self.clear_stage_files('stage2_blocks', ['.json'])
        self.refresh_results()  # 刷新显示

    def refresh_results(self):
        """刷新结果显示"""
        output_dir = self.config.get('global', 'output_dir', 'output')
        block_path = os.path.join(output_dir, 'stage2_blocks', 'blocks.json')

        self.result_text.delete(1.0, tk.END)

        if os.path.exists(block_path):
            try:
                with open(block_path, 'r', encoding='utf-8') as f:
                    block_data = json.load(f)

                # 格式化显示结果
                for i, block in enumerate(block_data['blocks'], 1):
                    self.result_text.insert(tk.END, f"块 {i}:\n", "title")
                    self.result_text.insert(tk.END, f"  章节: {block['chapters'][0]}-{block['chapters'][-1]}\n")
                    self.result_text.insert(tk.END, f"  核心冲突: {block['main_conflict']}\n")
                    self.result_text.insert(tk.END, f"  转折点: {block['turning_points']}\n")

                    if 'alert' in block:
                        self.result_text.insert(tk.END, f"  警告: {block['alert']}\n", "warning")

                    self.result_text.insert(tk.END, "\n")

                if block_data.get('alert'):
                    self.result_text.insert(tk.END, f"系统警告: {block_data['alert']}\n", "error")
            except Exception as e:
                self.result_text.insert(tk.END, f"结果解析失败: {str(e)}", "error")
        else:
            self.result_text.insert(tk.END, "分块结果未生成", "info")