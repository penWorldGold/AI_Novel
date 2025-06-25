# ui/tabs/visualization_tab.py
import tkinter as tk
from tkinter import ttk
from analyzers.visualization import StoryVisualizer
from ui.components.graph_view import GraphView
from .base_tab import BaseTab
import os


class VisualizationTab(BaseTab):
    def __init__(self, parent, config_manager, app):
        super().__init__(parent, config_manager, app)
        self.tab_name = "可视化"
        self.visualizer = StoryVisualizer(config_manager)

        # 配置区域
        config_frame = ttk.LabelFrame(self, text="可视化配置")
        config_frame.pack(fill=tk.X, pady=15, padx=15)

        ttk.Label(config_frame, text="布局样式:", font=("Arial", 10)).grid(
            row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.layout_var = tk.StringVar(value=self.config.get('visualization', 'layout_style'))
        layout_combo = ttk.Combobox(
            config_frame,
            textvariable=self.layout_var,
            values=["circular", "spring"],
            width=15,
            font=("Arial", 10)
        )
        layout_combo.grid(row=0, column=1, padx=10, pady=10)

        ttk.Button(
            config_frame,
            text="保存配置",
            command=self.save_config,
            width=15
        ).grid(row=0, column=2, padx=10)

        # 图形显示区域
        self.graph_view = GraphView(self, config_manager)
        self.graph_view.pack(fill=tk.BOTH, expand=True, pady=15, padx=15)

        # 控制按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=15, padx=15)

        ttk.Button(
            btn_frame,
            text="生成脉络图",
            command=self.generate_graph,
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
        self.config.set('visualization', 'layout_style', self.layout_var.get())
        self.config.save_config()
        self.log("可视化配置已保存")

    def clear_files(self):
        """清除可视化生成的文件"""
        output_dir = self.config.get('global', 'output_dir', 'output')
        graph_path = os.path.join(output_dir, 'story_graph.png')

        if os.path.exists(graph_path):
            os.remove(graph_path)
            self.log(f"已删除脉络图: {graph_path}")
            self.graph_view.refresh_image()  # 刷新显示
        else:
            self.log("未找到脉络图文件", level="warning")

    def generate_graph(self):
        """安全启动脉络图生成"""
        # 设置控制事件
        self.visualizer.set_control_events(
            self.app.pause_event,
            self.app.stop_event
        )
        self.app.start_task(self._run_generate_graph)

    def _run_generate_graph(self):
        """实际执行脉络图生成"""
        self.log("开始生成故事脉络图...")
        if self.visualizer.generate_story_graph():
            self.log("故事脉络图生成成功")
            self.graph_view.refresh_image()
        else:
            self.log("故事脉络图生成失败", level="error")