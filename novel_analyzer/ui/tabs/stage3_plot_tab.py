# ui/tabs/stage3_plot_tab.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import json
from analyzers.stage3_plot_analyzer import Stage3PlotAnalyzer
from .base_tab import BaseTab


class Stage3PlotTab(BaseTab):
    def __init__(self, parent, config_manager, app):
        super().__init__(parent, config_manager, app)
        self.tab_name = "阶段3: 情节块摘要"
        self.analyzer = Stage3PlotAnalyzer(config_manager)

        # 配置区域
        config_frame = ttk.LabelFrame(self, text="情节摘要配置")
        config_frame.pack(fill=tk.X, pady=15, padx=15)

        # 伏笔关联深度
        ttk.Label(config_frame, text="伏笔关联深度:", font=("Arial", 10)).grid(
            row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.depth_var = tk.StringVar(value=self.config.get('stage3', 'foreshadow_depth'))
        depth_combo = ttk.Combobox(
            config_frame,
            textvariable=self.depth_var,
            values=["1", "2", "3"],
            state="readonly",
            width=5,
            font=("Arial", 10)
        )
        depth_combo.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        # 提示词区域
        prompt_frame = ttk.Frame(config_frame)
        prompt_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W + tk.E, padx=10, pady=10)

        ttk.Label(prompt_frame, text="提示词:", font=("Arial", 10)).pack(side=tk.TOP, anchor=tk.W)
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, wrap=tk.WORD, height=12, width=100,
                                                     font=("Arial", 10))
        self.prompt_text.pack(fill=tk.X, expand=True)
        self.prompt_text.insert(tk.END, self.config.get('stage3', 'prompt'))

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

        # 结果显示区域
        result_frame = ttk.LabelFrame(self, text="情节摘要")
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
            text="开始生成",
            command=self.start_generation,
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
        self.config.set('stage3', 'foreshadow_depth', self.depth_var.get())
        self.config.set('stage3', 'prompt', self.prompt_text.get("1.0", tk.END).strip())
        self.config.save_config()
        self.log("情节摘要配置已保存")

    def restore_default(self):
        """恢复默认提示词"""
        default_prompt = self.config.defaults['stage3']['prompt']
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
        self.log("开始生成情节块摘要...")
        if self.analyzer.run():
            self.log("情节块摘要生成完成")
            self.refresh_results()
        else:
            self.log("情节块摘要生成失败", level="error")

    def clear_files(self):
        """清除阶段3生成的文件"""
        # 使用基类方法清除文件
        self.clear_stage_files('stage3_plots', ['.json'])
        self.refresh_results()  # 刷新显示

    def refresh_results(self):
        """刷新结果显示"""
        output_dir = self.config.get('global', 'output_dir', 'output')
        plot_dir = os.path.join(output_dir, 'stage3_plots')

        self.result_text.delete(1.0, tk.END)

        if os.path.exists(plot_dir):
            plot_files = sorted(
                [f for f in os.listdir(plot_dir) if f.endswith('.json')],
                key=lambda x: int(x.split('_')[1].split('.')[0])
            )

            if not plot_files:
                self.result_text.insert(tk.END, "未找到情节块摘要文件", "info")
                return

            for plot_file in plot_files:
                plot_path = os.path.join(plot_dir, plot_file)
                try:
                    with open(plot_path, 'r', encoding='utf-8') as f:
                        plot_data = json.load(f)

                    block_id = plot_data.get('block_id', '?')
                    self.result_text.insert(tk.END, f"情节块 {block_id}:\n", "title")
                    self.result_text.insert(tk.END, f"核心目标: {plot_data.get('core_goal', '')}\n")

                    # 三幕结构
                    self.result_text.insert(tk.END, "\n三幕结构:\n", "subtitle")
                    three_acts = plot_data.get('three_acts', {})
                    self.result_text.insert(tk.END, f"发端: {three_acts.get('setup', '')}\n")
                    self.result_text.insert(tk.END, "升级:\n")
                    for event in three_acts.get('confrontation', []):
                        self.result_text.insert(tk.END, f"  - {event}\n")
                    self.result_text.insert(tk.END, f"落定: {three_acts.get('resolution', '')}\n")

                    # 角色弧光
                    self.result_text.insert(tk.END, "\n角色弧光:\n", "subtitle")
                    for arc in plot_data.get('character_arcs', []):
                        self.result_text.insert(tk.END, f"  - {arc}\n")

                    # 未解伏笔
                    self.result_text.insert(tk.END, "\n未解伏笔:\n", "subtitle")
                    for foreshadowing in plot_data.get('unsolved_foreshadowings', []):
                        self.result_text.insert(tk.END, f"  - {foreshadowing}\n")

                    self.result_text.insert(tk.END, "\n" + "=" * 80 + "\n\n")

                except Exception as e:
                    self.result_text.insert(tk.END, f"文件 {plot_file} 解析失败: {str(e)}\n", "error")
        else:
            self.result_text.insert(tk.END, "情节块摘要未生成", "info")