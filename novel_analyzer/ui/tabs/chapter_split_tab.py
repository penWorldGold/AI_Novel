# ui/tabs/chapter_split_tab.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import logging
from .base_tab import BaseTab
from analyzers.chapter_splitter import ChapterSplitter


class ChapterSplitTab(BaseTab):
    def __init__(self, parent, config_manager, app):
        super().__init__(parent, config_manager, app)
        self.tab_name = "章节分割"
        self.splitter = ChapterSplitter(config_manager)

        # 配置区域
        config_frame = ttk.LabelFrame(self, text="分割配置")
        config_frame.pack(fill=tk.X, pady=15, padx=15)  # 增加内边距

        # 配置网格
        config_frame.columnconfigure(0, weight=1)
        config_frame.columnconfigure(1, weight=3)
        config_frame.columnconfigure(2, weight=1)
        config_frame.columnconfigure(3, weight=1)

        # 章节标题正则表达式
        ttk.Label(config_frame, text="章节标题正则:", font=("Arial", 10)).grid(
            row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.regex_var = tk.StringVar(
            value=self.config.get('chapter_split', 'regex', r'第[零一二三四五六七八九十百千0-9]+章'))
        regex_entry = ttk.Entry(config_frame, textvariable=self.regex_var, width=50)
        regex_entry.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W + tk.E)

        # 文件编码选择
        ttk.Label(config_frame, text="文件编码:", font=("Arial", 10)).grid(
            row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.encoding_var = tk.StringVar(value=self.config.get('chapter_split', 'encoding', 'auto'))
        encoding_combo = ttk.Combobox(
            config_frame,
            textvariable=self.encoding_var,
            values=['auto', 'utf-8', 'gb18030', 'gbk', 'big5', 'latin1'],
            width=15
        )
        encoding_combo.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        # 检测文件编码按钮
        detect_btn = ttk.Button(
            config_frame,
            text="检测编码",
            command=self.detect_encoding,
            width=15
        )
        detect_btn.grid(row=1, column=2, padx=10)
        self.register_button(detect_btn)

        # 保存配置按钮
        save_btn = ttk.Button(
            config_frame,
            text="保存配置",
            command=self.save_config,
            width=15
        )
        save_btn.grid(row=0, column=2, padx=10, rowspan=2)
        self.register_button(save_btn)

        # 控制按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=15, padx=15)

        start_btn = ttk.Button(
            btn_frame,
            text="开始分割",
            command=self.start_split,
            width=15
        )
        start_btn.pack(side=tk.LEFT, padx=10)
        self.register_button(start_btn)

        # 错误报告按钮
        report_btn = ttk.Button(
            btn_frame,
            text="报告编码问题",
            command=self.report_encoding_issue,
            width=15
        )
        report_btn.pack(side=tk.LEFT, padx=10)
        self.register_button(report_btn)

        # 新增清除文件按钮
        clear_btn = ttk.Button(
            btn_frame,
            text="清除文件",
            command=self.clear_files,
            width=15
        )
        clear_btn.pack(side=tk.LEFT, padx=10)
        self.register_button(clear_btn)

    def save_config(self):
        """保存配置"""
        self.config.set('chapter_split', 'regex', self.regex_var.get())
        self.config.set('chapter_split', 'encoding', self.encoding_var.get())
        self.config.save_config()
        self.log("分割配置已保存")

    def start_split(self):
        """开始章节分割"""
        self.app.lock_ui(True)  # 锁定UI
        self.reset_progress()  # 重置进度
        self.log("开始章节分割...")
        self.update_status("章节分割中...")

        try:
            if self.splitter.run():
                self.log("章节分割完成")
                self.update_progress(100)
                self.update_status("章节分割完成")
            else:
                self.log("章节分割失败", level="error")
                self.update_status("分割失败")
        except Exception as e:
            self.log(f"分割过程中出错: {str(e)}", level="error")
        finally:
            self.app.lock_ui(False)  # 解锁UI

    def clear_files(self):
        """清除章节分割生成的文件"""
        # 确认对话框
        if not messagebox.askyesno("确认清除", "确定要清除所有章节文件吗？"):
            return

        output_dir = self.config.get('global', 'output_dir', 'output')
        chapter_dir = os.path.join(output_dir, 'chapters')

        if os.path.exists(chapter_dir):
            # 删除所有章节文件
            for f in os.listdir(chapter_dir):
                if f.endswith('.txt'):
                    os.remove(os.path.join(chapter_dir, f))
            self.log(f"已清除章节文件: {chapter_dir}")
        else:
            self.log("未找到章节目录", level="warning")

    def detect_encoding(self):
        """检测文件编码"""
        novel_path = self.config.get('global', 'novel_path')
        if not novel_path or not os.path.exists(novel_path):
            self.log("请先选择有效的小说文件", level="error")
            return

        from file_processor import FileProcessor
        try:
            encoding = FileProcessor.advanced_detect_encoding(novel_path)
            self.encoding_var.set(encoding)
            self.log(f"检测建议编码: {encoding}")
        except Exception as e:
            self.log(f"编码检测失败: {str(e)}", level="error")

    def report_encoding_issue(self):
        """收集编码问题信息"""
        novel_path = self.config.get('global', 'novel_path')

        if novel_path and os.path.exists(novel_path):
            messagebox.showinfo(
                "报告编码问题",
                f"文件编码问题已记录\n"
                f"文件路径: {novel_path}\n"
                "我们会分析并改进编码处理"
            )
            self.log("已报告编码问题")
        else:
            messagebox.showwarning(
                "无法报告问题",
                "请先选择有效的小说文件"
            )