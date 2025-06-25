import json
import os
import logging
from .base_analyzer import BaseAnalyzer


class Stage4OutlineAnalyzer(BaseAnalyzer):
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.logger = logging.getLogger(__name__)
        self.default_prompt = """# 角色：大纲分析师
# 输入：情节块摘要
# 输出要求（Markdown格式）：
## 一、主线阶段表
| 阶段   | 章节   | 核心目标 | 关键转折事件          |
|--------|--------|----------|-----------------------|
| 崛起篇 | 1-200  | 生存     | 获得异能◎第34章(分4) |

## 二、角色成长轴
主角名：  
✓ 初始：[状态] ◎第1章  
✓ 蜕变：[事件] ◎X章  
✓ 终局：[状态] ◎Y章  

## 三、伏应关系表
| 伏笔内容 | 出现章 | 回收章 | 回收方式   |
|----------|--------|--------|------------|
| 玉佩发光 | 5      | 1200   | 激活神器   |

## 四、终局分析
世界观结局：1句话  
主题呼应：首尾伏笔对比

# 生成规则：
- 相邻块核心冲突相似度>70%则合并阶段
- 重大转折事件仅取各块最高分转折
- 高潮事件标记：⭐(基础事件) ⭐⭐(转折点) ⭐⭐⭐(大高潮)"""

    def run(self):
        """生成全书大纲"""
        # 检查暂停/停止请求
        if not self.check_pause() or self.check_stop():
            self.logger.info("任务被用户中断")
            return False, None

        output_dir = self.get_output_dir()
        plot_dir = os.path.join(output_dir, 'stage3_plots')
        outline_path = os.path.join(output_dir, 'stage4_outline', 'full_outline.txt')

        # 检查输入是否存在
        if not os.path.exists(plot_dir):
            self.logger.error("情节块摘要不存在，请先完成阶段3分析")
            return False, None

        # 加载所有情节块摘要
        plot_summaries = []
        for fname in sorted(os.listdir(plot_dir)):
            # 检查暂停/停止请求
            if not self.check_pause() or self.check_stop():
                return False, None

            if fname.endswith('.json'):
                with open(os.path.join(plot_dir, fname), 'r', encoding='utf-8') as f:
                    plot_summaries.append(json.load(f))

        if not plot_summaries:
            self.logger.error("未找到情节块摘要")
            return False, None

        # 构建提示词
        prompt = self.build_prompt(plot_summaries)

        try:
            if not self.check_pause() or self.check_stop():
                return False, None
            response = self.api_handler.generate(prompt)
        except Exception as e:
            self.logger.error(f"大纲生成失败: {str(e)}")
            return False, None

        # 保存结果
        os.makedirs(os.path.dirname(outline_path), exist_ok=True)
        with open(outline_path, 'w', encoding='utf-8') as f:
            f.write(response)

        return True, response

    def build_prompt(self, plot_summaries):
        """构建全书大纲提示词"""
        climax_threshold = self.config.get('stage4', 'climax_threshold', '4')

        # 从配置获取自定义提示词
        custom_prompt = self.config.get('stage4', 'prompt', self.default_prompt)

        # 替换占位符
        prompt = custom_prompt.replace('{climax_threshold}', climax_threshold) \
                 + "\n\n# 情节块摘要数据:\n" + json.dumps(plot_summaries, ensure_ascii=False, indent=2)
        return prompt