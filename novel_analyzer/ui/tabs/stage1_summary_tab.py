# ui/tabs/stage1_summary_tab.py
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import os
from .base_tab import BaseTab
from analyzers.stage1_summary_analyzer import Stage1SummaryAnalyzer


class Stage1SummaryTab(BaseTab):
    def __init__(self, parent, config_manager, app):
        super().__init__(parent, config_manager, app)
        self.tab_name = "阶段1: 章节摘要"
        self.analyzer = Stage1SummaryAnalyzer(config_manager)

        # 配置区域
        config_frame = ttk.LabelFrame(self, text="摘要配置")
        config_frame.pack(fill=tk.X, pady=15, padx=15)

        # 章节范围
        ttk.Label(config_frame, text="章节范围:", font=("Arial", 10)).grid(
            row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.range_var = tk.StringVar(value=self.config.get('stage1', 'chapter_range'))
        range_entry = ttk.Entry(config_frame, textvariable=self.range_var, width=30)
        range_entry.grid(row=0, column=1, padx=10, pady=10)
        ttk.Label(config_frame, text="(例如: 1-10,15,20-30 或 all)", font=("Arial", 9)).grid(
            row=0, column=2, padx=10)

        # 术语绑定
        self.term_binding_var = tk.BooleanVar(value=self.config.get('stage1', 'term_binding') == 'true')
        ttk.Checkbutton(
            config_frame,
            text="术语绑定",
            variable=self.term_binding_var
        ).grid(row=0, column=3, padx=10)

        # 提示词区域
        prompt_frame = ttk.Frame(config_frame)
        prompt_frame.grid(row=1, column=0, columnspan=4, sticky=tk.W + tk.E, padx=10, pady=10)

        ttk.Label(prompt_frame, text="提示词:", font=("Arial", 10)).pack(side=tk.TOP, anchor=tk.W)
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, wrap=tk.WORD, height=15, width=100,
                                                     font=("Arial", 10))
        self.prompt_text.pack(fill=tk.X, expand=True)
        self.prompt_text.insert(tk.END, self.config.get('stage1', 'prompt'))

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

        # 控制按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=15, padx=15)

        ttk.Button(
            btn_frame,
            text="开始生成",
            command=self.start_generation,
            width=15
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            btn_frame,
            text="导出Excel",
            command=self.export_excel,
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
        self.config.set('stage1', 'chapter_range', self.range_var.get())
        self.config.set('stage1', 'term_binding', 'true' if self.term_binding_var.get() else 'false')
        self.config.set('stage1', 'prompt', self.prompt_text.get("1.0", tk.END).strip())
        self.config.save_config()
        self.log("摘要配置已保存")

    def restore_default(self):
        """恢复默认提示词"""
        default_prompt = self.config.defaults['stage1']['prompt']
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert(tk.END, default_prompt)
        self.log("已恢复默认提示词")

    def start_generation(self):
        """安全启动生成任务"""
        # 设置控制事件
        self.analyzer.set_control_events(
            self.app.pause_event,
            self.app.stop_event
        )
        self.app.start_task(self._run_generation)

    def _run_generation(self):
        """实际执行生成任务"""
        self.log("开始生成章节摘要...")
        self.reset_progress()  # 重置进度

        # 设置进度回调
        self.analyzer.progress_callback = lambda progress, message: self.app.update_progress(progress, message)

        if self.analyzer.run():
            self.log("章节摘要生成完成")
        else:
            self.log("章节摘要生成失败", level="error")

    def clear_files(self):
        """清除阶段1生成的文件"""
        output_dir = self.config.get('global', 'output_dir', 'output')
        summary_dir = os.path.join(output_dir, 'stage1_summaries')

        if os.path.exists(summary_dir):
            # 删除所有摘要文件
            for f in os.listdir(summary_dir):
                if f.endswith('.json'):
                    os.remove(os.path.join(summary_dir, f))
            self.log(f"已清除阶段1摘要文件: {summary_dir}")

            # 删除Excel文件
            excel_path = os.path.join(output_dir, 'chapter_summaries.xlsx')
            if os.path.exists(excel_path):
                os.remove(excel_path)
                self.log(f"已删除Excel文件: {excel_path}")
        else:
            self.log("未找到阶段1摘要目录", level="warning")

    def export_excel(self):
        """导出Excel"""
        from file_processor import FileProcessor
        output_dir = self.config.get('global', 'output_dir', 'output')
        excel_path = FileProcessor.export_summary_excel(output_dir)
        if excel_path:
            self.log(f"Excel文件已导出: {excel_path}")
        else:
            self.log("Excel导出失败", level="error")