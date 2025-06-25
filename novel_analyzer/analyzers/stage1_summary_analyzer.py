# analyzers/stage1_summary_analyzer.py
import json
import os
import logging
import re
import time
from .base_analyzer import BaseAnalyzer
from config_manager import ConfigManager
from file_processor import FileProcessor


class Stage1SummaryAnalyzer(BaseAnalyzer):
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.terminology = config_manager.load_terminology()
        self.logger = logging.getLogger(__name__)
        self.default_prompt = """
        # 角色：小说分析师
        # 术语绑定：{term_binding}
        # 输入章节：{chapter_title}
        # 章节内容（截取前8000字符）：
        {chapter_content}...

        # 输出要求（严格JSON格式）：
        {{
          "chapter": 章节号（整数）,
          "summary": ["≤20字事件描述", "..."],
          "entities": {{
            "new_roles": ["姓名@身份"],
            "new_settings": ["名称@关键属性"],
            "foreshadowings": ["伏笔简述@类型"]
          }},
          "turning_score": 0-5
        }}

        # 硬性要求：
        1. 实体名与术语表一致（新实体首字母大写）
        2. 转折分必须匹配事件描述
        3. 摘要总字数≤200字
        4. 删除对话和环境描写"""

    def build_prompt(self, chapter_title, chapter_content):
        term_binding = json.dumps(self.terminology, ensure_ascii=False)
        custom_prompt = self.config.get('stage1', 'prompt', self.default_prompt)

        prompt = custom_prompt.replace('{term_binding}', term_binding) \
            .replace('{chapter_title}', chapter_title) \
            .replace('{chapter_content}', chapter_content[:8000])
        return prompt

    def run(self):
        output_dir = self.get_output_dir()
        chapter_dir = os.path.join(output_dir, 'chapters')
        summary_dir = os.path.join(output_dir, 'stage1_summaries')

        if not os.path.exists(chapter_dir):
            self.logger.error("章节目录不存在，请先进行章节分割")
            return False

        chapter_range = self.get_chapter_range(
            self.config.get('stage1', 'chapter_range', 'all')
        )
        chapter_files = FileProcessor.get_chapter_files(output_dir)
        if not chapter_files:
            self.logger.error("未找到章节文件")
            return False

        os.makedirs(summary_dir, exist_ok=True)
        success_count = 0
        total_chapters = len(chapter_files)
        to_process = []
        processed_count = 0

        for chapter_file in chapter_files:
            filename = os.path.basename(chapter_file)
            match = re.match(r'ch_(\d+)\.txt', filename)
            if not match:
                self.logger.error(f"无效的章节文件名: {filename}")
                continue

            chapter_num = int(match.group(1))
            if chapter_range and chapter_num not in chapter_range:
                self.logger.info(f"跳过章节 {chapter_num} (不在指定范围内)")
                continue

            to_process.append((chapter_file, chapter_num))

        total_to_process = len(to_process)
        if total_to_process == 0:
            self.logger.warning("没有需要处理的章节")
            return False

        for idx, (chapter_file, chapter_num) in enumerate(to_process):
            if not self.check_pause() or self.check_stop():
                self.logger.info("任务被用户中断")
                return False

            processed_count = idx + 1
            progress_message = f"处理章节 {chapter_num} ({processed_count}/{total_to_process})"
            self.update_progress(processed_count, total_to_process, progress_message)

            if self.process_chapter(chapter_file, chapter_num):
                success_count += 1
                self.logger.info(f"章节 {chapter_num} 处理成功")

        FileProcessor.export_summary_excel(output_dir)
        self.logger.info(f"章节摘要生成完成: {success_count}/{total_to_process}")
        return success_count > 0

    def process_chapter(self, chapter_path, chapter_num):
        output_path = os.path.join(
            self.get_output_dir(),
            'stage1_summaries',
            f'summary_{chapter_num:03d}.json'
        )

        if os.path.exists(output_path):
            self.logger.info(f"跳过已处理章节: ch_{chapter_num:03d}")
            return True

        try:
            with open(chapter_path, 'r', encoding='utf-8') as f:
                content = f.read().split('\n', 1)
                chapter_title = content[0]
                chapter_content = content[1] if len(content) > 1 else ""

            prompt = self.build_prompt(chapter_title, chapter_content)
            response = self.api_handler.generate(prompt)
            result = self._parse_response(response)
            result['chapter'] = chapter_num
            self._update_terminology(result)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            self.logger.error(f"章节 {chapter_num} 处理失败: {str(e)}")
            return False

    def _parse_response(self, response):
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            return json.loads(response[start:end])
        except json.JSONDecodeError:
            self.logger.error(f"API响应解析失败: {response}")
            raise ValueError("API返回了无效的JSON格式")

    def _update_terminology(self, result):
        new_terms = {}
        for role in result['entities'].get('new_roles', []):
            name = role.split('@')[0]
            if name not in self.terminology:
                new_terms[name] = name
        for setting in result['entities'].get('new_settings', []):
            name = setting.split('@')[0]
            if name not in self.terminology:
                new_terms[name] = name
        if new_terms:
            self.terminology = self.config.update_terminology(new_terms)