# ui/tabs/stage4_outline_tab.py
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import os
import shutil
from analyzers.stage4_outline_analyzer import Stage4OutlineAnalyzer
from .base_tab import BaseTab


class Stage4OutlineTab(BaseTab):
    def __init__(self, parent, config_manager, app):
        super().__init__(parent, config_manager, app)
        self.tab_name = "阶段4: 全书大纲"
        self.analyzer = Stage4OutlineAnalyzer(config_manager)

        # 配置区域
        config_frame = ttk.LabelFrame(self, text="大纲配置")
        config_frame.pack(fill=tk.X, pady=15, padx=15)

        # 高潮事件阈值
        ttk.Label(config_frame, text="高潮事件阈值:", font=("Arial", 10)).grid(
            row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.climax_var = tk.StringVar(value=self.config.get('stage4', 'climax_threshold'))
        climax_combo = ttk.Combobox(
            config_frame,
            textvariable=self.climax_var,
            values=["3", "4"],
            state="readonly",
            width=5,
            font=("Arial", 10)
        )
        climax_combo.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        # 提示词区域
        prompt_frame = ttk.Frame(config_frame)
        prompt_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W + tk.E, padx=10, pady=10)

        ttk.Label(prompt_frame, text="提示词:", font=("Arial", 10)).pack(side=tk.TOP, anchor=tk.W)
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, wrap=tk.WORD, height=15, width=100,
                                                     font=("Arial", 10))
        self.prompt_text.pack(fill=tk.X, expand=True)
        self.prompt_text.insert(tk.END, self.config.get('stage4', 'prompt'))

        # 按钮区域
        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

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

        # 大纲显示区域
        self.output_area = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            font=("Arial", 10)
        )
        self.output_area.pack(fill=tk.BOTH, expand=True, pady=15, padx=15)

        # 控制按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=15, padx=15)

        ttk.Button(
            btn_frame,
            text="生成大纲",
            command=self.generate_outline,
            width=15
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            btn_frame,
            text="导出Markdown",
            command=self.export_markdown,
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
        self.config.set('stage4', 'climax_threshold', self.climax_var.get())
        self.config.set('stage4', 'prompt', self.prompt_text.get("1.0", tk.END).strip())
        self.config.save_config()
        self.log("大纲配置已保存")

    def restore_default(self):
        """恢复默认提示词"""
        default_prompt = self.config.defaults['stage4']['prompt']
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert(tk.END, default_prompt)
        self.log("已恢复默认提示词")

    def generate_outline(self):
        """安全启动大纲生成"""
        # 设置控制事件
        self.analyzer.set_control_events(
            self.app.pause_event,
            self.app.stop_event
        )
        self.app.start_task(self._run_generate_outline)

    def _run_generate_outline(self):
        """实际执行大纲生成"""
        self.log("开始生成全书大纲...")
        self.output_area.delete(1.0, tk.END)

        try:
            success, result = self.analyzer.run()
            if success:
                self.output_area.insert(tk.END, result)
                self.log("全书大纲生成成功")
            else:
                self.log("大纲生成失败，请检查日志", level="error")
        except Exception as e:
            self.log(f"大纲生成出错: {str(e)}", level="error")

    def clear_files(self):
        """清除阶段4生成的文件"""
        # 使用基类方法清除文件
        self.clear_stage_files('stage4_outline', ['.txt', '.md'])
        self.output_area.delete(1.0, tk.END)  # 清空显示区域

    def export_markdown(self):
        """导出为Markdown文件"""
        output_dir = self.config.get('global', 'output_dir', 'output')
        outline_path = os.path.join(output_dir, 'stage4_outline', 'full_outline.txt')

        if os.path.exists(outline_path):
            save_path = filedialog.asksaveasfilename(
                title="保存大纲文件",
                filetypes=[("Markdown文件", "*.md"), ("文本文件", "*.txt")],
                defaultextension=".md"
            )
            if save_path:
                try:
                    import shutil
                    shutil.copy(outline_path, save_path)
                    self.log(f"大纲已导出到: {save_path}")
                except Exception as e:
                    self.log(f"导出失败: {str(e)}", level="error")
        else:
            self.log("大纲文件未生成", level="error")