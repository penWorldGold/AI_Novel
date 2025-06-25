import json
import os
import logging
from .base_analyzer import BaseAnalyzer

import json
import os
import logging
from .base_analyzer import BaseAnalyzer


class Stage3PlotAnalyzer(BaseAnalyzer):
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.logger = logging.getLogger(__name__)
        self.default_prompt = """# 角色：情节分析师
# 输入：情节块信息
# 输出要求（严格JSON格式）：
{{
  "block_id": 1,
  "core_goal": "≤15字目标",
  "three_acts": {{
    "setup": "起始状态（1句）",
    "confrontation": [
      "章A: 事件A（转折分+原因）", 
      "章B: 事件B"
    ],
    "resolution": "结局状态+遗留问题"
  }},
  "character_arcs": ["主角: ▲成长方向"],
  "unsolved_foreshadowings": ["伏笔@关联章"]
}}

# 特殊要求：
1. 强制关联伏笔章节号
2. 角色成长方向使用▲符号标记
3. 转折点必须引用章节号"""

    def run(self):
        """生成情节块摘要"""
        # 检查暂停/停止请求
        if not self.check_pause() or self.check_stop():
            self.logger.info("任务被用户中断")
            return False

        output_dir = self.get_output_dir()
        block_path = os.path.join(output_dir, 'stage2_blocks', 'blocks.json')
        plot_dir = os.path.join(output_dir, 'stage3_plots')

        # 检查输入是否存在
        if not os.path.exists(block_path):
            self.logger.error("分块结果不存在，请先完成阶段2分析")
            return False

        with open(block_path, 'r', encoding='utf-8') as f:
            block_data = json.load(f)

        # 处理每个情节块
        success_count = 0
        total_blocks = len(block_data['blocks'])

        for idx, block in enumerate(block_data['blocks']):
            # 检查暂停/停止请求
            if not self.check_pause() or self.check_stop():
                return False

            block_id = idx + 1
            plot_path = os.path.join(plot_dir, f'block_{block_id}.json')

            if os.path.exists(plot_path):
                self.logger.info(f"跳过已处理块: block_{block_id}")
                continue

            # 更新进度
            if self.progress_callback:
                self.progress_callback(idx + 1, total_blocks, f"处理块 {block_id}")

            plot_summary = self._generate_plot_summary(block_id, block, output_dir)
            if plot_summary:
                with open(plot_path, 'w', encoding='utf-8') as f:
                    json.dump(plot_summary, f, ensure_ascii=False, indent=2)
                success_count += 1

        self.logger.info(f"情节块摘要生成完成: {success_count}/{total_blocks}")
        return success_count > 0

    def _generate_plot_summary(self, block_id, block, output_dir):
        """生成单个情节块摘要"""
        # 加载相关章节摘要
        summaries = []
        summary_dir = os.path.join(output_dir, 'stage1_summaries')
        for ch in block['chapters']:
            summary_path = os.path.join(summary_dir, f'summary_{ch:03d}.json')
            if os.path.exists(summary_path):
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summaries.append(json.load(f))

        if not summaries:
            return None

        # 构建提示词
        prompt = self.build_prompt(block_id, block, summaries)
        try:
            response = self.api_handler.generate(prompt)
        except Exception as e:
            self.logger.error(f"块{block_id}摘要生成失败: {str(e)}")
            return None

        # 解析响应
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            result = json.loads(response[start:end])
            result['block_id'] = block_id
            return result
        except Exception as e:
            self.logger.error(f"块{block_id}摘要解析失败: {str(e)}")
            return None

    def build_prompt(self, block_id, block, summaries):
        """构建情节块摘要提示词"""
        # 从配置获取自定义提示词
        custom_prompt = self.config.get('stage3', 'prompt', self.default_prompt)

        chapters_str = ', '.join(str(s['chapter']) for s in summaries)
        turning_points = block.get('turning_points', [])

        # 替换占位符
        prompt = custom_prompt.replace('{block_id}', str(block_id)) \
                     .replace('{chapters}', str(len(block['chapters']))) \
                     .replace('{main_conflict}', block.get('main_conflict', '')) \
                     .replace('{turning_points}', ', '.join(str(tp) for tp in turning_points)) \
                 + "\n\n# 章节摘要数据:\n" + json.dumps(summaries, ensure_ascii=False, indent=2)
        return prompt