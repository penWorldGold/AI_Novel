# ui/app.py
import tkinter as tk
from tkinter import ttk
import logging
import threading
from config_manager import ConfigManager
from components.file_settings import FileSettings
from components.api_settings import APISettings
from components.progress_log import ProgressLog
from tabs.chapter_split_tab import ChapterSplitTab
from tabs.stage1_summary_tab import Stage1SummaryTab
from tabs.stage2_block_tab import Stage2BlockTab
from tabs.stage3_plot_tab import Stage3PlotTab
from tabs.stage4_outline_tab import Stage4OutlineTab
from tabs.visualization_tab import VisualizationTab


class NovelAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("小说智能分析系统")
        self.geometry("1600x1200")  # 扩大窗口尺寸
        self.config_manager = ConfigManager()
        self.running_thread = None
        self.pause_event = threading.Event()  # 暂停控制
        self.stop_event = threading.Event()  # 停止控制

        # 添加全局样式
        style = ttk.Style()
        style.configure("TFrame", padding=5)
        style.configure("TLabelFrame", padding=10)
        style.configure("TButton", padding=5, font=("Arial", 10))
        style.configure("TCombobox", padding=3, font=("Arial", 10))
        style.configure("TProgressbar", thickness=20)  # 加粗进度条
        style.configure("TLabel", font=("Arial", 10))
        style.configure("TCheckbutton", font=("Arial", 10))  # 添加复选框样式

        # 创建主网格布局 (3:5比例)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)  # 左侧占3份
        self.grid_columnconfigure(1, weight=5)  # 右侧占5份

        # 左侧面板 (3/8)
        self.left_panel = ttk.Frame(self)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.left_panel.grid_rowconfigure(0, weight=4)  # 上部设置区域占4份
        self.left_panel.grid_rowconfigure(1, weight=6)  # 下部日志区域占6份
        self.left_panel.grid_columnconfigure(0, weight=1)

        # 左上部分 - 全局设置
        self.settings_frame = ttk.LabelFrame(self.left_panel, text="全局设置")
        self.settings_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 15))
        self.settings_frame.grid_rowconfigure(0, weight=1)
        self.settings_frame.grid_columnconfigure(0, weight=1)

        # 文件设置
        self.file_settings = FileSettings(self.settings_frame, self.config_manager)
        self.file_settings.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # API设置
        self.api_settings = APISettings(self.settings_frame, self.config_manager)
        self.api_settings.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 保存按钮
        save_frame = ttk.Frame(self.settings_frame)
        save_frame.pack(fill=tk.X, pady=10, padx=10)

        ttk.Button(
            save_frame,
            text="保存全局设置",
            command=self.save_global_settings,
            width=15
        ).pack(side=tk.LEFT, padx=10)

        self.save_status = ttk.Label(save_frame, text="", foreground="green", font=("Arial", 10))
        self.save_status.pack(side=tk.LEFT, padx=10)

        # 左下部分 - 进度与日志
        self.progress_log = ProgressLog(self.left_panel)
        self.progress_log.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        # 右侧面板 (5/8) - Tab区域
        self.right_panel = ttk.Frame(self)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        # 标签页
        self.notebook = ttk.Notebook(self.right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 添加标签页
        self.tabs = {
            "ch_split": ChapterSplitTab(self.notebook, self.config_manager, self),
            "stage1": Stage1SummaryTab(self.notebook, self.config_manager, self),
            "stage2": Stage2BlockTab(self.notebook, self.config_manager, self),
            "stage3": Stage3PlotTab(self.notebook, self.config_manager, self),
            "stage4": Stage4OutlineTab(self.notebook, self.config_manager, self),
            "visual": VisualizationTab(self.notebook, self.config_manager, self)
        }

        for name, tab in self.tabs.items():
            self.notebook.add(tab, text=tab.tab_name)

        # 添加任务控制按钮
        self.control_frame = ttk.Frame(self)
        self.control_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=10)

        self.pause_btn = ttk.Button(
            self.control_frame,
            text="暂停任务",
            command=self.toggle_pause,
            width=15
        ).pack(side=tk.LEFT, padx=10)

        self.stop_btn = ttk.Button(
            self.control_frame,
            text="停止任务",
            command=self.stop_task,
            state=tk.DISABLED,
            width=15
        ).pack(side=tk.LEFT, padx=10)

        # 设置初始大小
        self.update_idletasks()
        self.minsize(1400, 1000)

    def save_global_settings(self):
        """保存全局设置"""
        self.file_settings.save_settings()
        self.api_settings.save_settings()
        self.config_manager.save_config()
        self.save_status.config(text="✓ 全局设置已保存")

        # 初始化输出目录
        output_dir = self.config_manager.get('global', 'output_dir')
        if output_dir:
            from file_processor import FileProcessor
            try:
                FileProcessor.create_output_structure(output_dir)
            except Exception as e:
                logging.error(f"创建输出目录失败: {str(e)}")

    def lock_ui(self, locked=True):
        """锁定/解锁UI"""
        state = tk.DISABLED if locked else tk.NORMAL

        # 禁用所有标签页内的按钮
        for tab in self.tabs.values():
            tab.set_ui_state(state)

        # 更新停止按钮状态
        self.stop_btn.config(state=tk.NORMAL if locked else tk.DISABLED)

    def start_task(self, task_func):
        """启动任务线程"""
        if self.running_thread and self.running_thread.is_alive():
            self.progress_log.log("已有任务进行中，请等待完成", "warning")
            return

        self.pause_event.clear()
        self.stop_event.clear()

        # 重置进度
        self.progress_log.reset()

        # 创建并启动线程
        self.running_thread = threading.Thread(
            target=self._run_task,
            args=(task_func,),
            daemon=True
        )
        self.running_thread.start()

        # 启用UI锁定
        self.lock_ui(True)

    def _run_task(self, task_func):
        """执行任务"""
        try:
            task_func()
        except Exception as e:
            self.progress_log.log(f"任务执行出错: {str(e)}", "error")
        finally:
            # 任务完成后更新UI
            self.after(0, self._task_completed)

    def _task_completed(self):
        """任务完成后的清理工作"""
        self.lock_ui(False)
        self.stop_btn.config(state=tk.DISABLED)
        self.pause_btn.config(text="暂停任务")
        self.running_thread = None

    def toggle_pause(self):
        """暂停/继续任务"""
        if not self.running_thread or not self.running_thread.is_alive():
            return

        if self.pause_event.is_set():
            # 继续任务
            self.pause_event.clear()
            self.pause_btn.config(text="暂停任务")
            self.progress_log.log("任务已继续")
        else:
            # 暂停任务
            self.pause_event.set()
            self.pause_btn.config(text="继续任务")
            self.progress_log.log("任务已暂停")

    def stop_task(self):
        """停止当前任务"""
        if self.running_thread and self.running_thread.is_alive():
            self.stop_event.set()
            self.pause_event.set()  # 确保任务停止
            self.progress_log.log("正在停止任务...", "warning")
            self.stop_btn.config(state=tk.DISABLED)

    def log(self, message, level="info"):
        """添加日志"""
        self.progress_log.log(message, level)

    def update_progress(self, value, message=None):
        """更新进度"""
        if message:
            self.progress_log.update_status(message)
        self.progress_log.update_progress(value)

    def update_status(self, message):
        """更新状态"""
        self.progress_log.update_status(message)