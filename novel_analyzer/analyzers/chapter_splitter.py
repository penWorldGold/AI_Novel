# analyzers/chapter_splitter.py
import os
import logging
from .base_analyzer import BaseAnalyzer


class ChapterSplitter(BaseAnalyzer):
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.logger = logging.getLogger(__name__)

    def run(self):
        novel_path = self.config.get('global', 'novel_path')
        output_dir = self.get_output_dir()

        if not novel_path or not os.path.exists(novel_path):
            self.logger.error("小说文件路径无效或不存在")
            return False

        self.file_processor.create_output_structure(output_dir)
        chapter_regex = self.config.get('chapter_split', 'regex', r'第[零一二三四五六七八九十百千0-9]+章')
        encoding_setting = self.config.get('chapter_split', 'encoding', 'auto')

        self.logger.info("开始章节分割...")
        chapter_files = self.file_processor.split_chapters(
            novel_path, output_dir, chapter_regex, encoding=encoding_setting
        )

        if chapter_files:
            self.logger.info(f"成功分割 {len(chapter_files)} 个章节")
            return True
        return False