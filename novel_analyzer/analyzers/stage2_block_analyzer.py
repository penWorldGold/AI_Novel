# analyzers/stage2_block_analyzer.py
import json
import os
import logging
import numpy as np
from sklearn.cluster import DBSCAN
from collections import defaultdict
from .base_analyzer import BaseAnalyzer


class Stage2BlockAnalyzer(BaseAnalyzer):
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.logger = logging.getLogger(__name__)
        self.sensitivity_map = {
            'low': {'min_pts': 8, 'eps': 1.2},
            'medium': {'min_pts': 5, 'eps': 1.0},
            'high': {'min_pts': 3, 'eps': 0.8}
        }
        self.default_prompt = """# 角色：分块分析师
# 输入：章节摘要列表
# 输出要求（严格JSON格式）：
{{
  "blocks": [
    {{
      "block_id": 1,
      "chapters": [101,102,...],
      "main_conflict": "人族vs妖族",
      "turning_points": [115]
    }}
  ],
  "alert": "异常提示"
}}

# 分块规则：
1. 核心切割点：转折分≥4 或章节数达25章
2. 连续≤1分章节≥5章 → 合并到前块
3. 块边界校验：
   - 相邻块核心冲突对象必须不同
   - 每块必须包含≥1个转折分≥3章节"""

    def run(self):
        """执行分块分析"""
        # 检查暂停/停止请求
        if not self.check_pause() or self.check_stop():
            self.logger.info("任务被用户中断")
            return False

        output_dir = self.get_output_dir()
        summary_dir = os.path.join(output_dir, 'stage1_summaries')
        block_path = os.path.join(output_dir, 'stage2_blocks', 'blocks.json')

        # 跳过已存在的结果
        if os.path.exists(block_path):
            self.logger.info("分块结果已存在，跳过处理")
            return True

        # 加载所有摘要
        self.update_progress(0, 100, "加载章节摘要...")
        summaries = self._load_summaries(summary_dir)
        if not summaries:
            self.logger.error("未找到章节摘要，请先完成阶段1分析")
            return False

        total_steps = 5  # 总步骤数
        current_step = 1
        self.logger.info(f"成功加载 {len(summaries)} 个章节摘要")

        # 预聚类分组
        self.update_progress(current_step * 20, 100, "进行章节聚类...")
        if not self.check_pause() or self.check_stop():
            return False
        clusters = self._pre_cluster(summaries)
        self.logger.info(f"聚类完成，得到 {len(clusters)} 个初始分组")
        current_step += 1

        # 应用分块规则
        self.update_progress(current_step * 20, 100, "应用分块规则...")
        if not self.check_pause() or self.check_stop():
            return False
        blocks = self._apply_block_rules(clusters, summaries)
        self.logger.info(f"分块完成，得到 {len(blocks)} 个情节块")
        current_step += 1

        # 构建提示词
        self.update_progress(current_step * 20, 100, "构建API提示词...")
        if not self.check_pause() or self.check_stop():
            return False
        prompt = self.build_prompt(summaries)
        current_step += 1

        # 调用API生成分块结果
        self.update_progress(current_step * 20, 100, "调用API进行分块分析...")
        self.logger.info("调用API进行分块分析...")
        try:
            if not self.check_pause() or self.check_stop():
                return False
            response = self.api_handler.generate(prompt)
        except Exception as e:
            self.logger.error(f"API调用失败: {str(e)}")
            return False

        try:
            # 解析API响应
            result = self.parse_response(response)
            # 添加聚类结果
            result['blocks'] = blocks
            # 保存结果
            os.makedirs(os.path.dirname(block_path), exist_ok=True)
            with open(block_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            self.update_progress(100, 100, "分块分析完成")
            self.logger.info("分块分析完成")
            return True
        except Exception as e:
            self.logger.error(f"分块分析失败: {str(e)}")
            return False
        try:
            # 解析API响应
            result = self.parse_response(response)
            # 添加聚类结果
            result['blocks'] = blocks
            # 保存结果
            os.makedirs(os.path.dirname(block_path), exist_ok=True)
            with open(block_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            self.update_progress(100, 100, "分块分析完成")
            self.logger.info("分块分析完成")
            return True
        except Exception as e:
            self.logger.error(f"分块分析失败: {str(e)}")
            return False

    def build_prompt(self, summaries):
        """构建分块提示词"""
        # 从配置获取自定义提示词
        custom_prompt = self.config.get('stage2', 'prompt', self.default_prompt)

        # 准备摘要数据
        summary_data = []
        for s in summaries:
            summary_data.append({
                'chapter': s['chapter'],
                'summary': s['summary'],
                'turning_score': s['turning_score']
            })

        # 替换占位符
        prompt = custom_prompt + "\n\n# 章节摘要数据:\n" + json.dumps(summary_data, ensure_ascii=False, indent=2)
        return prompt

    def parse_response(self, response):
        """解析API响应"""
        try:
            # 尝试提取JSON部分
            start = response.find('{')
            end = response.rfind('}') + 1
            return json.loads(response[start:end])
        except json.JSONDecodeError:
            self.logger.error(f"API响应解析失败: {response}")
            raise ValueError("API返回了无效的JSON格式")

    def _load_summaries(self, summary_dir):
        """加载所有章节摘要，支持0编号的前言"""
        summaries = []
        # 获取所有摘要文件并按数字排序
        summary_files = []
        for fname in os.listdir(summary_dir):
            if fname.endswith('.json'):
                # 提取数字部分
                try:
                    num_part = re.search(r'summary_(\d+)\.json', fname).group(1)
                    num = int(num_part)
                    summary_files.append((num, fname))
                except:
                    continue

        # 按章节号排序
        summary_files.sort(key=lambda x: x[0])

        # 加载摘要内容
        for num, fname in summary_files:
            with open(os.path.join(summary_dir, fname), 'r', encoding='utf-8') as f:
                summary = json.load(f)
                # 确保章节号正确
                summary['chapter'] = num
                summaries.append(summary)

        return summaries

    def _pre_cluster(self, summaries):
        """使用DBSCAN预聚类"""
        # 提取特征：转折分序列
        scores = [s['turning_score'] for s in summaries]

        # 配置聚类参数
        sensitivity = self.config.get('stage2', 'block_sensitivity', fallback='medium')
        params = self.sensitivity_map.get(sensitivity, self.sensitivity_map['medium'])

        # 执行聚类
        X = np.array(scores).reshape(-1, 1)
        clustering = DBSCAN(eps=params['eps'], min_samples=params['min_pts']).fit(X)

        # 构建聚类结果
        clusters = {}
        for i, label in enumerate(clustering.labels_):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(summaries[i]['chapter'])

        return list(clusters.values())

    def _apply_block_rules(self, clusters, summaries):
        """应用分块规则"""
        blocks = []
        current_block = []
        chapter_map = {s['chapter']: s for s in summaries}

        for cluster in clusters:
            # 规则1: 转折分≥4或章节数达25章
            if any(chapter_map[ch]['turning_score'] >= 4 for ch in cluster) or len(cluster) >= 25:
                if current_block:
                    blocks.append(self._finalize_block(current_block, chapter_map))
                current_block = cluster
            else:
                current_block.extend(cluster)

        if current_block:
            blocks.append(self._finalize_block(current_block, chapter_map))

        # 规则2: 连续低分章节合并
        merged_blocks = []
        for block in blocks:
            if not merged_blocks:
                merged_blocks.append(block)
                continue

            # 检查是否为低分块
            low_score_chapters = [ch for ch in block['chapters'] if chapter_map[ch]['turning_score'] <= 1]
            if len(low_score_chapters) >= 5:
                # 合并到前一块
                prev_block = merged_blocks[-1]
                prev_block['chapters'].extend(block['chapters'])
                prev_block['chapters'].sort()
                # 更新转折点
                prev_turning_points = set(prev_block.get('turning_points', []))
                prev_turning_points.update(block.get('turning_points', []))
                prev_block['turning_points'] = sorted(prev_turning_points)
            else:
                merged_blocks.append(block)

        # 规则3: 块边界校验
        final_blocks = []
        for i, block in enumerate(merged_blocks):
            # 确保每块至少有一个高分转折
            if not any(chapter_map[ch]['turning_score'] >= 3 for ch in block['chapters']):
                # 向前合并
                if i > 0:
                    prev_block = final_blocks[-1]
                    prev_block['chapters'].extend(block['chapters'])
                    prev_block['chapters'].sort()
                    # 更新转折点
                    prev_turning_points = set(prev_block.get('turning_points', []))
                    prev_turning_points.update(block.get('turning_points', []))
                    prev_block['turning_points'] = sorted(prev_turning_points)
                else:
                    # 第一块无法向前合并，标记异常
                    block['alert'] = "缺乏高分转折章节"
                    final_blocks.append(block)
            else:
                final_blocks.append(block)

        return final_blocks

    def _finalize_block(self, chapters, chapter_map):
        """完成块的构建"""
        # 识别主要冲突
        conflicts = defaultdict(int)
        for ch in chapters:
            summary = chapter_map[ch]['summary']
            for event in summary:
                if 'vs' in event or '对抗' in event or '冲突' in event:
                    conflicts[event.split('vs')[0].strip()] += 1

        main_conflict = max(conflicts, key=conflicts.get, default="未知冲突")

        # 识别转折点
        turning_points = [
            ch for ch in chapters
            if chapter_map[ch]['turning_score'] >= 3
        ]

        return {
            "chapters": sorted(chapters),
            "main_conflict": main_conflict,
            "turning_points": turning_points
        }

    def _generate_alerts(self, blocks):
        """生成异常提示"""
        alerts = []
        for i, block in enumerate(blocks, 1):
            if 'alert' in block:
                alerts.append(f"块{i}: {block['alert']}")
            elif not block.get('turning_points'):
                alerts.append(f"块{i}: 缺乏高分转折点")
        return "; ".join(alerts) if alerts else None