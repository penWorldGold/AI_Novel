# analyzers/visualization.py
import os
import json
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from config_manager import ConfigManager


class StoryVisualizer:
    def __init__(self, config_manager):
        self.config = config_manager
        self.output_dir = config_manager.get('global', 'output_dir', 'output')

    def generate_story_graph(self):
        """生成故事脉络图"""
        # 加载分块数据
        block_path = os.path.join(self.output_dir, 'stage2_blocks', 'blocks.json')
        if not os.path.exists(block_path):
            return False

        with open(block_path, 'r', encoding='utf-8') as f:
            block_data = json.load(f)

        # 创建图结构
        G = nx.DiGraph()
        node_colors = []
        node_sizes = []

        # 添加节点（情节块）
        for i, block in enumerate(block_data['blocks']):
            conflict = block.get('main_conflict', '未知冲突')
            node_id = f"Block_{i + 1}"
            G.add_node(node_id, label=conflict)

            # 根据转折点数量设置节点大小
            turning_count = len(block.get('turning_points', []))
            node_sizes.append(500 + turning_count * 200)

            # 根据冲突类型设置颜色
            if '内部' in conflict:
                node_colors.append('lightcoral')
            elif '外部' in conflict:
                node_colors.append('lightgreen')
            else:
                node_colors.append('lightblue')

        # 添加边（块之间的关系）
        for i in range(len(block_data['blocks']) - 1):
            prev_block = block_data['blocks'][i]
            next_block = block_data['blocks'][i + 1]

            # 计算相似度
            prev_conflict = prev_block.get('main_conflict', '')
            next_conflict = next_block.get('main_conflict', '')
            similarity = self._calculate_similarity(prev_conflict, next_conflict)

            G.add_edge(f"Block_{i + 1}", f"Block_{i + 2}", weight=similarity)

        # 绘制图形
        plt.figure(figsize=(15, 10))

        # 根据配置选择布局
        layout_style = self.config.get('visualization', 'layout_style', 'circular')
        if layout_style == 'circular':
            pos = nx.circular_layout(G)
        else:  # spring
            pos = nx.spring_layout(G, seed=42)

        # 绘制节点和边
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.8)
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)

        # 添加标签
        labels = {node: G.nodes[node]['label'] for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=10)

        # 添加标题
        plt.title("故事脉络图 - 冲突演进", fontsize=16)
        plt.axis('off')

        # 保存图像
        graph_path = os.path.join(self.output_dir, 'story_graph.png')
        plt.savefig(graph_path, dpi=300, bbox_inches='tight')
        plt.close()

        return True

    def _calculate_similarity(self, str1, str2):
        """计算两个冲突描述的相似度"""
        words1 = set(str1.split())
        words2 = set(str2.split())
        intersection = words1 & words2
        return len(intersection) / max(len(words1), len(words2), 1)