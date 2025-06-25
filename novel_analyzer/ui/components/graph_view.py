# ui/components/graph_view.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os


class GraphView(ttk.Frame):
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.config = config_manager
        self.image_label = ttk.Label(self)
        self.image_label.pack(fill=tk.BOTH, expand=True)

        self.refresh_button = ttk.Button(self, text="刷新图像", command=self.refresh_image)
        self.refresh_button.pack(pady=5)

        self.refresh_image()

    def refresh_image(self):
        """刷新故事脉络图"""
        output_dir = self.config.get('global', 'output_dir', 'output')
        graph_path = os.path.join(output_dir, 'story_graph.png')

        if os.path.exists(graph_path):
            try:
                image = Image.open(graph_path)
                image = image.resize((800, 600), Image.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.image_label.config(image=photo)
                self.image_label.image = photo  # 保持引用
            except Exception as e:
                self.image_label.config(text=f"图像加载失败: {str(e)}")
        else:
            self.image_label.config(text="故事脉络图未生成")